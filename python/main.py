"""
main.py — CLI entrypoint for SRRS simulation.

Author: Vishal Gattani <vishalgattani09@gmail.com>
Created: 2026-04-13

Usage:
    python -m python.main --config CHO --mode D --timesteps 100
    python -m python.main --config CHO CHE --mode MC --mc-runs 100 --timesteps 250
    python -m python.main --config CHO --mode D --timesteps 100 --plot
"""

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

from python.models.types import Config, SimMode
from python.models.resources import Resources
from python.simulation.config import SimulationParams
from python.simulation.runner import run_simulation
from python.analysis.stats import aggregate_mc_results, compute_confidence_intervals, describe_results
from python.visualization.plots import plot_simulation, plot_mc_distributions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Self-Replicating Robot System Simulation")
    parser.add_argument(
        "--config", nargs="+", choices=[c.value for c in Config],
        default=["CHO"], help="Robot system configuration(s)"
    )
    parser.add_argument(
        "--mode", choices=["D", "MC"], default="D",
        help="D = Deterministic, MC = Monte Carlo"
    )
    parser.add_argument("--timesteps", type=int, default=100, help="Simulation timesteps")
    parser.add_argument("--mc-runs", type=int, default=500, help="Number of MC iterations")
    parser.add_argument("--quality-threshold", type=float, default=0.5, help="Robot quality threshold")
    parser.add_argument("--risk-threshold", type=float, default=3.0, help="Risk threshold")
    parser.add_argument("--tasks-before-fail", type=int, default=5, help="Tasks before failure (deterministic)")
    parser.add_argument("--plot", action="store_true", help="Generate Plotly HTML output")
    parser.add_argument("--output-dir", type=Path, default=Path("output"), help="Output directory")
    return parser.parse_args()


def run_deterministic(config: Config, params: SimulationParams, args: argparse.Namespace) -> dict:
    print(f"  Deterministic {config.value}, t={params.timesteps}, risk={params.risk_threshold}, tasks={params.num_tasks_before_fail}")
    start = time.time()
    df, ram = run_simulation(params)
    elapsed = (time.time() - start) * 1000

    print(f"  → Done in {elapsed:.1f}ms | MTBF={ram.mtbf:.3f} Aoss={ram.aoss:.4f}")

    if args.plot:
        out = args.output_dir / "Deterministic" / config.value / f"sim_{config.value}.html"
        plot_simulation(config.value, df, ram._asdict(), out)
        print(f"  → Plot: {out}")

    last = df.tail(1).to_dict("records")[0]
    last.update({"Configuration": config.value, "MTBF": ram.mtbf, "MTTR": ram.mttr, "MDT": ram.mdt, "Aoss": ram.aoss})
    return last


def run_mc(config: Config, params: SimulationParams, args: argparse.Namespace) -> dict:
    print(f"  MC {config.value}, t={params.timesteps}, runs={params.mc_runs}, risk={params.risk_threshold}")
    mc_rows = []
    start = time.time()

    for i in range(1, params.mc_runs + 1):
        sys.stdout.write(f"\r    Run {i}/{params.mc_runs}")
        sys.stdout.flush()
        df, ram = run_simulation(params)
        if not (ram.aoss != ram.aoss):  # skip NaN aoss
            row = df.tail(1).to_dict("records")[0]
            row.update({"MTBF": ram.mtbf, "MTTR": ram.mttr, "MDT": ram.mdt, "Aoss": ram.aoss})
            mc_rows.append(row)

    print()
    elapsed = (time.time() - start) * 1000
    mc_df = aggregate_mc_results(mc_rows)
    stats = describe_results(mc_df)
    ci = compute_confidence_intervals(mc_df, len(mc_rows))

    print(f"  → Done in {elapsed:.1f}ms | Valid runs: {len(mc_rows)}")
    print(f"  → Mean Aoss={mc_df['Aoss'].mean():.4f} ± {mc_df['Aoss'].std():.4f}")

    if args.plot:
        out = args.output_dir / "MC" / config.value / f"mc_{config.value}.html"
        plot_mc_distributions(config.value, mc_df, out)
        print(f"  → Plot: {out}")

    return stats.to_dict()


def main() -> None:
    args = parse_args()

    print(f"\n{'='*60}")
    print(f"SRRS Simulation  |  mode={args.mode}  |  configs={args.config}")
    print(f"{'='*60}\n")

    for cfg_str in args.config:
        config = Config(cfg_str)
        params = SimulationParams(
            config=config,
            mode=SimMode(args.mode),
            timesteps=args.timesteps,
            mc_runs=args.mc_runs,
            quality_threshold=args.quality_threshold,
            risk_threshold=args.risk_threshold,
            num_tasks_before_fail=args.tasks_before_fail,
        )

        if args.mode == "D":
            run_deterministic(config, params, args)
        else:
            run_mc(config, params, args)

    print("\nDone.")


if __name__ == "__main__":
    main()
