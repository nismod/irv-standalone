import importlib.util
from pathlib import Path

from django.test import SimpleTestCase, override_settings
from django.urls import resolve

from map.risk.jamaica import JamaicaRiskProvider


class AlternateRiskProvider(JamaicaRiskProvider):
    # Distinct classes let the test identify which provider registered a route.
    feature_viewset = type("AlternateFeatureViewset", (JamaicaRiskProvider.feature_viewset,), {})
    adaptation_viewset = type("AlternateAdaptationViewset", (JamaicaRiskProvider.adaptation_viewset,), {})
    expected_damages_viewset = type("AlternateExpectedViewset", (JamaicaRiskProvider.expected_damages_viewset,), {})
    return_period_damages_viewset = type("AlternateRpViewset", (JamaicaRiskProvider.return_period_damages_viewset,), {})
    scenarios_view = type("AlternateScenariosView", (JamaicaRiskProvider.scenarios_view,), {})
    sorted_features_view = type("AlternateSortedView", (JamaicaRiskProvider.sorted_features_view,), {})
    protected_features_view = type("AlternateProtectedView", (JamaicaRiskProvider.protected_features_view,), {})
    attribute_lookup_view = type("AlternateAttributesView", (JamaicaRiskProvider.attribute_lookup_view,), {})


class RiskProviderRoutingTests(SimpleTestCase):
    @override_settings(RISK_PROVIDER="map.test_risk_provider.AlternateRiskProvider")
    def test_alternate_provider_registers_all_risk_routes(self):
        # Load a separate URL configuration so the project's cached URLconf
        # remains untouched when this test changes the startup setting.
        path = Path(__file__).with_name("urls.py")
        spec = importlib.util.spec_from_file_location("alternate_risk_urls", path)
        urlconf = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(urlconf)
        routes = {
            "/features": "feature_viewset",
            "/features/1": "feature_viewset",
            "/adaptation-cost-benefits": "adaptation_viewset",
            "/damages-expected": "expected_damages_viewset",
            "/damages-rp": "return_period_damages_viewset",
            "/model-scenarios/damages_expected": "scenarios_view",
            "/features/sorted-by/damages_expected": "sorted_features_view",
            "/features/1/protected-by": "protected_features_view",
            "/attributes/damages_expected": "attribute_lookup_view",
        }
        for path, attribute in routes.items():
            with self.subTest(path=path):
                self.assertIs(resolve(path, urlconf=urlconf).func.cls, getattr(AlternateRiskProvider, attribute))
