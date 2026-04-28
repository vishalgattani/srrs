"""
ram.py — Reliability, Availability, and Maintainability (RAM) metrics.

Author: Vishal Gattani <vishalgattani09@gmail.com>
Created: 2026-04-13
"""

import math

import numpy as np
from pydantic import BaseModel, Field

from ..models.robot import Robot


class RAMResult(BaseModel):
    """System-level RAM metrics computed from robot populations."""

    mtbf: float = Field(description="Mean Time Between Failures")
    mttr: float = Field(description="Mean Time To Repair")
    mdt: float = Field(description="Mean Down Time")
    aoss: float = Field(description="Operational Steady-State Availability")

    model_config = {"frozen": True}


def compute_system_ram(robots: list[Robot]) -> RAMResult:
    """
    Compute system-level RAM from individual robot metrics.

    Uses series reliability model:
      lambda_SRRS = pi(lambda_i) * sigma(mu_i) / pi(mu_i)
    """
    for r in robots:
        r.compute_ram()

    mtbf_list, mttr_list, mdt_list, aoss_list = [], [], [], []
    for r in robots:
        if not math.isnan(r.aoss):
            mtbf_list.append(r.mtbf)
            mttr_list.append(r.mttr)
            mdt_list.append(r.mdt)
            aoss_list.append(r.aoss)

    if not mtbf_list:
        return RAMResult(mtbf=float("nan"), mttr=float("nan"), mdt=float("nan"), aoss=float("nan"))

    mtbf_arr = np.array(mtbf_list)
    mttr_arr = np.array(mttr_list)
    mdt_arr = np.array(mdt_list)

    lambda_robots = np.reciprocal(mtbf_arr)
    mu_robots = np.reciprocal(mttr_arr)

    pi_lambda = float(np.prod(lambda_robots))
    sigma_mu = float(np.sum(mu_robots))
    pi_mu = float(np.prod(mu_robots))
    mdt_srrs = float(np.sum(np.reciprocal(mdt_arr)))

    try:
        lambda_srrs = pi_lambda * sigma_mu / pi_mu
        mtbf_srrs = 1.0 / lambda_srrs
    except ZeroDivisionError:
        mtbf_srrs = float("nan")

    mu_srrs = sigma_mu
    mttr_srrs = 1.0 / mu_srrs if mu_srrs else float("nan")

    try:
        aoss_srrs = mtbf_srrs / (mtbf_srrs + mdt_srrs)
    except Exception:
        aoss_srrs = float("nan")

    return RAMResult(mtbf=mtbf_srrs, mttr=mttr_srrs, mdt=mdt_srrs, aoss=aoss_srrs)
