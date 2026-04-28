"""
plots.py — Matplotlib-based visualisation (6-panel summary + MC distributions).

Author: Vishal Gattani <vishalgattani09@gmail.com>
Created: 2026-04-13
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # non-interactive backend — safe for headless/CI
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd


_TASK_SERIES = [
    ("#Printing", "Printing"),
    ("#Assembling", "Assembling"),
    ("#Collecting", "Collecting"),
    ("#Idle", "Idle"),
    ("#Repair", "Repair"),
]

_SERVICE_SERIES = [
    ("#In", "In Service"),
    ("#Out", "Out of Service"),
]

_TYPE_SERIES = [
    ("#Replicator", "Replicator"),
    ("#Normal", "Normal"),
    ("#Assembler", "Assembler"),
    ("#Printer", "Printer"),
]

_RESOURCE_SERIES = [
    ("NonPr", "NonPr"),
    ("Printable", "Printable"),
    ("Materials", "Materials"),
    ("Env_Materials", "Env Materials"),
]

_QUALITY_SERIES = [
    ("Average Build Quality in-service", "In Service"),
    ("Average Build Quality of System", "System"),
]


def plot_simulation(config: str, df: pd.DataFrame, ram: dict, out_path: Path) -> None:
    """
    Generate a 6-panel simulation summary figure and save as PNG.

    Panels:
      1. Robot Tasks vs Time
      2. Robots In/Out of Service
      3. Robot Types vs Time
      4. Resources vs Time
      5. Average Build Quality vs Time
      6. RAM Metrics (table)

    Args:
        config: Configuration name (e.g. "CHO").
        df: Per-timestep simulation DataFrame.
        ram: Dict with keys mtbf, mttr, mdt, aoss.
        out_path: Path to write the PNG file.
    """
    fig, axes = plt.subplots(3, 2, figsize=(14, 12))
    fig.suptitle(f"SRRS Simulation — {config}", fontsize=14, fontweight="bold")

    t = df["Time"]

    # Panel 1 — tasks
    ax = axes[0, 0]
    for col, name in _TASK_SERIES:
        ax.plot(t, df[col], label=name)
    ax.set_title("Robot Tasks vs Time")
    ax.set_xlabel("Time")
    ax.set_ylabel("Count")
    ax.legend(fontsize=8)
    ax.xaxis.set_major_locator(ticker.AutoLocator())

    # Panel 2 — in/out service
    ax = axes[0, 1]
    for col, name in _SERVICE_SERIES:
        ax.plot(t, df[col], label=name)
    ax.set_title("Robots In/Out of Service")
    ax.set_xlabel("Time")
    ax.set_ylabel("Count")
    ax.legend(fontsize=8)

    # Panel 3 — robot types
    ax = axes[1, 0]
    for col, name in _TYPE_SERIES:
        ax.plot(t, df[col], label=name)
    ax.set_title("Robot Types vs Time")
    ax.set_xlabel("Time")
    ax.set_ylabel("Count")
    ax.legend(fontsize=8)

    # Panel 4 — resources
    ax = axes[1, 1]
    for col, name in _RESOURCE_SERIES:
        ax.plot(t, df[col], label=name)
    ax.set_title("Resources vs Time")
    ax.set_xlabel("Time")
    ax.set_ylabel("Amount")
    ax.legend(fontsize=8)

    # Panel 5 — build quality
    ax = axes[2, 0]
    for col, name in _QUALITY_SERIES:
        ax.plot(t, df[col], label=name)
    ax.set_title("Average Build Quality vs Time")
    ax.set_xlabel("Time")
    ax.set_ylabel("Quality")
    ax.set_ylim(0.0, 1.0)
    ax.legend(fontsize=8)

    # Panel 6 — RAM metrics table
    ax = axes[2, 1]
    ax.axis("off")
    metrics = ["mtbf", "mttr", "mdt", "aoss"]
    labels = ["MTBF", "MTTR", "MDT", "Aoss"]
    values = [f"{ram.get(m, float('nan')):.4f}" for m in metrics]
    table = ax.table(
        cellText=[[l, v] for l, v in zip(labels, values)],
        colLabels=["Metric", "Value"],
        loc="center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.8)
    ax.set_title("RAM Metrics")

    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_mc_distributions(config: str, df: pd.DataFrame, out_path: Path) -> None:
    """Plot histograms of key MC metrics as a 6-panel PNG."""
    metrics = [
        "MTBF", "MTTR", "MDT", "Aoss",
        "Average Build Quality in-service",
        "Average Build Quality of System",
    ]
    available = [m for m in metrics if m in df.columns]

    fig, axes = plt.subplots(3, 2, figsize=(14, 12))
    fig.suptitle(f"MC Distributions — {config}", fontsize=14, fontweight="bold")

    for i, (ax, metric) in enumerate(zip(axes.flat, available)):
        data = df[metric].dropna()
        ax.hist(data, bins=30, edgecolor="black", alpha=0.7)
        ax.set_title(metric, fontsize=9)
        ax.set_xlabel("Value")
        ax.set_ylabel("Frequency")
        mean = data.mean()
        ax.axvline(mean, color="red", linestyle="--", linewidth=1, label=f"μ={mean:.3f}")
        ax.legend(fontsize=7)

    # hide any unused panels
    for ax in axes.flat[len(available):]:
        ax.axis("off")

    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
