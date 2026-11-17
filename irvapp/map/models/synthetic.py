from django.db import models


class SyntheticDataRun(models.Model):
    """Ownership record for opt-in development fixtures, never model parameters."""

    name = models.CharField(primary_key=True, max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    config = models.JSONField()
    result_ids = models.JSONField(default=dict)
    parameter_set_ids = models.JSONField(default=list)

    class Meta:
        db_table = "synthetic_data_runs"
