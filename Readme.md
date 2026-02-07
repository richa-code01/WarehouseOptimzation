# Distributed Warehouse Picking Optimization Engine

A scalable optimization system that solves the warehouse picking problem using the Apparent Tardiness Cost (ATC) heuristic. The engine prioritizes orders by combining pick density and urgency, then schedules picklists against shift capacity and delivery cutoffs.

## Key Features

- ATC-based prioritization with deadline-aware scoring
- Zone-based partitioning to enable parallel execution
- Constraint satisfaction for weight, item limits, and cutoff windows
- Shift-aware scheduling with picklist splitting and utilization metrics

## Tech Stack

- Python 3.x
- Pandas, NumPy
- Multiprocessing for zone-level parallelization

## High-Scale Architecture Concept

The engine is structured to scale horizontally by partitioning warehouse zones into independent tasks. This model supports parallel execution across cores or distributed workers, with centralized scheduling for shift capacity and deadline adherence.

## Complexity Summary

| Component | Time Complexity | Space Complexity |
|-----------|-----------------|------------------|
| Scoring (ATC) | O(1) | O(1) |
| Picklist Generation | O(Z * N log N) | O(N) |
| Parallel Engine | O(max(N_zone) log N) | O(N) |

## Project Structure

```
├── main.py                     # Entry point
├── optimization_problem/
│   ├── parallel_engine.py      # Parallel zone processing
│   ├── config.py               # Configuration (shifts, constraints, cutoffs)
│   ├── core_logic.py           # ATC scoring and duration estimation
│   ├── data_loader.py          # CSV loading and preprocessing
│   ├── picklist_builder.py     # Picklist generation algorithm
│   ├── scheduler.py            # Picker assignment and scheduling
│   └── utils.py                # Output generation and metrics
├── requirements.txt
└── Dockerfile
```

## Installation

```bash
pip install -r requirements.txt
```

## Usage

1. Place your dataset as input.csv in the project root
2. Run the engine:

```bash
python main.py
```

3. Results are saved to the output/ directory
