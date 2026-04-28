"""
resources.py — Global simulation resource state as a mutable Pydantic model.

Author: Vishal Gattani <vishalgattani09@gmail.com>
Created: 2026-04-13
"""

from pydantic import BaseModel, Field


class Resources(BaseModel):
    """Tracks all shared material quantities during a simulation run."""

    non_printable: float = 300.0    # NonPr
    printable: float = 100.0        # Printable
    materials: float = 50.0         # Raw materials
    env_materials: float = 500.0    # Environment materials

    # Exhaust timestamps (0 = not exhausted yet)
    env_exhaust_time: int = 0
    print_exhaust_time: int = 0
    non_pr_exhaust_time: int = 0
    mat_exhaust_time: int = 0

    def collect(self, amount: float = 1.0) -> None:
        self.materials += amount
        self.env_materials -= amount

    def print_material(self, efficiency: float = 1.0, amount: float = 1.0) -> None:
        self.materials -= efficiency * amount
        self.printable += efficiency * amount

    def can_collect(self, amount: float = 1.0) -> bool:
        return self.env_materials - amount >= 0

    def can_print(self, efficiency: float = 1.0, amount: float = 1.0) -> bool:
        return self.materials - (efficiency * amount) > 0

    def can_assemble(self, cost_pr: float, cost_non_pr: float) -> bool:
        return self.printable - cost_pr >= 0 and self.non_printable - cost_non_pr >= 0

    def consume_assembly(self, cost_pr: float, cost_non_pr: float) -> None:
        self.printable -= cost_pr
        self.non_printable -= cost_non_pr

    def update_exhaust_times(self, t: int) -> None:
        if self.env_materials == 0 and self.env_exhaust_time == 0:
            self.env_exhaust_time = t
        if self.printable <= 0 and self.print_exhaust_time == 0:
            self.print_exhaust_time = t
        if self.non_printable <= 1 and self.non_pr_exhaust_time == 0:
            self.non_pr_exhaust_time = t
        if self.materials <= 1 and self.mat_exhaust_time == 0:
            self.mat_exhaust_time = t
