"""
runner.py — Core simulation loop, decoupled from I/O.

Author: Vishal Gattani <vishalgattani09@gmail.com>
Created: 2026-04-13
"""

from __future__ import annotations

import math
import random
from copy import deepcopy

import pandas as pd

from python.models.robot import Robot, Replicator, Normal, Assembler, Printer, make_robot
from python.models.resources import Resources
from python.models.types import RobotType, TaskType, Config
from python.simulation.config import SimulationParams, COST_PR, COST_NON_PR
from python.analysis.ram import compute_system_ram, RAMResult

DECIMAL_PLACES = 3

TABLE_COLUMNS = [
    "Time", "NonPr", "Printable", "Materials", "Env_Materials",
    "#Replicator", "#Normal", "#Assembler", "#Printer",
    "#Assembling", "#Printing", "#Collecting", "#Idle", "#Repair",
    "#In", "#Out",
    "Average Build Quality in-service", "Average Build Quality of System",
    "#WasteReplicator", "#WasteNormal", "#WasteAssembler", "#WastePrinter",
    "Environment Exhaust Time", "Printable Exhaust Time",
    "NonPr Exhaust Time", "Material Exhaust Time", "Average Risk",
]

_robot_id_counters: dict[RobotType, int] = {t: 0 for t in RobotType}


def _next_id(robot_type: RobotType) -> str:
    _robot_id_counters[robot_type] += 1
    return f"{robot_type.value[0]}{_robot_id_counters[robot_type]}"


def _reset_counters(init: dict[RobotType, int] | None = None) -> None:
    for t in RobotType:
        _robot_id_counters[t] = init.get(t, 0) if init else 0


# ── Risk ──────────────────────────────────────────────────────────────────────

def _task_risk(robot: Robot, params: SimulationParams) -> float:
    task = robot.current_task
    risk_task_type = 0 if task in (TaskType.IDLE, TaskType.REPAIR) else 1
    rand = round(random.uniform(0, 1), DECIMAL_PLACES)
    modifier = params.risk_factory_modifier if robot.factory_made else params.risk_quality_modifier
    return (1.0 - robot.build_qual) * (risk_task_type + rand * modifier)


# ── Task helpers ──────────────────────────────────────────────────────────────

def _can_collect(robot: Robot, res: Resources, params: SimulationParams) -> bool:
    return res.can_collect(params.collect_amount)


def _can_print(robot: Robot, res: Resources, params: SimulationParams) -> bool:
    return robot.robot_type in (RobotType.REPLICATOR, RobotType.PRINTER) and \
           res.can_print(params.print_efficiency, params.print_amount)


def _assemble_cost(robot_type: RobotType) -> tuple[float, float]:
    idx = [RobotType.REPLICATOR, RobotType.NORMAL, RobotType.ASSEMBLER, RobotType.PRINTER].index(robot_type)
    return COST_PR[idx], COST_NON_PR[idx]


def _can_assemble(robot: Robot, tobuild: RobotType, res: Resources) -> bool:
    cp, cnp = _assemble_cost(tobuild)
    return res.can_assemble(cp, cnp)


def _do_collect(robot: Robot, res: Resources, params: SimulationParams, mc: bool) -> bool:
    robot.set_task(TaskType.COLLECTING, 1)
    if not mc and robot.num_tasks_remaining == 0:
        robot.task_fail()
        _do_repair(robot, params)
        return False
    robot.add_operational_time(robot.task_dur)
    res.collect(params.collect_amount)
    robot.task_success()
    if not mc:
        robot.reduce_tasks_before_failure()
    robot.set_risk(0.0)
    return True


def _do_print(robot: Robot, res: Resources, params: SimulationParams, mc: bool) -> bool:
    robot.set_task(TaskType.PRINTING, 2)
    if not mc and robot.num_tasks_remaining == 0:
        robot.task_fail()
        _do_repair(robot, params)
        return False
    robot.add_operational_time(robot.task_dur)
    robot.task_success()
    res.print_material(params.print_efficiency, params.print_amount)
    if not mc:
        robot.reduce_tasks_before_failure()
    return True


def _do_assemble(builder: Robot, tobuild: RobotType, res: Resources, params: SimulationParams, mc: bool) -> bool:
    time_map = {
        RobotType.REPLICATOR: 6,
        RobotType.NORMAL: 2,
        RobotType.ASSEMBLER: 4,
        RobotType.PRINTER: 4,
    }
    builder.set_task(TaskType.ASSEMBLING, time_map[tobuild])
    if not mc and builder.num_tasks_remaining == 0:
        builder.task_fail()
        _do_repair(builder, params)
        return False
    cp, cnp = _assemble_cost(tobuild)
    res.consume_assembly(cp, cnp)
    rid = _next_id(tobuild)
    builder.being_built_list.append(f"{tobuild.value[0]}{rid.lstrip(tobuild.value[0])}")
    builder.previously_built = tobuild.value
    if not mc:
        builder.reduce_tasks_before_failure()
    builder.add_operational_time(builder.task_dur)
    return True


def _finish_assemble(builder: Robot, tobuild: RobotType, params: SimulationParams, mc: bool) -> Robot | None:
    """Pop the next robot from the build queue and create it."""
    if not builder.being_built_list:
        return None
    raw_id = builder.being_built_list.pop(0)
    qual = builder.build_qual
    if mc:
        rand = round(random.uniform(0, 1), DECIMAL_PLACES)
        if rand > round(1.0 - params.quality_incr_chance / 100, DECIMAL_PLACES):
            qual += random.uniform(params.quality_incr_lower, params.quality_incr_upper)
        elif rand < params.quality_decr_chance:
            qual -= random.uniform(params.quality_decr_lower, params.quality_decr_upper)
    qual = max(0.0, min(1.0, qual))
    new_robot = make_robot(tobuild, raw_id, qual)
    builder.task_success()
    return new_robot


def _do_repair(robot: Robot, params: SimulationParams) -> None:
    robot.failure_times.append(robot.time)
    repair_dur = robot.task_dur
    robot.next_task = robot.current_task
    robot.set_task(TaskType.REPAIR, repair_dur)
    robot.num_repairs += 1
    robot.add_down_time(repair_dur)
    robot.reset_tasks_before_failure()


def _idle(robot: Robot) -> None:
    robot.set_task(TaskType.IDLE, 0)


# ── Config snapshot ───────────────────────────────────────────────────────────

def _snapshot(t: int, active: list[Robot], waste: list[Robot], res: Resources) -> dict:
    counts = {rt: 0 for rt in RobotType}
    tasks = {tt: 0 for tt in TaskType}
    total_qual_in = 0.0
    total_qual_all = 0.0
    avg_risk = 0.0
    waste_counts = {rt: 0 for rt in RobotType}

    for r in active:
        counts[r.robot_type] += 1
        tasks[r.current_task] += 1
        total_qual_in += r.build_qual
        total_qual_all += r.build_qual
        avg_risk += r.risk_set

    for r in waste:
        total_qual_all += r.build_qual
        waste_counts[r.robot_type] += 1

    n = len(active)
    n_all = len(active) + len(waste)
    avg_qual_in = round(total_qual_in / n, DECIMAL_PLACES) if n else 0.0
    avg_qual_all = round(total_qual_all / n_all, DECIMAL_PLACES) if n_all else 0.0
    avg_risk = avg_risk / n if n else 0.0

    return {
        "Time": t,
        "NonPr": res.non_printable,
        "Printable": res.printable,
        "Materials": res.materials,
        "Env_Materials": res.env_materials,
        "#Replicator": counts[RobotType.REPLICATOR],
        "#Normal": counts[RobotType.NORMAL],
        "#Assembler": counts[RobotType.ASSEMBLER],
        "#Printer": counts[RobotType.PRINTER],
        "#Assembling": tasks[TaskType.ASSEMBLING],
        "#Printing": tasks[TaskType.PRINTING],
        "#Collecting": tasks[TaskType.COLLECTING],
        "#Idle": tasks[TaskType.IDLE],
        "#Repair": tasks[TaskType.REPAIR],
        "#In": n,
        "#Out": len(waste),
        "Average Build Quality in-service": avg_qual_in,
        "Average Build Quality of System": avg_qual_all,
        "#WasteReplicator": waste_counts[RobotType.REPLICATOR],
        "#WasteNormal": waste_counts[RobotType.NORMAL],
        "#WasteAssembler": waste_counts[RobotType.ASSEMBLER],
        "#WastePrinter": waste_counts[RobotType.PRINTER],
        "Environment Exhaust Time": res.env_exhaust_time,
        "Printable Exhaust Time": res.print_exhaust_time,
        "NonPr Exhaust Time": res.non_pr_exhaust_time,
        "Material Exhaust Time": res.mat_exhaust_time,
        "Average Risk": avg_risk,
    }


# ── Main simulation ───────────────────────────────────────────────────────────

def run_simulation(params: SimulationParams) -> tuple[pd.DataFrame, RAMResult]:
    """
    Run a single deterministic or MC simulation pass.

    Returns:
        df: Per-timestep DataFrame.
        ram: System-level RAMResult.
    """
    _reset_counters()
    mc = params.mode.value == "MC"
    res = deepcopy(params.initial_resources)

    # Initialise starting robots per config
    qual = round(random.uniform(params.build_qual_min, params.build_qual_max), DECIMAL_PLACES)
    active: list[Robot] = []
    waste: list[Robot] = []
    rows: list[dict] = []

    config = params.config
    if config in (Config.CHO, Config.DHO, Config.HHO):
        r = make_robot(RobotType.REPLICATOR, _next_id(RobotType.REPLICATOR), qual)
        r.factory_made = True
        active = [r]
    else:  # CHE, DHE, HHE
        p = make_robot(RobotType.PRINTER, _next_id(RobotType.PRINTER), qual)
        a = make_robot(RobotType.ASSEMBLER, _next_id(RobotType.ASSEMBLER), qual)
        p.factory_made = True
        a.factory_made = True
        active = [p, a]

    for t in range(params.timesteps):
        new_robots: list[Robot] = []

        for robot in active:
            robot.time = t
            robot.num_tasks_before_failure = params.num_tasks_before_fail

            if robot.current_task == TaskType.IDLE:
                _assign_task_idle(robot, active, res, params, mc)

            elif robot.current_task == TaskType.REPAIR:
                if robot.task_dur <= 1:
                    _assign_task_after_repair(robot, res, params, mc)
                else:
                    robot.task_dur -= 1

            else:
                # Tick task
                if robot.task_dur > 1:
                    robot.task_dur -= 1
                else:
                    # Task completion
                    spawned = _complete_task(robot, active, res, params, mc)
                    if spawned:
                        for new_bot in spawned:
                            if new_bot.build_qual >= params.quality_threshold:
                                _assign_task_idle(new_bot, active, res, params, mc)
                                active.append(new_bot)
                            else:
                                waste.append(new_bot)
                            new_robots.append(new_bot)

        res.update_exhaust_times(t)
        rows.append(_snapshot(t, active, waste, res))

    ram = compute_system_ram(active)
    df = pd.DataFrame(rows, columns=TABLE_COLUMNS)
    df["Print Capacity"] = df[["#Printer", "#Replicator"]].sum(axis=1)
    df["Assembling Capacity"] = df[["#Assembler", "#Replicator"]].sum(axis=1)
    df["Collection Capacity"] = df[["#Printer", "#Replicator", "#Assembler", "#Normal"]].sum(axis=1)
    return df, ram


# ── Task dispatch helpers (config-specific logic extracted) ───────────────────

def _assign_task_idle(robot: Robot, active: list[Robot], res: Resources, params: SimulationParams, mc: bool) -> None:
    config = params.config

    match robot.robot_type:
        case RobotType.REPLICATOR:
            if config == Config.CHO:
                if _can_assemble(robot, RobotType.NORMAL, res):
                    _do_assemble(robot, RobotType.NORMAL, res, params, mc)
                elif _can_print(robot, res, params):
                    _do_print(robot, res, params, mc)
                else:
                    _idle(robot)
            elif config == Config.DHO:
                if _can_assemble(robot, RobotType.REPLICATOR, res):
                    _do_assemble(robot, RobotType.REPLICATOR, res, params, mc)
                elif _can_print(robot, res, params):
                    _do_print(robot, res, params, mc)
                elif _can_collect(robot, res, params):
                    _do_collect(robot, res, params, mc)
                else:
                    _idle(robot)
            else:  # HHO
                prev = robot.previously_built
                if not prev:
                    if _can_assemble(robot, RobotType.REPLICATOR, res):
                        _do_assemble(robot, RobotType.REPLICATOR, res, params, mc)
                    elif _can_assemble(robot, RobotType.NORMAL, res):
                        _do_assemble(robot, RobotType.NORMAL, res, params, mc)
                    elif _can_print(robot, res, params):
                        _do_print(robot, res, params, mc)
                    else:
                        _idle(robot)
                else:
                    next_build = RobotType.NORMAL if prev == RobotType.REPLICATOR.value else RobotType.REPLICATOR
                    if _can_assemble(robot, next_build, res):
                        _do_assemble(robot, next_build, res, params, mc)
                    elif _can_print(robot, res, params):
                        _do_print(robot, res, params, mc)
                    else:
                        _idle(robot)

        case RobotType.NORMAL:
            if _can_collect(robot, res, params):
                _do_collect(robot, res, params, mc)
            else:
                _idle(robot)

        case RobotType.ASSEMBLER:
            if config == Config.CHE:
                if _can_assemble(robot, RobotType.NORMAL, res):
                    _do_assemble(robot, RobotType.NORMAL, res, params, mc)
                elif _can_collect(robot, res, params):
                    _do_collect(robot, res, params, mc)
                else:
                    _idle(robot)
            elif config in (Config.DHE, Config.HHE):
                prev = robot.previously_built
                if not prev:
                    if _can_assemble(robot, RobotType.ASSEMBLER, res):
                        _do_assemble(robot, RobotType.ASSEMBLER, res, params, mc)
                    elif _can_assemble(robot, RobotType.PRINTER, res):
                        _do_assemble(robot, RobotType.PRINTER, res, params, mc)
                    elif _can_collect(robot, res, params):
                        _do_collect(robot, res, params, mc)
                    else:
                        _idle(robot)
                else:
                    next_build = RobotType.PRINTER if prev == RobotType.ASSEMBLER.value else RobotType.ASSEMBLER
                    if _can_assemble(robot, next_build, res):
                        _do_assemble(robot, next_build, res, params, mc)
                    elif _can_collect(robot, res, params):
                        _do_collect(robot, res, params, mc)
                    else:
                        _idle(robot)

        case RobotType.PRINTER:
            if _can_print(robot, res, params):
                _do_print(robot, res, params, mc)
            elif _can_collect(robot, res, params):
                _do_collect(robot, res, params, mc)
            else:
                _idle(robot)


def _assign_task_after_repair(robot: Robot, res: Resources, params: SimulationParams, mc: bool) -> None:
    next_t = robot.next_task
    match robot.robot_type:
        case RobotType.REPLICATOR | RobotType.ASSEMBLER:
            if next_t == TaskType.ASSEMBLING:
                pass  # handled in complete_task
            elif next_t == TaskType.PRINTING and _can_print(robot, res, params):
                _do_print(robot, res, params, mc)
            elif next_t == TaskType.COLLECTING and _can_collect(robot, res, params):
                _do_collect(robot, res, params, mc)
            else:
                _idle(robot)
        case RobotType.NORMAL:
            if next_t == TaskType.COLLECTING and _can_collect(robot, res, params):
                _do_collect(robot, res, params, mc)
            else:
                _idle(robot)
        case RobotType.PRINTER:
            if next_t == TaskType.PRINTING and _can_print(robot, res, params):
                _do_print(robot, res, params, mc)
            else:
                _idle(robot)


def _complete_task(robot: Robot, active: list[Robot], res: Resources, params: SimulationParams, mc: bool) -> list[Robot]:
    """Handle task completion — returns list of newly spawned robots."""
    spawned = []

    if robot.current_task in (TaskType.ASSEMBLING,) and robot.being_built_list:
        prev = robot.previously_built
        tobuild = RobotType(prev) if prev else RobotType.NORMAL
        new_bot = _finish_assemble(robot, tobuild, params, mc)
        if new_bot:
            spawned.append(new_bot)

    # Re-assign next task
    _assign_task_idle(robot, active, res, params, mc)
    return spawned
