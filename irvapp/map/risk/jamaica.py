"""Default risk endpoints for the existing risk schema."""

from map.views import (
    AdaptationCostBenefitViewset,
    AttributeLookupView,
    DamagesExpectedViewset,
    DamagesRpViewset,
    FeatureViewset,
    ProtectedFeaturesView,
    SortedFeaturesView,
)
from map.views.model_scenarios import ModelScenariosView


class JamaicaRiskProvider:
    feature_viewset = FeatureViewset
    adaptation_viewset = AdaptationCostBenefitViewset
    expected_damages_viewset = DamagesExpectedViewset
    return_period_damages_viewset = DamagesRpViewset
    scenarios_view = ModelScenariosView
    sorted_features_view = SortedFeaturesView
    protected_features_view = ProtectedFeaturesView
    attribute_lookup_view = AttributeLookupView
