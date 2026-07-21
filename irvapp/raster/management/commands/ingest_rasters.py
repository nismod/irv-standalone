"""Django command to ingest raster files into a Terracotta database."""

import os
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from raster.ingestion import ingest_rasters
from raster.models import RasterTileSource


class Command(BaseCommand):
    help = "Ingest raster files into a Terracotta metadata database."

    def add_arguments(self, parser):
        BASE_PATH = os.environ.get("RASTER_BASE_PATH", "/data/raster")
        parser.add_argument(
            "base_path",
            nargs="?",
            default=BASE_PATH,
            help=(
                "base directory for a relative path template "
                "(default: RASTER_BASE_PATH or /data/raster)"
            ),
        )
        parser.add_argument(
            "--rgb-key",
            help="move this key to the final position for RGB compositing",
        )
        parser.add_argument(
            "--skip-existing",
            action="store_true",
            help="do not replace existing keys",
        )
        parser.add_argument(
            "--skip-metadata",
            action="store_true",
            help="defer raster metadata computation until the first request",
        )
        parser.add_argument("--quiet", action="store_true", help="hide output")

    def handle(self, *args, **options):
        base_path = Path(options["base_path"]).expanduser().resolve()
        sources = (
            RasterTileSource.objects.order_by("path_template", "database")
            .values_list("path_template", "database")
            .distinct()
        )

        count = 0
        try:
            for path_template, database in sources:
                path_template = Path(path_template).expanduser()
                if not path_template.is_absolute():
                    path_template = base_path / path_template

                database_str = str(database)
                if "://" not in database_str:
                    database_path = Path(database_str).expanduser()
                    if not database_path.is_absolute():
                        database_path = base_path / database_path
                    database_str = str(database_path)

                count += ingest_rasters(
                    path_template=str(path_template),
                    database=database_str,
                    database_provider=None,
                    rgb_key=options["rgb_key"],
                    skip_existing=options["skip_existing"],
                    skip_metadata=options["skip_metadata"],
                    quiet=options["quiet"],
                )
        except Exception as exc:
            raise CommandError(str(exc)) from exc

        if not options["quiet"]:
            message = (
                f"Ingested {count} raster file"
                f"{'s' if count != 1 else ''}."
            )
            self.stdout.write(self.style.SUCCESS(message))
