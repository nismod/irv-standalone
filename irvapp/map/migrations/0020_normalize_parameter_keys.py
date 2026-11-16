import json

from django.db import IntegrityError, migrations

from map.model_parameters import canonical_parameter_key


def normalize_parameter_keys(apps, schema_editor):
    ParameterSet = apps.get_model("map", "ModelParameterSet")
    alias = schema_editor.connection.alias
    groups = {}
    for parameter_set in ParameterSet.objects.using(alias).order_by("id"):
        key = canonical_parameter_key(json.loads(parameter_set.canonical_key))
        groups.setdefault((parameter_set.model_type, key), []).append(parameter_set)

    for (model_type, key), parameter_sets in groups.items():
        # Prefer a set whose key is already canonical, avoiding a transient
        # violation of the unique (model_type, canonical_key) constraint.
        retained = next(
            (item for item in parameter_sets if item.canonical_key == key),
            parameter_sets[0],
        )
        for duplicate in parameter_sets:
            if duplicate.pk == retained.pk:
                continue
            for model_name in (
                "AdaptationCostBenefit", "DamagesExpected", "DamagesNpv", "DamagesRp"
            ):
                Result = apps.get_model("map", model_name)
                try:
                    Result.objects.using(alias).filter(
                        parameter_set_id=duplicate.pk
                    ).update(parameter_set_id=retained.pk)
                except IntegrityError as exc:
                    # The migration is atomic: leave all original data intact
                    # if equivalent scenarios have overlapping result keys.
                    raise RuntimeError(
                        f"Cannot merge {model_type} parameter sets "
                        f"{duplicate.pk} and {retained.pk}: overlapping "
                        f"{model_name} results must be resolved first."
                    ) from exc
            ParameterSet.objects.using(alias).filter(pk=duplicate.pk).delete()
        if retained.canonical_key != key:
            ParameterSet.objects.using(alias).filter(pk=retained.pk).update(
                canonical_key=key
            )


class Migration(migrations.Migration):
    dependencies = [("map", "0019_add_flexible_result_primary_keys")]

    operations = [
        migrations.RunPython(normalize_parameter_keys, migrations.RunPython.noop),
    ]
