from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction


class Command(BaseCommand):
    help = (
        "Migrate Django app metadata from the historical app label to the "
        "current one for already-initialized databases."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--from-label",
            default="api",
            help="Existing app label stored in the database.",
        )
        parser.add_argument(
            "--to-label",
            default="map",
            help="Target app label used by the current codebase.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report the changes without writing them.",
        )

    def handle(self, *args, **options):
        from_label = options["from_label"]
        to_label = options["to_label"]
        dry_run = options["dry_run"]

        if from_label == to_label:
            raise CommandError("--from-label and --to-label must differ.")

        app_config = apps.get_app_config(to_label)
        model_names = sorted(
            model._meta.model_name for model in app_config.get_models()
        )

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT name FROM django_migrations WHERE app = %s ORDER BY name",
                [from_label],
            )
            source_migrations = [row[0] for row in cursor.fetchall()]
            cursor.execute(
                "SELECT name FROM django_migrations WHERE app = %s ORDER BY name",
                [to_label],
            )
            target_migrations = [row[0] for row in cursor.fetchall()]

        duplicate_migrations = sorted(
            set(source_migrations).intersection(target_migrations)
        )
        if duplicate_migrations:
            joined = ", ".join(duplicate_migrations)
            raise CommandError(
                "Refusing to continue because both app labels already exist "
                f"in django_migrations for: {joined}"
            )

        source_content_types = list(
            ContentType.objects.filter(
                app_label=from_label,
                model__in=model_names,
            ).order_by("model")
        )
        target_content_types = list(
            ContentType.objects.filter(
                app_label=to_label,
                model__in=model_names,
            ).order_by("model")
        )

        duplicate_content_types = sorted(
            {content_type.model for content_type in target_content_types}
        )
        if duplicate_content_types:
            joined = ", ".join(duplicate_content_types)
            raise CommandError(
                "Refusing to continue because target content types already "
                f"exist for: {joined}. Remove or merge them first."
            )

        self.stdout.write(
            f"Planned migration rows: {len(source_migrations)} "
            f"from '{from_label}' to '{to_label}'."
        )
        self.stdout.write(
            f"Planned content types: {len(source_content_types)} "
            f"from '{from_label}' to '{to_label}'."
        )

        if dry_run:
            if source_migrations:
                self.stdout.write(
                    "Migrations: " + ", ".join(source_migrations)
                )
            if source_content_types:
                self.stdout.write(
                    "Content types: "
                    + ", ".join(
                        content_type.model
                        for content_type in source_content_types
                    )
                )
            return

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE django_migrations SET app = %s WHERE app = %s",
                    [to_label, from_label],
                )

            ContentType.objects.filter(
                app_label=from_label,
                model__in=model_names,
            ).update(app_label=to_label)

        self.stdout.write(
            self.style.SUCCESS(
                "Updated django_migrations and django_content_type. "
                "Run `python irvapp/manage.py migrate` next."
            )
        )
