"""Load return period damages from a single file to database
"""
import pyarrow.parquet as pq

import sys
from itertools import zip_longest
from pathlib import Path
sys.path.insert(0, str(Path("scripts").resolve()))
import django_runtime  # noqa: F401
from map.models import DamagesRp
from result_import import import_results


def yield_return_period_damages(exposure_fname, damage_fname, loss_fname):
    """Generate ReturnPeriodDamage database model objects, reading through
    potentially very large parquet files in row batches.
    """
    batch_size = 100
    with open(exposure_fname, "rb") as exp_source, open(damage_fname, "rb") as dmg_source, open(loss_fname, "rb") as loss_source:
        exp_pf = pq.ParquetFile(exp_source)
        exp_batches = exp_pf.iter_batches(batch_size)
        dmg_pf = pq.ParquetFile(dmg_source)
        dmg_batches = dmg_pf.iter_batches(batch_size)
        loss_pf = pq.ParquetFile(loss_source)
        loss_batches = loss_pf.iter_batches(batch_size)

        for exp_batch, dmg_batch, loss_batch in zip_longest(exp_batches, dmg_batches, loss_batches):
            if exp_batch is None or dmg_batch is None or loss_batch is None:
                raise ValueError("Exposure, damage and loss files have different row counts")
            uids = [batch.column(batch.schema.get_field_index("uid")).to_pylist()
                    for batch in (exp_batch, dmg_batch, loss_batch)]
            if uids[0] != uids[1] or uids[0] != uids[2]:
                raise ValueError("Exposure, damage and loss files have different UID order")
            exp_df = parse_rp_damage_batch(exp_batch).rename(columns={"none": "exposure"})
            dmg_df = parse_rp_damage_batch(dmg_batch).rename(columns={
                "amin": "damage_amin", "mean": "damage_mean", "amax": "damage_amax"})
            loss_df = parse_rp_damage_batch(loss_batch).rename(columns={
                "amin": "loss_amin", "mean": "loss_mean", "amax": "loss_amax"})
            batch_df = dmg_df.join(loss_df, how="outer").join(exp_df, how="outer").fillna(0).reset_index()
            columns = ["damage_amin", "damage_mean", "damage_amax", "loss_amin", "loss_mean", "loss_amax", "exposure"]
            ensure_columns(batch_df, columns)
            for row in batch_df.itertuples():
                params = {"rcp": str(row.rcp), "epoch": int(row.epoch)}
                if row.conf != "None":
                    params["confidence"] = str(row.conf)
                yield params, dict(
                    feature_id=int(row.uid), hazard=str(row.hazard), rp=int(row.rp),
                    **{name: getattr(row, name) for name in columns},
                )



def parse_rp_damage_batch(batch):
    """Parse a parquet (arrow) row batch to pandas"""
    data = batch.to_pandas()
    data_cols = [c for c in batch.schema.names if "rp" in c]
    if not data_cols:
        raise ValueError("No result columns found in source")
    if data["uid"].isna().any():
        raise ValueError("Return-period source has missing feature IDs")

    melted = (
        data.melt(id_vars="uid", value_vars=data_cols)
        .query("value > 0")
        .reset_index(drop=True)
    )

    meta = melted.variable.str.extract(
        r"^(\w+)__rp_(\d+)__rcp_([\w\d.]+)__epoch_(\d+)__?conf_([^_]+)_?(\w+)?"
    )
    meta.columns = ["hazard", "rp", "rcp", "epoch", "conf", "var"]
    if meta[["hazard", "rp", "rcp", "epoch", "conf"]].isna().any().any():
        raise ValueError("Unrecognized return-period damage column name")
    meta["var"] = meta["var"].fillna("none")
    if not meta["var"].isin(["none", "amin", "mean", "amax"]).all():
        raise ValueError("Unrecognized return-period damage statistic")

    return (
        melted.join(meta)
        .drop(columns="variable")
        .pivot(
            index=["uid", "hazard", "rp", "rcp", "epoch", "conf"],
            columns="var",
            values="value",
        )
    )


def ensure_columns(data, expected_columns):
    for col in expected_columns:
        if col not in data.columns:
            data[col] = 0
    return data


if __name__ == "__main__":
    try:
        input = snakemake.input
        exposure = snakemake.input.exposure
        damage = snakemake.input.damage
        loss = snakemake.input.loss
        layer = snakemake.wildcards.layer
        output = snakemake.output
    except NameError:
        print("Expected to run from snakemake")
        exit()

    import_results(
        DamagesRp, "damages_rp", ["parameter_set", "feature", "hazard", "rp"],
        ["exposure", "damage_amin", "damage_mean", "damage_amax", "loss_amin", "loss_mean", "loss_amax"],
        yield_return_period_damages(exposure, damage, loss),
    )

    with open(str(output), "w") as fh:
        fh.write(f"Loaded to database.\n\n")
        fh.write(f"From:\n{input}\n\n")
