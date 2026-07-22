"""Django command to ingest pixel rasters into Zarr stacks."""

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from pixel.ingestion import DEFAULT_LAYERS_PATH, ingest_pixel_stacks


class Command(BaseCommand):
    help = "Ingest pixel rasters into Zarr stacks for the pixel app."

    def add_arguments(self, parser):
        parser.add_argument(
            "source_path",
            help="base directory containing the source raster files",
        )
        parser.add_argument(
            "target_path",
            help="directory where Zarr stacks and metadata CSVs will be written",
        )
        parser.add_argument(
            "--layers-path",
            default=str(DEFAULT_LAYERS_PATH),
            help=(
                "CSV describing raster layers "
                f"(default: {DEFAULT_LAYERS_PATH})"
            ),
        )
        parser.add_argument("--quiet", action="store_true", help="hide output")

    def handle(self, *args, **options):
        source_path = Path(options["source_path"]).expanduser().resolve()
        target_path = Path(options["target_path"]).expanduser().resolve()
        layers_path = Path(options["layers_path"]).expanduser().resolve()

        try:
            layers, grids = ingest_pixel_stacks(
                source_path,
                target_path,
                layers_path=layers_path,
                quiet=options["quiet"],
            )
        except Exception as exc:
            raise CommandError(str(exc)) from exc

        if not options["quiet"]:
            self.stdout.write(
                self.style.SUCCESS(
                    "Ingested "
                    f"{len(layers)} raster file"
                    f"{'s' if len(layers) != 1 else ''} "
                    f"into {len(grids)} stack"
                    f"{'s' if len(grids) != 1 else ''}."
                )
            )
