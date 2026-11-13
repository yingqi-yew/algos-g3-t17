# IS115 Project README: Last-Mile Delivery Planning

**Team G3-T17:** SUH Sumin, YEW Ying Qi, Tejas S/O ILANGKUMARAN

We compare three dispatch policies against the supplied FIFO baseline. 

Our metric is the **on-time delivery rate**: parcels delivered within their delivery window, divided by all parcels that arrived that day.

## Requirements

- Python 3.9 or later

Run every command from the **project root**, the folder that contains `simulator/`, `data/` and `solution/`.

On Windows, use `python` (or `py`) in place of `python3`.

## Folder structure

```
project/
├── simulator/                      # supplied simulator (unchanged)
├── data/                           # input data (unchanged)
├── solution/
│   ├── performance_monitor.py      # our metric: calculate_metrics()
│   ├── policies/
│   │   ├── baseline.py             # supplied FIFO policy (unchanged)
│   │   ├── helpers.py              # shared helper functions
│   │   ├── edf.py                  # window-aware Earliest Deadline First
│   │   ├── window_nn.py            # window-aware nearest neighbour
│   │   └── window_nn_2opt.py       # window-aware nearest neighbour + 2-opt
│   └── summarise_results/
│       ├── overall_results.py      # combines metrics.json into one results table
│       └── run_profile.py          # operation counts vs Big-O prediction
├── results/                        # generated outputs (see below)
└── README.md
```

## Policies

| Module | Policy | Idea |
|---|---|---|
| `solution.policies.baseline` | FIFO (supplied) | Parcels in arrival order; ignores delivery windows |
| `solution.policies.edf` | Window-aware EDF | Sort by window end, scan once, add parcels that arrive on time |
| `solution.policies.window_nn` | Window-aware nearest neighbour | Repeatedly add the closest parcel that arrives on time |
| `solution.policies.window_nn_2opt` | Nearest neighbour + 2-opt | Build with nearest neighbour, then shorten the route with up to three 2-opt moves |

`helpers.py` holds the shared waiting-list filter and feasibility check (capacity, range, 18:00 return and delivery window). All three policies are therefore judged by the same rules.

## Performance metric

`solution/performance_monitor.py` reads one day's `log.txt` and writes `metrics.json` next to it.

| Field | Meaning |
|---|---|
| `on_time_rate` | **Main metric.** On-time parcels ÷ all parcels in the day's file |
| `on_time_parcels` | Delivered with window start ≤ delivery time ≤ window end |
| `total_parcels` | All parcels in the day's file |
| `delivered_parcels`, `early_parcels`, `late_parcels`, `undelivered_parcels` | Delivery breakdown |
| `km_driven`, `km_per_delivered_parcel` | Distance driven: hub → stops → hub, for every trip |

## Reproducing the results

### 1. Run one policy on one day

Run the simulator, then the performance monitor on its log:

```bash
python3 -m simulator --policy solution.policies.baseline --data data --day day_001 --output results/baseline/day_001
python3 -m solution.performance_monitor --data data --day day_001 --log results/baseline/day_001/log.txt
```

To run another policy, change `baseline` in both the `--policy` module and the folder name, for example to `solution.policies.window_nn` with `results/window_nn/day_001`.

### 2. Run all policies on all 20 days

**macOS / Linux:**

```bash
for pol in baseline edf window_nn window_nn_2opt; do
  for d in $(seq -f "day_%03g" 1 20); do
    python3 -m simulator --policy solution.policies.$pol --data data --day $d --output results/$pol/$d
    python3 -m solution.performance_monitor --data data --day $d --log results/$pol/$d/log.txt
  done
done
```

**Windows (PowerShell):**

```powershell
foreach ($pol in "baseline","edf","window_nn","window_nn_2opt") {
  foreach ($i in 1..20) {
    $d = "day_{0:D3}" -f $i
    python -m simulator --policy solution.policies.$pol --data data --day $d --output results/$pol/$d
    python -m solution.performance_monitor --data data --day $d --log results/$pol/$d/log.txt
  }
}
```

This creates `results/<policy>/day_XXX/log.txt` and `metrics.json` for all four policies.

### 3. Summarise the results

Run this after step 2. It reads every `metrics.json` and prints the overall table for all 20 days:

```bash
python3 -m solution.summarise_results.overall_results
```

Output is saved to `results/summary.txt`.

### 4. Empirical validation (operation counts vs Big-O)

```bash
python3 -m solution.summarise_results.run_profile
```

This runs each policy on all 20 days and counts its basic operations:
- each feasibility check, where one parcel is checked against capacity, range, the return cutoff and its window;
- each 2-opt stop re-check.

It compares these counts with the Big-O prediction for every `dispatch` call. The counts are the same on every run and every machine. Output is saved to `results/profiling/summary.txt`, and the simulation logs from this run go to `results/profiling/logs/`. It does not modify the policies or `data/`.

## Expected results

`overall_results` (20 days, 15,867 parcels):

| Policy | On-time | Delivered | Late | Undelivered | On-time rate | Km per delivered parcel |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 4,349 | 6,421 | 2,072 | 9,446 | 27.41% | 16.21 |
| edf | 6,296 | 6,296 | 0 | 9,571 | 39.68% | 16.48 |
| window_nn | 13,064 | 13,064 | 0 | 2,803 | 82.33% | 5.96 |
| window_nn_2opt | 13,117 | 13,117 | 0 | 2,750 | 82.67% | 5.86 |

`run_profile`:

| Policy | Predicted cost | Calls | Measured operations | Predicted operations | r |
|---|---|---:|---:|---:|---:|
| edf | O(P + N log N) | 620 | 118,408 | 118,408 | 1.00 |
| window_nn | O(P + NK) | 2,330 | 2,064,314 | 2,265,296 | 1.00 |
| window_nn_2opt | O(P + NK + K³) | 2,420 | 8,720,215 | 14,431,760 | 0.95 |

All policies are deterministic, so rerunning the commands gives exactly these numbers.
