"""Transactional, batched upserts shared by the Jamaica result loaders."""
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory

from django.db import transaction

from map.model_parameters import canonical_parameter_key
from map.models import Feature, ModelParameterSet


class ResultWriter:
    def __init__(self, model, model_type, key_fields, value_fields, key_database, batch_size=1000):
        self.model = model
        self.model_type = model_type
        self.key_fields = key_fields
        self.value_fields = value_fields
        self.batch_size = batch_size
        self.parameters = {}
        self.key_database = key_database
        columns = [f"k{i}" for i in range(len(key_fields))]
        self.key_insert = f"INSERT INTO result_keys VALUES ({', '.join('?' for _ in columns)})"
        self.key_database.execute(
            f"CREATE TABLE result_keys ({', '.join(f'{name} NOT NULL' for name in columns)}, "
            f"PRIMARY KEY ({', '.join(columns)})) WITHOUT ROWID"
        )
        self.pending = []
        self.count = 0

    def add(self, parameters, **values):
        canonical = canonical_parameter_key(parameters)
        if canonical not in self.parameters:
            self.parameters[canonical] = ModelParameterSet.for_values(self.model_type, parameters).pk
        values['parameter_set_id'] = self.parameters[canonical]
        self.pending.append(self.model(**values))
        self.count += 1
        if len(self.pending) >= self.batch_size:
            self.flush()

    def flush(self):
        if not self.pending:
            return
        keys = [
            tuple(getattr(row, field + '_id' if field in ('parameter_set', 'feature') else field)
                  for field in self.key_fields)
            for row in self.pending
        ]
        try:
            self.key_database.executemany(self.key_insert, keys)
            self.key_database.commit()
        except sqlite3.IntegrityError as exc:
            if exc.sqlite_errorname not in ("SQLITE_CONSTRAINT_PRIMARYKEY", "SQLITE_CONSTRAINT_UNIQUE"):
                raise
            raise ValueError(f"Duplicate {self.model_type} result key in input") from exc
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
    # A disk-backed unique index bounds Python memory independently of input size.
    # The temporary database is private to this import and removed on failure.
    with TemporaryDirectory(prefix="irv-result-keys-") as directory:
        key_database = sqlite3.connect(str(Path(directory) / "keys.sqlite3"))
        try:
            with transaction.atomic():
                writer = ResultWriter(model, model_type, key_fields, value_fields, key_database)
                for parameters, values in rows:
                    writer.add(parameters, **values)
                writer.finish()
        finally:
            key_database.close()
