"""
test_HHO.py — Simulation tests for configuration HHO.

Author: Vishal Gattani <vishalgattani09@gmail.com>
Created: 2026-04-13
"""

import pytest
from srrs.models.types import Config
from srrs.simulation.runner import run_simulation
from .conftest import make_params, assert_valid_df, assert_valid_ram


def test_hho_simulation_runs():
    """Simulation completes without error for HHO."""
    params = make_params(Config.HHO)
    df, ram = run_simulation(params)
    assert df is not None
    assert ram is not None


def test_hho_dataframe_shape():
    """Output DataFrame has correct shape and columns."""
    params = make_params(Config.HHO)
    df, _ = run_simulation(params)
    assert_valid_df(df)


def test_hho_robot_count_positive():
    """At least one robot must be active throughout."""
    params = make_params(Config.HHO)
    df, _ = run_simulation(params)
    assert (df["#In"] >= 1).all(), "Robot count dropped to zero"


def test_hho_ram_metrics():
    """RAM metrics are computed and at least partially valid."""
    params = make_params(Config.HHO)
    _, ram = run_simulation(params)
    assert_valid_ram(ram)


def test_hho_build_quality_in_range():
    """Average build quality must stay in [0, 1]."""
    params = make_params(Config.HHO)
    df, _ = run_simulation(params)
    assert (df["Average Build Quality in-service"] >= 0).all()
    assert (df["Average Build Quality in-service"] <= 1).all()
