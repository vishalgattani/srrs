"""
stats.py — Monte Carlo aggregation and confidence interval computation.

Author: Vishal Gattani <vishalgattani09@gmail.com>
Created: 2026-04-13
"""

import math
from typing import Any

import pandas as pd


CONFIDENCE_LEVELS = {80: 1.282, 85: 1.440, 90: 1.645, 95: 1.960}

RAM_COLS = ["MTBF", "MTTR", "MDT", "Aoss"]
SUMMARY_COLS = RAM_COLS + [
    "Average Build Quality in-service",
    "Average Build Quality of System",
    "Print Capacity",
    "Assembling Capacity",
    "Collection Capacity",
    "Environment Exhaust Time",
    "Printable Exhaust Time",
    "NonPr Exhaust Time",
    "Material Exhaust Time",
    "#Replicator",
    "#Normal",
    "#Assembler",
    "#Printer",
]


def aggregate_mc_results(mc_rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Aggregate per-run MC results into a summary DataFrame."""
    df = pd.DataFrame(mc_rows)
    df = df.apply(pd.to_numeric, errors="coerce")
    return df


def compute_confidence_intervals(
    df: pd.DataFrame, mc_runs: int
) -> pd.DataFrame:
    """Compute confidence intervals for Aoss across configured levels."""
    rows = []
    mean_aoss = df["Aoss"].mean()
    std_aoss = df["Aoss"].std()

    for pct, z in CONFIDENCE_LEVELS.items():
        me = z * std_aoss / math.sqrt(mc_runs) if mc_runs > 0 else float("nan")
        rows.append(
            {
                "Confidence %": pct,
                "Aoss(Mu)": round(mean_aoss, 4),
                "Aoss(ME)": round(me, 4),
                "Range": [round(mean_aoss - me, 4), round(mean_aoss + me, 4)],
                "MC Iterations": mc_runs,
            }
        )
    return pd.DataFrame(rows)


def describe_results(df: pd.DataFrame) -> pd.DataFrame:
    """Return mean/std/min/max for key metrics."""
    available = [c for c in SUMMARY_COLS if c in df.columns]
    return df[available].describe().loc[["count", "mean", "std", "min", "max"]]
