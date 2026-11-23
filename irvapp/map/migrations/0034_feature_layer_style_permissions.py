from django.conf import settings
from django.db import migrations


def move_permissions(apps, schema_editor, old_model, new_model):
    alias = schema_editor.connection.alias
    ContentType = apps.get_model("contenttypes", "ContentType")
    Permission = apps.get_model("auth", "Permission")
    Group = apps.get_model("auth", "Group")
    User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))
    content_types = ContentType.objects.using(alias).filter(
        app_label="map", model__in=[old_model, new_model],
    )
    if not content_types.exists():
        return
    target_type, _ = ContentType.objects.using(alias).get_or_create(app_label="map", model=new_model)

    for action in ("add", "change", "delete", "view"):
        old_code = f"{action}_{old_model}"
        new_code = f"{action}_{new_model}"
        sources = list(Permission.objects.using(alias).filter(content_type__in=content_types, codename=old_code))
        target = Permission.objects.using(alias).filter(content_type=target_type, codename=new_code).first()
        for source in sources:
            if target is None:
                source.content_type = target_type
                source.codename = new_code
                source.name = f"Can {action} {'feature' if new_model == 'featurelayerstyle' else 'network'} layer style"
                source.save(using=alias, update_fields=["content_type", "codename", "name"])
                target = source
                continue
            for model, field_name in ((Group, "permissions"), (User, "user_permissions")):
                field = model._meta.get_field(field_name)
                through = field.remote_field.through
                owner_id = f"{field.m2m_field_name()}_id"
                permission_id = f"{field.m2m_reverse_field_name()}_id"
                owner_ids = through.objects.using(alias).filter(**{permission_id: source.pk}).values_list(owner_id, flat=True)
                through.objects.using(alias).bulk_create(
                    [through(**{owner_id: pk, permission_id: target.pk}) for pk in owner_ids],
                    ignore_conflicts=True,
                )
            source.delete(using=alias)


def forward(apps, schema_editor):
    move_permissions(apps, schema_editor, "networklayerstyle", "featurelayerstyle")


def backward(apps, schema_editor):
    move_permissions(apps, schema_editor, "featurelayerstyle", "networklayerstyle")


class Migration(migrations.Migration):
    dependencies = [
        ("map", "0033_feature_layer_styles"),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [migrations.RunPython(forward, backward)]
