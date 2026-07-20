"""Django command to ingest raster files into a Terracotta database."""

import os
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from raster.ingestion import (
    DEFAULT_PATH_TEMPLATE,
    SUPPORTED_DATABASE_PROVIDERS,
    ingest_rasters,
)


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
            "--path-template",
            default=os.environ.get(
                "RASTER_PATH_TEMPLATE", DEFAULT_PATH_TEMPLATE
            ),
            help=(
                "Python-style raster path template "
                "(default: RASTER_PATH_TEMPLATE)"
            ),
        )
        parser.add_argument(
            "--database",
            default=os.environ.get(
                "TC_DRIVER_PATH",
                str(Path(BASE_PATH) / "terracotta.sqlite"),
            ),
            help=(
                "SQLite path or SQL URL "
                "(default: TC_DRIVER_PATH or BASE_PATH/terracotta.sqlite)"
            ),
        )
        parser.add_argument(
            "--database-provider",
            choices=SUPPORTED_DATABASE_PROVIDERS,
            default=os.environ.get("TC_DRIVER_PROVIDER"),
            help=(
                "Terracotta database provider "
                "(default: TC_DRIVER_PROVIDER or auto-detect)"
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
        path_template = Path(options["path_template"]).expanduser()
        if not path_template.is_absolute():
            path_template = base_path / path_template

        database = options["database"] or str(base_path / "terracotta.sqlite")
        try:
            count = ingest_rasters(
                path_template=str(path_template),
                database=database,
                database_provider=options["database_provider"],
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
