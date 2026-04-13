"""
config.py — Simulation configuration models.

Author: Vishal Gattani <vishalgattani09@gmail.com>
Created: 2026-04-13
"""

from pydantic import BaseModel, Field
from python.models.types import Config, SimMode
from python.models.resources import Resources


# Assembly cost tables: [Replicator, Normal, Assembler, Printer]
COST_PR = [6, 2, 4, 4]
COST_NON_PR = [3, 1, 2, 2]
TIME_COST = {
    "base": 2,
    "print": 2,
    "assemble": 2,
}


class SimulationParams(BaseModel):
    """All tunable simulation parameters."""

    config: Config
    mode: SimMode = SimMode.DETERMINISTIC
    timesteps: int = Field(default=100, gt=0)
    mc_runs: int = Field(default=500, gt=0)

    # Initial resources
    initial_resources: Resources = Resources()

    # Robot costs
    cost_pr: list[int] = COST_PR
    cost_non_pr: list[int] = COST_NON_PR

    # Simulation thresholds
    quality_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    risk_threshold: float = Field(default=3.0, ge=0.0)
    num_tasks_before_fail: int = Field(default=5, gt=0)

    # Quality variation (MC mode)
    quality_incr_chance: float = 5.0
    quality_incr_lower: float = 0.01
    quality_incr_upper: float = 0.05
    quality_decr_chance: float = 50.0
    quality_decr_lower: float = 0.01
    quality_decr_upper: float = 0.25

    # Risk modifiers
    risk_factory_modifier: float = 0.2
    risk_quality_modifier: float = 1.0

    # Print efficiency
    print_efficiency: float = 1.0
    print_amount: float = 1.0
    collect_amount: float = 1.0

    # Build quality range for initial robots
    build_qual_min: float = 0.85
    build_qual_max: float = 0.95
