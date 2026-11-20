from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F

from map.models import Dataset, FeatureLayer


class Command(BaseCommand):
    help = "Link unassigned feature layers to datasets with matching IDs."

    @transaction.atomic
    def handle(self, *args, **options):
        matching_ids = Dataset.objects.values_list("pk", flat=True)
        updated = FeatureLayer.objects.filter(dataset__isnull=True, pk__in=matching_ids).update(dataset_id=F("layer_name"))
        missing = list(FeatureLayer.objects.filter(dataset__isnull=True).order_by("pk").values_list("pk", flat=True))
        self.stdout.write(f"Linked {updated} feature layer(s).")
        if missing:
            self.stdout.write(self.style.WARNING(
                "Unlinked feature layers; assign a dataset in Django admin: " + ", ".join(missing)
            ))
