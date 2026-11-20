"""Generate reversible UI fixtures using existing features and raster scenarios."""

from collections import defaultdict
import math
import random
import re

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from map.model_parameters import canonical_parameter_key
from map.models import (
    AdaptationCostBenefit,
    DamagesExpected,
    DamagesNpv,
    DamagesRp,
    RasterLayer,
    Feature,
    FeatureLayer,
    ModelParameter,
    ModelParameterSet,
    SyntheticDataRun,
)
from raster.views.shared import _source_options
from map.synthetic_sql import insert_fixtures


RESULT_MODELS = {
    "damages_expected": DamagesExpected,
    "damages_rp": DamagesRp,
    "damages_npv": DamagesNpv,
    "adaptation": AdaptationCostBenefit,
}
ADAPTATIONS = (
    ("Synthetic flood barrier", 50, 0.4),
    ("Synthetic flood barrier", 100, 0.65),
    ("Synthetic asset elevation", 100, 0.8),
)
BATCH_SIZE = 500
FULL_BATCH_SIZE = 1000
FULL_PROTECTOR_GROUP_SIZE = 100


def scalar(value):
    """Match the sidebar's numeric and legacy RCP raster-key normalisation."""
    if not isinstance(value, str):
        return value
    try:
        number = float(value)
    except ValueError:
        return value.replace("x", ".")
    if not math.isfinite(number):
        raise CommandError(f"Non-finite raster parameter: {value!r}")
    return int(number) if number.is_integer() else number


def raster_scenarios(dataset):
    """Keep complete climate combinations; RP and confidence are result axes."""
    source = dataset.tile_source
    filters = {"type": dataset.pk} if "type" in source.keys else None
    try:
        domains = _source_options(source.database, filters=filters)
    except Exception as exc:
        raise CommandError(
            f"Cannot read raster scenarios for {dataset.pk}: {exc}"
        ) from exc
    combinations = {}
    for row in domains:
        parameters = {}
        return_period = None
        for name, value in row.items():
            lower = name.lower().replace("_", "")
            if lower == "type" or lower == "confidence":
                continue
            if lower in ("rp", "returnperiod"):
                return_period = scalar(value)
            else:
                parameters[name] = scalar(value)
        if (
            not isinstance(return_period, (int, float))
            or isinstance(return_period, bool)
            or return_period <= 0
            or int(return_period) != return_period
        ):
            raise CommandError(
                f"{dataset.pk} needs positive integer return periods in its raster domains."
            )
        key = canonical_parameter_key(parameters)
        combination = combinations.setdefault(
            key, {"parameters": parameters, "return_periods": set()}
        )
        combination["return_periods"].add(int(return_period))
    if not combinations:
        raise CommandError(f"No raster scenarios found for {dataset.pk}.")
    return [
        {
            "parameters": item["parameters"],
            "return_periods": sorted(item["return_periods"]),
        }
        for _, item in sorted(combinations.items())
    ]


def sample_features(layer_id, limit, seed):
    """Reservoir-sample IDs without fetching geometries or sorting randomly in SQL."""
    rng = random.Random(f"{seed}:sample:{layer_id}")
    sample = []
    ids = (
        Feature.objects.filter(layer_id=layer_id, id__gt=0)
        .order_by("id")
        .values_list("id", flat=True)
    )
    if limit is None:
        return list(ids.iterator(chunk_size=10000))
    for index, feature_id in enumerate(ids.iterator(chunk_size=10000)):
        if index < limit:
            sample.append(feature_id)
        else:
            replacement = rng.randrange(index + 1)
            if replacement < limit:
                sample[replacement] = feature_id
    return sorted(sample)


def uncertainty(prefix, mean):
    return {
        f"{prefix}_amin": None if mean is None else round(mean * 0.7, 2),
        f"{prefix}_mean": mean,
        f"{prefix}_amax": None if mean is None else round(mean * 1.3, 2),
    }


def fixture_values(seed, feature_id, hazard, scenario_index, return_periods, position):
    rng = random.Random(f"{seed}:values:{feature_id}:{hazard}")
    base = 10 ** rng.uniform(4, 7)
    severity = 1 + scenario_index * 0.25
    # Include zero/missing results in larger samples; keep the first feature,
    # which is also the default protector, useful for an immediate UI check.
    status = position % 10
    multiplier = 0 if status == 8 else 1
    damages = [
        round(base * severity * (rp / max(return_periods)) ** 0.4 * multiplier, 2)
        for rp in return_periods
    ]
    points = [
        (1, 0),
        *[(1 / rp, damage) for rp, damage in zip(return_periods, damages)],
        (0, damages[-1]),
    ]
    annual = round(
        sum(
            (p0 - p1) * (d0 + d1) / 2 for (p0, d0), (p1, d1) in zip(points, points[1:])
        ),
        2,
    )
    if status == 9:
        return None, None, [None] * len(damages), round(base * 0.08, 2)
    return annual, round(annual * 0.35, 2), damages, round(base * 0.08, 2)


class Command(BaseCommand):
    help = "Seed deterministic SYNTHETIC UI data. Existing results are preserved unless --replace is supplied."

    def add_arguments(self, parser):
        parser.add_argument(
            "--name",
            default="development",
            help="Named run, also used for cleanup (default: development).",
        )
        parser.add_argument("--seed", type=int, default=42)
        coverage = parser.add_mutually_exclusive_group()
        coverage.add_argument(
            "--limit-per-layer",
            type=int,
            default=25,
            help="Maximum sampled features per layer (default: 25).",
        )
        coverage.add_argument(
            "--all-features",
            action="store_true",
            help="Cover every positive-ID feature in the selected layers using set-based generation.",
        )
        parser.add_argument(
            "--layer",
            action="append",
            default=[],
            help="Feature layer ID; repeat to select several (default: all layers).",
        )
        parser.add_argument(
            "--hazard",
            action="append",
            default=[],
            help="Hazard dataset ID; repeat to select several (default: all hazard rasters).",
        )
        parser.add_argument(
            "--protector-id",
            type=int,
            action="append",
            default=[],
            help="Existing protector feature ID; repeat to distribute links among several. Defaults to the first sampled feature per layer.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report the plan without writing to the database.",
        )
        action = parser.add_mutually_exclusive_group()
        action.add_argument(
            "--clear",
            action="store_true",
            help="Remove only rows created by this named run.",
        )
        action.add_argument(
            "--replace",
            action="store_true",
            help="Replace ALL rows in the four result tables, then seed the selected layers/hazards in one transaction. Feature tables are preserved.",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["dry_run"]:
            raise CommandError(
                "Synthetic results may only be written or cleared with DEBUG=True."
            )
        name = options["name"]
        if not re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", name):
            raise CommandError(
                "--name must start with a lowercase letter and contain at most 64 lowercase letters, digits, underscores or hyphens."
            )
        if options["limit_per_layer"] <= 0:
            raise CommandError("--limit-per-layer must be positive.")
        config = {key: options[key] for key in ("seed", "limit_per_layer")}
        config.update(
            {
                key: sorted(set(options[key]))
                for key in ("layer", "hazard", "protector_id")
            }
        )
        if options["all_features"]:
            config["limit_per_layer"] = None
        if options["replace"]:
            config["replace"] = True
        run = SyntheticDataRun.objects.filter(pk=name).first()
        if options["clear"]:
            if not run:
                self.stdout.write(f"No synthetic run named {name!r}; nothing to clear.")
                return
            self.clear(run, options["dry_run"])
            return
        if run and not options["replace"]:
            if run.config != config:
                raise CommandError(
                    f"Run {name!r} already exists with different options. Clear it before regenerating."
                )
            self.stdout.write(
                f"Synthetic run {name!r} already exists; nothing changed."
            )
            self.report(run.result_ids)
            return

        datasets = (
            RasterLayer.objects.filter(dataset__group__iexact="hazards")
            .select_related("tile_source")
            .order_by("id")
        )
        if config["hazard"]:
            datasets = datasets.filter(pk__in=config["hazard"])
        datasets = list(datasets)
        missing = set(config["hazard"]) - {item.pk for item in datasets}
        if missing:
            raise CommandError(
                f"Unknown hazards or missing raster sources: {', '.join(sorted(missing))}"
            )
        if not datasets:
            raise CommandError("No hazard datasets with raster sources were found.")
        scenarios = {item.pk: raster_scenarios(item) for item in datasets}

        layers = FeatureLayer.objects.order_by("pk")
        if config["layer"]:
            layers = layers.filter(pk__in=config["layer"])
        layers = list(layers)
        missing = set(config["layer"]) - {item.pk for item in layers}
        if missing:
            raise CommandError(f"Unknown feature layers: {', '.join(sorted(missing))}")
        samples = {
            layer.pk: sample_features(
                layer.pk, config["limit_per_layer"], config["seed"]
            )
            for layer in layers
        }
        samples = {layer: ids for layer, ids in samples.items() if ids}
        if not samples:
            raise CommandError("No positive-ID features found in the selected layers.")
        protectors = config["protector_id"]
        if protectors:
            if any(item <= 0 or item > 2147483647 for item in protectors):
                raise CommandError("Protector IDs must fit a positive 32-bit integer.")
            if set(protectors) != set(
                Feature.objects.filter(pk__in=protectors).values_list("pk", flat=True)
            ):
                raise CommandError(
                    "Every --protector-id must identify an existing feature."
                )
        elif any(ids[0] > 2147483647 for ids in samples.values()):
            raise CommandError(
                "Default protector IDs exceed the result field's range; specify --protector-id."
            )

        per_feature = defaultdict(int)
        for combinations in scenarios.values():
            for item in combinations:
                per_feature["damages_expected"] += 2
                per_feature["damages_rp"] += len(item["return_periods"])
                per_feature["damages_npv"] += 1
                per_feature["adaptation"] += len(ADAPTATIONS)
        feature_count = sum(map(len, samples.values()))
        self.stdout.write(
            f"SYNTHETIC UI fixtures: run={name}, seed={config['seed']}, {feature_count} features across {len(samples)} layers."
        )
        for hazard, combinations in scenarios.items():
            self.stdout.write(
                f"  {hazard}: {len(combinations)} scenarios: "
                + ", ".join(
                    canonical_parameter_key(item["parameters"]) for item in combinations
                )
            )
        for layer, ids in samples.items():
            self.stdout.write(
                f"  {layer}: {len(ids)} features; example/protector ID {protectors[0] if protectors else ids[0]}"
            )
        self.stdout.write("Planned row counts (existing result keys will be skipped):")
        self.report(
            {key: range(count * feature_count) for key, count in per_feature.items()}
        )
        if options["replace"]:
            self.stdout.write(
                "Replacement will remove ALL existing result rows, including imported results:"
            )
            for key, model in RESULT_MODELS.items():
                self.stdout.write(f"  {key}: {model.objects.count():,}")
        if options["dry_run"]:
            self.stdout.write("Dry run: no database changes.")
            return

        with transaction.atomic():
            if options["replace"]:
                # The four tables contain results only. No CASCADE or feature
                # table is included; TRUNCATE is transactional in PostgreSQL.
                connection.check_constraints()
                tables = ", ".join(
                    connection.ops.quote_name(model._meta.db_table)
                    for model in RESULT_MODELS.values()
                )
                with connection.cursor() as cursor:
                    cursor.execute("TRUNCATE TABLE " + tables)
                SyntheticDataRun.objects.all().delete()
            if options["all_features"]:
                # check_constraints() above restores deferred mode. Switch
                # after that call so each bulk statement checks its own FKs.
                with connection.cursor() as cursor:
                    cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
            run = SyntheticDataRun.objects.create(name=name, config=config)
            owned_parameters = []
            parameter_sets = {}
            for combinations in scenarios.values():
                for item in combinations:
                    parameters = item["parameters"]
                    for model_type in RESULT_MODELS:
                        key = (model_type, canonical_parameter_key(parameters))
                        if key in parameter_sets:
                            continue
                        (
                            parameter_set,
                            created,
                        ) = ModelParameterSet.objects.get_or_create(
                            model_type=model_type, canonical_key=key[1]
                        )
                        if created:
                            ModelParameter.objects.bulk_create(
                                [
                                    ModelParameter(
                                        parameter_set=parameter_set,
                                        name=name,
                                        value=value,
                                    )
                                    for name, value in parameters.items()
                                ]
                            )
                            owned_parameters.append(parameter_set.pk)
                        elif canonical_parameter_key(parameter_set.values) != key[1]:
                            raise CommandError(
                                f"Inconsistent existing parameter set {parameter_set.pk}; no synthetic data was saved."
                            )
                        parameter_sets[key] = parameter_set.pk
            result_ids = {
                key: ({"ranges": [], "count": 0} if options["all_features"] else [])
                for key in RESULT_MODELS
            }
            if options["all_features"]:
                self.generate_all(
                    samples,
                    scenarios,
                    protectors,
                    config["seed"],
                    parameter_sets,
                    result_ids,
                )
            pending = {key: [] for key in RESULT_MODELS}
            for layer, ids in [] if options["all_features"] else samples.items():
                for position, feature_id in enumerate(ids):
                    protector_id = (
                        protectors[position % len(protectors)] if protectors else ids[0]
                    )
                    for hazard, combinations in scenarios.items():
                        for scenario_index, item in enumerate(combinations):
                            self.generate(
                                pending,
                                feature_id,
                                protector_id,
                                hazard,
                                item,
                                scenario_index,
                                position,
                                config["seed"],
                                parameter_sets,
                            )
                            for key in RESULT_MODELS:
                                if len(pending[key]) >= BATCH_SIZE:
                                    self.insert(key, pending[key], result_ids)
            for key in RESULT_MODELS:
                self.insert(key, pending[key], result_ids)
            run.result_ids = result_ids
            run.parameter_set_ids = owned_parameters
            run.save(update_fields=["result_ids", "parameter_set_ids"])
            if options["all_features"]:
                with connection.cursor() as cursor:
                    cursor.execute("SET CONSTRAINTS ALL DEFERRED")
        message = (
            "Existing results were replaced."
            if options["replace"]
            else "Imported results were preserved."
        )
        self.stdout.write(
            self.style.SUCCESS(f"Created synthetic run {name!r}. {message}")
        )
        self.report(result_ids)

    def generate_all(
        self, samples, scenarios, protectors, seed, parameter_sets, result_ids
    ):
        sql_scenarios = {key: [] for key in RESULT_MODELS}
        for hazard, combinations in scenarios.items():
            for index, item in enumerate(combinations):
                periods = item["return_periods"]
                points = [
                    (1, 0),
                    *[(1 / rp, (rp / max(periods)) ** 0.4) for rp in periods],
                    (0, 1),
                ]
                factor = sum(
                    (p0 - p1) * (d0 + d1) / 2
                    for (p0, d0), (p1, d1) in zip(points, points[1:])
                )
                for key in RESULT_MODELS:
                    sql_scenarios[key].append(
                        {
                            "hazard": hazard,
                            "parameter_set_id": parameter_sets[
                                (key, canonical_parameter_key(item["parameters"]))
                            ],
                            "severity": 1 + index * 0.25,
                            "annual_factor": factor,
                            "periods": periods,
                        }
                    )
        for layer, ids in samples.items():
            for start in range(0, len(ids), FULL_BATCH_SIZE):
                features = [
                    (
                        feature_id,
                        position,
                        protectors[position % len(protectors)]
                        if protectors
                        else ids[
                            position
                            // FULL_PROTECTOR_GROUP_SIZE
                            * FULL_PROTECTOR_GROUP_SIZE
                        ],
                    )
                    for position, feature_id in enumerate(
                        ids[start : start + FULL_BATCH_SIZE], start
                    )
                ]
                for key, model in RESULT_MODELS.items():
                    manifest = result_ids[key]
                    for first, last, count in insert_fixtures(
                        model, key, features, sql_scenarios[key], seed, ADAPTATIONS
                    ):
                        ranges = manifest["ranges"]
                        if ranges and ranges[-1][1] + 1 == first:
                            ranges[-1][1] = last
                        else:
                            ranges.append([first, last])
                        manifest["count"] += count
                self.stdout.write(
                    f"  Generated {layer}: {min(start + FULL_BATCH_SIZE, len(ids)):,}/{len(ids):,} features"
                )
                self.stdout.flush()

    def generate(
        self,
        pending,
        feature_id,
        protector_id,
        hazard,
        item,
        scenario_index,
        position,
        seed,
        parameter_sets,
    ):
        annual, loss, damages, cost = fixture_values(
            seed, feature_id, hazard, scenario_index, item["return_periods"], position
        )
        parameter_key = canonical_parameter_key(item["parameters"])

        def common(model_type):
            return {
                "feature_id": feature_id,
                "hazard": hazard,
                "parameter_set_id": parameter_sets[(model_type, parameter_key)],
            }

        for protection, fraction in ((0, 1), (100, 0.6)):
            pending["damages_expected"].append(
                DamagesExpected(
                    **common("damages_expected"),
                    protection_standard=protection,
                    **uncertainty(
                        "ead", None if annual is None else round(annual * fraction, 2)
                    ),
                    **uncertainty(
                        "eael", None if loss is None else round(loss * fraction, 2)
                    ),
                )
            )
        pending["damages_npv"].append(
            DamagesNpv(
                **common("damages_npv"),
                **uncertainty("ead", None if annual is None else round(annual * 15, 2)),
                **uncertainty("eael", None if loss is None else round(loss * 15, 2)),
            )
        )
        for rp, damage in zip(item["return_periods"], damages):
            pending["damages_rp"].append(
                DamagesRp(
                    **common("damages_rp"),
                    rp=rp,
                    exposure=None if damage is None else (0 if damage == 0 else 1),
                    **uncertainty("damage", damage),
                    **uncertainty(
                        "loss", None if damage is None else round(damage * 0.35, 2)
                    ),
                )
            )
        for name, level, fraction in ADAPTATIONS:
            pending["adaptation"].append(
                AdaptationCostBenefit(
                    **common("adaptation"),
                    adaptation_name=name,
                    adaptation_protection_level=level,
                    protector_feature_id=protector_id,
                    adaptation_cost=cost,
                    **uncertainty(
                        "avoided_ead",
                        None if annual is None else round(annual * fraction, 2),
                    ),
                    **uncertainty(
                        "avoided_eael",
                        None if loss is None else round(loss * fraction, 2),
                    ),
                )
            )

    def insert(self, key, rows, result_ids):
        if not rows:
            return
        model = RESULT_MODELS[key]
        # Checking exact composite keys lets us retain ownership only of new
        # rows. ON CONFLICT DO NOTHING cannot return IDs for that distinction.
        existing = set(
            model.objects.filter(pk__in=[row.pk for row in rows]).values_list(
                *model._meta.pk.field_names
            )
        )
        created = model.objects.bulk_create(
            [row for row in rows if row.pk not in existing], batch_size=BATCH_SIZE
        )
        result_ids[key].extend(row.id for row in created)
        rows.clear()

    def clear(self, run, dry_run):
        self.stdout.write(
            f"{'Would clear' if dry_run else 'Clearing'} synthetic run {run.pk!r}:"
        )
        self.report(run.result_ids)
        if dry_run:
            return
        with transaction.atomic():
            for key, ids in run.result_ids.items():
                if isinstance(ids, dict):
                    for first, last in ids["ranges"]:
                        RESULT_MODELS[key].objects.filter(
                            id__gte=first, id__lte=last
                        ).delete()
                    continue
                for start in range(0, len(ids), BATCH_SIZE):
                    RESULT_MODELS[key].objects.filter(
                        id__in=ids[start : start + BATCH_SIZE]
                    ).delete()
            for parameter_set_id in run.parameter_set_ids:
                if not any(
                    model.objects.filter(parameter_set_id=parameter_set_id).exists()
                    for model in RESULT_MODELS.values()
                ):
                    ModelParameterSet.objects.filter(pk=parameter_set_id).delete()
            run.delete()

    def report(self, result_ids):
        for key, ids in result_ids.items():
            count = ids["count"] if isinstance(ids, dict) else len(ids)
            self.stdout.write(f"  {key}: {count:,}")
