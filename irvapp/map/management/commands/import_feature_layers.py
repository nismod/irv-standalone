"""Import feature-layer identities without overwriting curated metadata."""

import csv

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from map.models import FeatureLayer, LayerIdentity


class Command(BaseCommand):
    help = "Create feature layers from an ETL tile-layer CSV."

    def add_arguments(self, parser):
        parser.add_argument("csv_path")

    def handle(self, *args, **options):
        path = options["csv_path"]
        fields = ("layer", "sector", "subsector", "asset_type")
        rows = {}
        try:
            with open(path, newline="", encoding="utf-8-sig") as source:
                reader = csv.DictReader(source)
                if not reader.fieldnames or not set(fields).issubset(reader.fieldnames):
                    raise CommandError(f"{path}: required columns: {', '.join(fields)}")
                for line, row in enumerate(reader, 2):
                    values = tuple((row.get(field) or "").strip() for field in fields)
                    if not all(values):
                        raise CommandError(f"{path}:{line}: missing required value")
                    layer_id, *metadata = values
                    metadata = tuple(metadata)
                    if layer_id in rows and rows[layer_id] != metadata:
                        raise CommandError(f"{path}:{line}: conflicting definitions for {layer_id!r}")
                    rows[layer_id] = metadata
        except (OSError, csv.Error) as exc:
            raise CommandError(f"Cannot read {path}: {exc}") from exc

        created = 0
        conflicts = []
        with transaction.atomic():
            for layer_id, metadata in rows.items():
                identity, _ = LayerIdentity.objects.get_or_create(
                    pk=layer_id, defaults={"kind": "feature"},
                )
                if identity.kind != "feature":
                    raise CommandError(f"Layer ID {layer_id!r} belongs to {identity.kind}")
                layer, is_new = FeatureLayer.objects.get_or_create(
                    identity_id=layer_id,
                    defaults=dict(zip(fields[1:], metadata)),
                )
                created += is_new
                if not is_new and tuple(getattr(layer, f) for f in fields[1:]) != metadata:
                    conflicts.append(layer_id)
            unassigned = list(LayerIdentity.objects.filter(
                pk__in=rows, dataset__isnull=True,
            ).order_by("pk").values_list("pk", flat=True))

        self.stdout.write(f"Created {created} feature layer(s); reused {len(rows) - created}.")
        if conflicts:
            self.stdout.write(self.style.WARNING(
                "Existing metadata differs and was preserved: " + ", ".join(sorted(conflicts))
            ))
        if unassigned:
            self.stdout.write(self.style.WARNING(
                "Unassigned layers (unavailable to users): " + ", ".join(unassigned)
            ))
