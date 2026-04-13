"""
plots.py — Plotly-based visualisation (replaces chart_studio).

Author: Vishal Gattani <vishalgattani09@gmail.com>
Created: 2026-04-13
"""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def plot_simulation(config: str, df: pd.DataFrame, ram: dict, out_path: Path) -> None:
    """
    Generate a 6-panel simulation summary figure and save as HTML.

    Args:
        config: Configuration name (e.g. "CHO").
        df: Per-timestep simulation DataFrame.
        ram: Dict with keys MTBF, MTTR, MDT, Aoss.
        out_path: Path to write the HTML file.
    """
    fig = make_subplots(
        rows=3,
        cols=2,
        subplot_titles=(
            "Robot Tasks vs Time",
            "Robots In/Out of Service",
            "Robot Types vs Time",
            "Resources vs Time",
            "Average Build Quality vs Time",
            "RAM Metrics",
        ),
    )

    t = df["Time"]

    # Panel 1 — tasks
    for col, name in [
        ("#Printing", "Printing"),
        ("#Assembling", "Assembling"),
        ("#Collecting", "Collecting"),
        ("#Idle", "Idle"),
        ("#Repair", "Repair"),
    ]:
        fig.add_trace(go.Scatter(x=t, y=df[col], name=name, mode="lines"), row=1, col=1)

    # Panel 2 — in/out service
    for col, name in [("#In", "In Service"), ("#Out", "Out of Service")]:
        fig.add_trace(go.Scatter(x=t, y=df[col], name=name, mode="lines"), row=1, col=2)

    # Panel 3 — robot types
    for col, name in [
        ("#Replicator", "Replicator"),
        ("#Normal", "Normal"),
        ("#Assembler", "Assembler"),
        ("#Printer", "Printer"),
    ]:
        fig.add_trace(go.Scatter(x=t, y=df[col], name=name, mode="lines"), row=2, col=1)

    # Panel 4 — resources
    for col, name in [
        ("NonPr", "NonPr"),
        ("Printable", "Printable"),
        ("Materials", "Materials"),
        ("Env_Materials", "Env Materials"),
    ]:
        fig.add_trace(go.Scatter(x=t, y=df[col], name=name, mode="lines"), row=2, col=2)

    # Panel 5 — build quality
    for col, name in [
        ("Average Build Quality in-service", "In Service"),
        ("Average Build Quality of System", "System"),
    ]:
        fig.add_trace(go.Scatter(x=t, y=df[col], name=name, mode="lines"), row=3, col=1)

    # Panel 6 — RAM table
    ram_table = go.Table(
        header={"values": ["Metric", "Value"]},
        cells={
            "values": [
                list(ram.keys()),
                [f"{v:.4f}" if isinstance(v, float) else str(v) for v in ram.values()],
            ]
        },
    )
    fig.add_trace(ram_table, row=3, col=2)

    fig.update_layout(title_text=f"SRRS Simulation — {config}", height=900, showlegend=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(out_path))


def plot_mc_distributions(config: str, df: pd.DataFrame, out_path: Path) -> None:
    """Plot histograms of key MC metrics."""
    metrics = ["MTBF", "MTTR", "MDT", "Aoss", "Average Build Quality in-service", "Average Build Quality of System"]
    available = [m for m in metrics if m in df.columns]

    fig = make_subplots(rows=3, cols=2, subplot_titles=available)
    for i, metric in enumerate(available):
        row, col = divmod(i, 2)
        fig.add_trace(go.Histogram(x=df[metric].dropna(), name=metric), row=row + 1, col=col + 1)

    fig.update_layout(title_text=f"MC Distributions — {config}", height=900, showlegend=False)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(out_path))
