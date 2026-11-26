"""Transactional, batched upserts shared by the Jamaica result loaders."""
from django.db import transaction

from map.model_parameters import canonical_parameter_key
from map.models import Feature, ModelParameterSet


class ResultWriter:
    def __init__(self, model, model_type, key_fields, value_fields, batch_size=1000):
        self.model = model
        self.model_type = model_type
        self.key_fields = key_fields
        self.value_fields = value_fields
        self.batch_size = batch_size
        self.parameters = {}
        self.keys = set()
        self.pending = []
        self.count = 0

    def add(self, parameters, **values):
        canonical = canonical_parameter_key(parameters)
        if canonical not in self.parameters:
            self.parameters[canonical] = ModelParameterSet.for_values(self.model_type, parameters).pk
        values['parameter_set_id'] = self.parameters[canonical]
        key = tuple(values[field + '_id'] if field in ('parameter_set', 'feature') else values[field]
                    for field in self.key_fields)
        if key in self.keys:
            raise ValueError(f"Duplicate {self.model_type} result key: {key}")
        self.keys.add(key)
        self.pending.append(self.model(**values))
        self.count += 1
        if len(self.pending) >= self.batch_size:
            self.flush()

    def flush(self):
        if not self.pending:
            return
        ids = {row.feature_id for row in self.pending}
        ids.update(row.protector_feature_id for row in self.pending
                   if hasattr(row, 'protector_feature_id') and row.protector_feature_id is not None)
        missing = ids - set(Feature.objects.filter(pk__in=ids).values_list('pk', flat=True))
        if missing:
            raise ValueError(f"Result references missing feature IDs: {sorted(missing)[:20]}")
        if self.model_type == "adaptation":
            existing = self.model.objects.filter(
                feature_id__in={row.feature_id for row in self.pending},
                parameter_set_id__in={row.parameter_set_id for row in self.pending},
            ).values_list("parameter_set_id", "feature_id", "hazard", "adaptation_name",
                          "adaptation_protection_level", "protector_feature_id")
            protectors = {row[:-1]: row[-1] for row in existing}
            for row in self.pending:
                key = (row.parameter_set_id, row.feature_id, row.hazard,
                       row.adaptation_name, row.adaptation_protection_level)
                if key in protectors and protectors[key] != row.protector_feature_id:
                    raise ValueError(f"Conflicting protector for adaptation result {key}")
        self.model.objects.bulk_create(
            self.pending, update_conflicts=True,
            unique_fields=self.key_fields, update_fields=self.value_fields,
        )
        self.pending.clear()

    def finish(self):
        self.flush()
        print(f"Upserted {self.count} {self.model_type} result(s)")


def import_results(model, model_type, key_fields, value_fields, rows):
    with transaction.atomic():
        writer = ResultWriter(model, model_type, key_fields, value_fields)
        for parameters, values in rows:
            writer.add(parameters, **values)
        writer.finish()
