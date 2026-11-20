from django.db.models import OuterRef, Prefetch, Subquery
from django.db import connections
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from map.permissions import inaccessible_hazard_ids

from map.models import (
    AdaptationCostBenefit, DamagesExpected, Feature, FeatureLayer, ModelParameter, ModelParameterSet,
)


class ModelScenarioSerializer(serializers.Serializer):
    hazard = serializers.CharField()
    parameters = serializers.DictField(child=serializers.JSONField())
    protection_standard = serializers.IntegerField(required=False)
    adaptation_name = serializers.CharField(required=False)
    adaptation_protection_level = serializers.FloatField(required=False)


def scenario_combinations(model, dimensions, parameter_set_ids):
    """Seek the next distinct index prefix without walking duplicate results.

    The scenario indexes put these columns before feature_id. Each recursive
    step reads one combination then seeks beyond that entire prefix, making
    discovery proportional to the number of scenarios, not feature results.
    All SQL identifiers come from model fields, never request values.
    """
    if not parameter_set_ids:
        return []
    connection = connections[model.objects.db]
    quote = connection.ops.quote_name
    names = ("parameter_set_id", "hazard", *dimensions)
    columns = ", ".join(quote(model._meta.get_field(name).column) for name in names)
    previous = ", ".join(f"previous.{quote(name)}" for name in names)
    following = ", ".join(f"following.{quote(name)}" for name in names)
    table = quote(model._meta.db_table)
    sql = f"""
        WITH RECURSIVE scenario_keys AS (
            (SELECT {columns} FROM {table} ORDER BY {columns} LIMIT 1)
            UNION ALL
            SELECT {following} FROM scenario_keys AS previous
            CROSS JOIN LATERAL (
                SELECT {columns} FROM {table}
                WHERE ({columns}) > ({previous})
                ORDER BY {columns} LIMIT 1
            ) AS following
        )
        SELECT {columns} FROM scenario_keys WHERE parameter_set_id = ANY(%s)
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, [parameter_set_ids])
        return [dict(zip(names, row)) for row in cursor.fetchall()]


class ModelScenariosView(APIView):
    """Discover complete scenarios that have results in the requested scope."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter("layer", str, many=True),
            *[OpenApiParameter(name, str) for name in (
                "sector", "subsector", "asset_type", "hazard",
            )],
            OpenApiParameter("protector_id", int),
        ],
        responses=ModelScenarioSerializer(many=True),
    )
    def get(self, request, field_group):
        models = {
            "damages_expected": (DamagesExpected, ("protection_standard",)),
            "adaptation": (
                AdaptationCostBenefit,
                ("adaptation_name", "adaptation_protection_level"),
            ),
        }
        if field_group not in models:
            return Response({"field_group": ["Invalid field group."]}, status=400)
        model, dimensions = models[field_group]
        # Resolve the small parameter-set table first. A join against its
        # model_type statistics can make PostgreSQL severely underestimate the
        # result count after a backfill and choose millions of feature lookups.
        parameter_set_ids = list(ModelParameterSet.objects.filter(
            model_type=field_group,
        ).values_list("id", flat=True))
        results = model.objects.filter(parameter_set_id__in=parameter_set_ids)
        scoped_results = results
        layers = request.query_params.getlist("layer")
        layer_filters = {}
        if layers:
            scoped_results = scoped_results.filter(feature__layer_id__in=layers)
            layer_filters["pk__in"] = layers
        for name in ("sector", "subsector", "asset_type"):
            value = request.query_params.get(name)
            if value is not None:
                scoped_results = scoped_results.filter(**{f"feature__layer__{name}": value})
                layer_filters[name] = value
        hazard = request.query_params.get("hazard")
        if hazard is not None and hazard != "all":
            results = results.filter(hazard=hazard)
            scoped_results = scoped_results.filter(hazard=hazard)
        protector_id = request.query_params.get("protector_id")
        if protector_id is not None:
            if field_group != "adaptation":
                return Response({"protector_id": ["Only supported for adaptation."]}, status=400)
            try:
                protector_id = serializers.IntegerField().run_validation(protector_id)
            except serializers.ValidationError as exc:
                return Response({"protector_id": exc.detail}, status=status.HTTP_400_BAD_REQUEST)
            scoped_results = scoped_results.filter(protector_feature_id=protector_id)

        candidates = scenario_combinations(model, dimensions, parameter_set_ids)
        restricted = inaccessible_hazard_ids(request.user)
        candidates = [row for row in candidates if row["hazard"] not in restricted]
        if hazard is not None and hazard != "all":
            candidates = [row for row in candidates if row["hazard"] == hazard]
        has_scope = bool(layers) or protector_id is not None or any(
            request.query_params.get(name) is not None
            for name in ("sector", "subsector", "asset_type")
        )
        if layer_filters:
            features = Feature.objects.filter(layer_id=OuterRef("pk"))
            bounds = list(FeatureLayer.objects.filter(**layer_filters).annotate(
                first_id=Subquery(features.order_by("id").values("id")[:1]),
                last_id=Subquery(features.order_by("-id").values("id")[:1]),
            ).values("pk", "first_id", "last_id"))

            def available(row):
                checks = [scoped_results.filter(
                    **row, feature__layer_id=bound["pk"],
                    feature_id__gte=bound["first_id"], feature_id__lte=bound["last_id"],
                ).order_by() for bound in bounds if bound["first_id"] is not None]
                if not checks:
                    return False
                # Ranges only narrow the index search. Exact layer membership
                # is still checked, including when feature IDs are interleaved.
                return checks[0].union(*checks[1:], all=True).exists()
        else:
            def available(row):
                return not has_scope or scoped_results.filter(**row).exists()

        rows = [row for row in candidates if available(row)]
        parameter_sets = ModelParameterSet.objects.filter(
            pk__in={row["parameter_set_id"] for row in rows},
        ).prefetch_related(Prefetch(
            "parameters", queryset=ModelParameter.objects.order_by("name"),
        ))
        values = {item.pk: item.values for item in parameter_sets}
        payload = [
            {"parameters": values[row.pop("parameter_set_id")], **row}
            for row in rows
        ]
        payload.sort(key=lambda row: (
            row["hazard"],
            str(row.get("protection_standard", "")),
            row.get("adaptation_name", ""),
            row.get("adaptation_protection_level", 0),
            str(row["parameters"]),
        ))
        return Response(ModelScenarioSerializer(payload, many=True).data)
