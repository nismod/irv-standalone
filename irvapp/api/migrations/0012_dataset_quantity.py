from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0011_dataset_tile_source"),
    ]

    operations = [
        migrations.AddField(
            model_name="dataset",
            name="quantity",
            field=models.CharField(default=""),
            preserve_default=False,
        ),
    ]
