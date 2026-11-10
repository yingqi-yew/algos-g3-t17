"""Add up every policy's metrics.json files into one results table.

Run from the project root, after the simulator and performance monitor:
    python3 -m solution.summarise_results.overall_results
"""

import json
import statistics

POLICIES = ["baseline", "edf", "window_nn", "window_nn_2opt"]

lines = ["Policy            On-time Delivered   Late Undelivered On-time rate"
         "       Daily range  Std dev Km per parcel"]
on_time_by_policy = {}   # on-time parcels per day, used for the 2-opt comparison

for policy in POLICIES:
    total = 0
    on_time = 0
    delivered = 0
    late = 0
    undelivered = 0
    km = 0
    daily_rates = []
    daily_on_time = []

    for i in range(1, 21):
        day = "day_%03d" % i
        with open("results/" + policy + "/" + day + "/metrics.json") as f:
            m = json.load(f)

        total = total + m["total_parcels"]
        on_time = on_time + m["on_time_parcels"]
        delivered = delivered + m["delivered_parcels"]
        late = late + m["late_parcels"]
        undelivered = undelivered + m["undelivered_parcels"]
        km = km + m["km_driven"]
        daily_rates.append(m["on_time_parcels"] / m["total_parcels"] * 100)
        daily_on_time.append(m["on_time_parcels"])

    on_time_by_policy[policy] = daily_on_time

    rate = on_time / total * 100
    lines.append("%-16s %8d %9d %6d %11d %11.2f%% %7.2f%% - %5.2f%% %8.2f %13.2f" % (
        policy, on_time, delivered, late, undelivered, rate,
        min(daily_rates), max(daily_rates), statistics.stdev(daily_rates), km / delivered))

# Compare 2-opt with plain nearest neighbour, day by day.
better = 0
worse = 0
same = 0
for nn, two_opt in zip(on_time_by_policy["window_nn"], on_time_by_policy["window_nn_2opt"]):
    if two_opt > nn:
        better = better + 1
    elif two_opt < nn:
        worse = worse + 1
    else:
        same = same + 1
net = sum(on_time_by_policy["window_nn_2opt"]) - sum(on_time_by_policy["window_nn"])

lines.append("")
lines.append("Total parcels (20 days): %d" % total)
lines.append("2-opt vs NN: better on %d days, worse on %d, same on %d, net %+d parcels"
             % (better, worse, same, net))

summary = "\n".join(lines)
print(summary)
with open("results/summary.txt", "w") as f:
    f.write(summary + "\n")
