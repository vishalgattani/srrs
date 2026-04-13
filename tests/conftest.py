"""
conftest.py — Shared pytest fixtures for SRRS tests.

Author: Vishal Gattani <vishalgattani09@gmail.com>
Created: 2026-04-13
"""

import math
import pytest
import pandas as pd

from python.models.types import Config, SimMode
from python.simulation.config import SimulationParams
from python.simulation.runner import run_simulation


TIMESTEPS = 50  # short run for CI speed

EXPECTED_COLUMNS = [
    "Time", "NonPr", "Printable", "Materials", "Env_Materials",
    "#Replicator", "#Normal", "#Assembler", "#Printer",
    "#Assembling", "#Printing", "#Collecting", "#Idle", "#Repair",
    "#In", "#Out",
    "Average Build Quality in-service", "Average Build Quality of System",
    "Average Risk",
]


def make_params(config: Config) -> SimulationParams:
    return SimulationParams(
        config=config,
        mode=SimMode.DETERMINISTIC,
        timesteps=TIMESTEPS,
        num_tasks_before_fail=5,
        quality_threshold=0.5,
        risk_threshold=3.0,
    )


def assert_valid_df(df: pd.DataFrame) -> None:
    assert len(df) == TIMESTEPS, f"Expected {TIMESTEPS} rows, got {len(df)}"
    for col in EXPECTED_COLUMNS:
        assert col in df.columns, f"Missing column: {col}"
    assert (df["#In"] >= 1).all(), "Must always have at least 1 active robot"
    assert (df["Time"] == range(TIMESTEPS)).all(), "Time column must be sequential"


def assert_valid_ram(ram) -> None:
    # At least some metrics should be finite
    assert not (math.isnan(ram.mtbf) and math.isnan(ram.aoss)), \
        "Both MTBF and Aoss are NaN — simulation produced no RAM data"
