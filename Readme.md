# Warehouse Picking Optimization Engine

An intelligent warehouse order picking optimization system that uses the **Apparent Tardiness Cost (ATC)** scheduling algorithm to maximize units picked before delivery cutoffs.

## Problem Statement

In a warehouse fulfillment center, orders arrive with different priority levels and delivery cutoffs. The challenge is to:
- Generate optimal picklists that respect weight and item count constraints
- Assign picklists to pickers across multiple shifts
- Maximize the number of units picked before their respective cutoff times
- Handle fragile items with special weight constraints

## Features

- **ATC-Based Prioritization**: Uses pick density and urgency scoring to prioritize items
- **Zone-Aware Picking**: Groups items by zone with special handling for fragile zones
- **Multi-Shift Scheduling**: Supports Night, Morning, and General shifts with configurable picker counts
- **Constraint Handling**: Respects max weight (200kg standard, 50kg fragile), max items per picklist (2000)
- **Picklist Splitting**: Automatically splits picklists when shifts end
- **Performance Metrics**: Reports units picked, order completion rates, and picker utilization

## Project Structure

```
├── main.py                     # Entry point
├── swiggy_problem/
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
# Clone the repository
git clone https://github.com/<username>/warehouse-optimization.git
cd warehouse-optimization

# Install dependencies
pip install -r requirements.txt
```

## Usage

1. Place your order dataset as `input.csv` in the project root
2. Run the optimization engine:

```bash
python main.py
```

3. Results are saved to the `output/` directory:
   - `output/Summary.csv` - Picklist summary with types and stores
   - `output/picklists/` - Individual picklist detail files

## Input Format

The input CSV should contain:
- `order_id` - Unique order identifier
- `sku` - Product SKU
- `store_id` - Destination store
- `order_qty` - Quantity to pick
- `weight_in_grams` - Item weight
- `zone` - Warehouse zone
- `bin_rank` - Bin location ranking
- `pod_priority` - Priority level (P1-P9)
- `dt` - Order timestamp
- `pods_per_picklist_in_that_zone` - Zone capacity

## Configuration

Key parameters in `swiggy_problem/config.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `MAX_ITEMS_PER_PICKLIST` | 2000 | Maximum items per picklist |
| `MAX_WEIGHT_STD` | 200kg | Weight limit for standard zones |
| `MAX_WEIGHT_FRAGILE` | 50kg | Weight limit for fragile zones |
| `ATC_K` | 2.0 | ATC lookahead factor |

## Algorithm Overview

1. **Data Loading**: Parse orders and calculate absolute cutoff times
2. **Picklist Building**: 
   - Partition items by zone
   - Score items using ATC (urgency × pick density)
   - Build picklists respecting constraints
3. **Scheduling**:
   - Create picker pool across all shifts
   - Assign picklists using earliest-available picker
   - Split picklists if they exceed shift boundaries
4. **Output**: Generate summary and detailed picklist files

## Docker Support

```bash
docker build -t warehouse-opt .
docker run -v $(pwd)/input.csv:/app/input.csv warehouse-opt
```

## License

MIT