from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("map", "0008_mapconfig_config_type"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.AddField(
            model_name="dataset",
            name="access_groups",
            field=models.ManyToManyField(
                blank=True,
                related_name="datasets",
                to="auth.group",
            ),
        ),
    ]
