# SRRS — Self-Replicating Robot System

Simulation and Reliability, Availability, Maintainability (RAM) analysis of self-replicating robotic systems across 6 configurations.

![CI](https://github.com/vishalgattani/srrs/actions/workflows/ci.yml/badge.svg)
![Coverage](https://img.shields.io/badge/coverage-70%25-yellow)

---

## Overview

SRRS models robot colonies that can collect materials, print components, and assemble new robots. Six configurations are studied, varying replication strategy (Homogeneous vs Heterogeneous) and robot mix (One type vs External specialists):

| Config | Description |
|--------|-------------|
| CHO | Collect-Homogeneous-One — single replicator builds Normal workers |
| DHO | Deterministic-Homogeneous-One — replicator clones itself |
| HHO | Heterogeneous-Homogeneous-One — replicator alternates Normal/Replicator |
| CHE | Collect-Heterogeneous-External — Assembler + Printer team builds Normal workers |
| DHE | Deterministic-Heterogeneous-External — Assembler + Printer alternate clones |
| HHE | Heterogeneous-Heterogeneous-External — rotating 3-type build cycle |

---

## Package Structure

```
python/
├── models/
│   ├── types.py        ← RobotType, TaskType, Config, SimMode enums
│   ├── robot.py        ← Robot base class + Replicator/Normal/Assembler/Printer
│   └── resources.py    ← Simulation resource state (materials, env_materials, …)
├── simulation/
│   ├── config.py       ← SimulationParams (all tunable parameters)
│   └── runner.py       ← Core simulation loop (deterministic + MC)
├── analysis/
│   ├── ram.py          ← System-level MTBF / MTTR / MDT / Aoss
│   └── stats.py        ← MC aggregation + confidence intervals
├── visualization/
│   └── plots.py        ← Plotly HTML output (6-panel summary + MC distributions)
└── main.py             ← CLI entrypoint
```

---

## Installation

```bash
# From source
pip install -e ".[dev]"

# From built wheel
pip install dist/srrs-*.whl
```

---

## Usage

### CLI

```bash
# Deterministic — single config, 100 timesteps
python -m python.main --config CHO --mode D --timesteps 100

# Deterministic — with Plotly HTML output
python -m python.main --config CHO --mode D --timesteps 250 --plot --output-dir output/

# Monte Carlo — 6 configs, 500 runs each
python -m python.main --config CHO DHO HHO CHE DHE HHE --mode MC --mc-runs 500 --timesteps 250 --plot

# All options
python -m python.main --help
```

### Python API

```python
from python.models.types import Config, SimMode
from python.models.resources import Resources
from python.simulation.config import SimulationParams
from python.simulation.runner import run_simulation

params = SimulationParams(
    config=Config.CHO,
    mode=SimMode.DETERMINISTIC,
    timesteps=100,
    quality_threshold=0.5,
    risk_threshold=3.0,
)

df, ram = run_simulation(params)
print(f"Final robots: {df['#In'].iloc[-1]}")
print(f"System Aoss: {ram.aoss:.4f}")
```

---

## Testing

```bash
# Run all tests
pytest

# Run tests for a specific config with coverage
pytest tests/test_CHO.py -v --cov=python --cov-report=term-missing

# Run all configs
pytest tests/ -v --cov=python --cov-report=term-missing
```

---

## CI

GitHub Actions runs on every push and PR:

1. **build** — installs `build`, runs `python -m build --wheel`, uploads the `.whl` as an artifact
2. **test / CHO … HHE** — 6 parallel jobs, each downloads the wheel, installs it, and runs `pytest tests/test_<CONFIG>.py` with coverage

---

## RAM Metrics

| Metric | Description |
|--------|-------------|
| MTBF | Mean Time Between Failures |
| MTTR | Mean Time To Repair |
| MDT | Mean Down Time |
| Aoss | Operational Steady-State Availability |

---

## Dependencies

```
numpy
pandas
plotly
pydantic>=2.0
python-dotenv
```

Dev: `pytest`, `pytest-cov`
