"""
robot.py — Robot base class and 4 specialised subclasses using Pydantic.

Author: Vishal Gattani <vishalgattani09@gmail.com>
Created: 2026-04-13
"""

from __future__ import annotations

import math
import random
from typing import ClassVar

from pydantic import BaseModel, Field, computed_field

from python.models.types import RobotType, TaskType


class Robot(BaseModel):
    """Base robot model. Tracks identity, task state, and RAM metrics."""

    model_config = {"arbitrary_types_allowed": True}

    # Identity
    robot_type: RobotType
    robot_id: str
    build_qual: float = Field(ge=0.0, le=1.0)
    factory_made: bool = True

    # Task state
    current_task: TaskType = TaskType.IDLE
    prev_task: TaskType = TaskType.IDLE
    next_task: TaskType = TaskType.IDLE
    task_dur: int = 0
    prev_task_dur: int = 0
    time: int = 0

    # Build tracking (for assemblers/replicators)
    being_built_list: list[str] = Field(default_factory=list)
    previously_built: str = ""
    being_built: str = ""

    # Failure/repair tracking
    num_tasks_before_failure: int = 2
    num_tasks_remaining: int = 2
    curr_repair_dur: int = 0
    prev_repair_dur: int = 0

    # RAM counters
    num_success: int = 0
    num_failed: int = 0
    num_repairs: int = 0
    down_time: int = 0
    operational_time: int = 0
    failure_times: list[int] = Field(default_factory=lambda: [0])

    # Risk
    risk_amount: float = 0.0
    risk_set: bool = False

    # RAM computed metrics (populated after simulation)
    mtbf: float = 0.0
    mttr: float = 0.0
    mdt: float = 0.0
    aoss: float = float("nan")

    # Class-level allowed tasks per type (overridden in subclasses)
    ALLOWED_TASKS: ClassVar[list[TaskType]] = []

    @computed_field
    @property
    def num_tasks_performed(self) -> int:
        return self.num_success + self.num_failed

    def set_task(self, task: TaskType, dur: int) -> None:
        self.prev_task = self.current_task
        self.prev_task_dur = self.task_dur
        self.current_task = task
        self.task_dur = dur
        if task == TaskType.IDLE:
            self.task_dur = 0

    def tick(self) -> None:
        """Decrement task duration by 1."""
        if self.task_dur > 0:
            self.task_dur -= 1
        self.time += 1

    def task_success(self) -> None:
        self.num_success += 1

    def task_fail(self) -> None:
        self.num_failed += 1

    def set_risk(self, amount: float) -> None:
        self.risk_amount = amount
        self.risk_set = amount > 0.0

    def reduce_tasks_before_failure(self) -> None:
        self.num_tasks_remaining = max(0, self.num_tasks_remaining - 1)

    def reset_tasks_before_failure(self) -> None:
        self.num_tasks_remaining = self.num_tasks_before_failure

    def add_down_time(self, dur: int) -> None:
        self.down_time += dur

    def add_operational_time(self, dur: int) -> None:
        self.operational_time += dur

    def compute_ram(self) -> None:
        """Compute MTBF, MTTR, MDT, Aoss from counters."""
        try:
            self.mtbf = self.operational_time / self.num_failed if self.num_failed else math.inf
        except Exception:
            self.mtbf = math.inf

        try:
            self.mttr = self.down_time / self.num_repairs if self.num_repairs else math.inf
        except Exception:
            self.mttr = math.inf

        try:
            self.mdt = self.down_time / self.num_failed if self.num_failed else math.inf
        except Exception:
            self.mdt = math.inf

        try:
            denom = self.mdt if self.mdt not in (math.inf, 0) else 0
            self.aoss = self.mtbf / (self.mtbf + denom) if denom else float("nan")
        except Exception:
            self.aoss = float("nan")

    def __str__(self) -> str:
        return f"{self.robot_id},{self.current_task.value},{self.task_dur},tp:{self.num_success}"


class Replicator(Robot):
    """Can assemble, print, and collect. Builds other robots."""

    robot_type: RobotType = RobotType.REPLICATOR
    ALLOWED_TASKS: ClassVar[list[TaskType]] = [
        TaskType.ASSEMBLING,
        TaskType.PRINTING,
        TaskType.COLLECTING,
        TaskType.REPAIR,
    ]


class Normal(Robot):
    """Collector only."""

    robot_type: RobotType = RobotType.NORMAL
    ALLOWED_TASKS: ClassVar[list[TaskType]] = [
        TaskType.COLLECTING,
        TaskType.REPAIR,
    ]


class Assembler(Robot):
    """Assembles new robots and collects."""

    robot_type: RobotType = RobotType.ASSEMBLER
    ALLOWED_TASKS: ClassVar[list[TaskType]] = [
        TaskType.ASSEMBLING,
        TaskType.COLLECTING,
        TaskType.REPAIR,
    ]


class Printer(Robot):
    """Prints components and collects."""

    robot_type: RobotType = RobotType.PRINTER
    ALLOWED_TASKS: ClassVar[list[TaskType]] = [
        TaskType.PRINTING,
        TaskType.COLLECTING,
        TaskType.REPAIR,
    ]


def make_robot(robot_type: RobotType, robot_id: str, build_qual: float) -> Robot:
    """Factory function — returns the correct subclass instance."""
    cls_map = {
        RobotType.REPLICATOR: Replicator,
        RobotType.NORMAL: Normal,
        RobotType.ASSEMBLER: Assembler,
        RobotType.PRINTER: Printer,
    }
    cls = cls_map[robot_type]
    return cls(robot_type=robot_type, robot_id=robot_id, build_qual=build_qual)
