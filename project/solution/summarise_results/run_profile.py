"""Op counts per dispatch call vs predicted Big-O.
1 op = one check_parcel call, or one stop in evaluate_route (2-opt)."""

import math

import solution.policies.helpers as helpers
from simulator.loaders import day_input_paths
from simulator.simulator import Simulator
from solution.policies import edf, window_nn, window_nn_2opt

POLICIES = {
    "edf": edf.dispatch,
    "window_nn": window_nn.dispatch,
    "window_nn_2opt": window_nn_2opt.dispatch,
}

PREDICTED_COST = {
    "edf": "O(P + N log N)",
    "window_nn": "O(P + NK)",
    "window_nn_2opt": "O(P + NK + K^3)",
}

operations = 0   # operations counted during the current dispatch call


# wrap the real helpers so each parcel check / stop re-check adds 1 to the counter

real_check_parcel = helpers.check_parcel
real_evaluate_route = helpers.evaluate_route


def counting_check_parcel(record, location, load, travelled, departure, context):
    global operations
    operations = operations + 1
    return real_check_parcel(record, location, load, travelled, departure, context)


def counting_evaluate_route(route, parcel, context):
    global operations
    operations = operations + len(route)
    return real_evaluate_route(route, parcel, context)


# Make the policies use the counting versions.
helpers.check_parcel = counting_check_parcel
edf.check_parcel = counting_check_parcel
window_nn_2opt.evaluate_route = counting_evaluate_route


def predicted_operations(name, N, K):
    """Predicted number of counted operations for one call."""
    if name == "edf":
        return N                       # one scan of the sorted list
    if name == "window_nn":
        return N * (K + 1)             # K + 1 passes over up to N parcels
    return N * (K + 1) + K ** 3        # NN passes, plus 2-opt's K^3


def correlation(xs, ys):
    """Pearson r."""
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    top = 0
    sum_x = 0
    sum_y = 0
    for x, y in zip(xs, ys):
        top = top + (x - mean_x) * (y - mean_y)
        sum_x = sum_x + (x - mean_x) ** 2
        sum_y = sum_y + (y - mean_y) ** 2
    return top / math.sqrt(sum_x * sum_y)


current_policy = None
records = []   # one (N, K, operations) entry per dispatch call


def counted_dispatch(parcel, context):
    """Run the real policy and record how many operations it used."""
    global operations
    N = 0
    for p in parcel.values():
        if p["vehicle_assigned"] is None and p["delivery_time"] is None:
            N = N + 1

    operations = 0
    route = current_policy(parcel, context)
    records.append((N, len(route), operations))
    return route


lines = ["Policy           Predicted cost     Calls   Measured ops   Predicted ops      r"]

for name in POLICIES:
    current_policy = POLICIES[name]
    records = []

    for i in range(1, 21):
        day = "day_%03d" % i
        parcels_csv, dist_csv, config_json = day_input_paths("data", day)
        sim = Simulator(parcels_csv, dist_csv, config_json, dispatch_policy=counted_dispatch)
        sim.run("results/profiling/logs/" + name + "/" + day + "/log.txt")

    measured = [r[2] for r in records]
    predicted = [predicted_operations(name, r[0], r[1]) for r in records]

    lines.append("%-16s %-16s %7d %14d %15d %6.2f" % (
        name, PREDICTED_COST[name], len(records),
        sum(measured), sum(predicted), correlation(predicted, measured)))

summary = "\n".join(lines)
print(summary)
with open("results/profiling/summary.txt", "w") as f:
    f.write(summary + "\n")