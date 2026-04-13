"""
types.py — Enums for robot types and task types.

Author: Vishal Gattani <vishalgattani09@gmail.com>
Created: 2026-04-13
"""

from enum import Enum


class RobotType(str, Enum):
    REPLICATOR = "Replicator"
    NORMAL = "Normal"
    ASSEMBLER = "Assembler"
    PRINTER = "Printer"


class TaskType(str, Enum):
    IDLE = "idle"
    COLLECTING = "collecting"
    ASSEMBLING = "assembling"
    PRINTING = "printing"
    REPAIR = "repair"


class SimMode(str, Enum):
    DETERMINISTIC = "D"
    MONTE_CARLO = "MC"


class Config(str, Enum):
    CHO = "CHO"  # Collect-Homogeneous-One
    DHO = "DHO"  # Deterministic-Homogeneous-One
    HHO = "HHO"  # Heterogeneous-Homogeneous-One
    CHE = "CHE"  # Collect-Heterogeneous-External
    DHE = "DHE"  # Deterministic-Heterogeneous-External
    HHE = "HHE"  # Heterogeneous-Heterogeneous-External
