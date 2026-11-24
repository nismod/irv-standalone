from django.conf import settings
from django.utils.module_loading import import_string


def get_risk_provider():
    """Load the risk endpoint provider selected when Django starts."""
    path = getattr(settings, "RISK_PROVIDER", "map.risk.jamaica.JamaicaRiskProvider")
    return import_string(path)()
