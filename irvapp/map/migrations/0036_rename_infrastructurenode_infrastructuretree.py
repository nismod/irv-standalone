import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('map', '0035_delete_damagesnpv'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='InfrastructureNode',
            new_name='InfrastructureTree',
        ),
        migrations.AlterModelTable(
            name='infrastructuretree',
            table='infrastructure_trees',
        ),
        migrations.AlterField(
            model_name='infrastructuretree',
            name='feature_layer',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='infrastructure_tree',
                to='map.featurelayer',
            ),
        ),
    ]
