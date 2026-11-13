"""NN route, then first-improvement 2-opt (max 3 moves). Reversals must keep all parcels on time."""

from typing import Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies.helpers import (
    evaluate_route,
    nearest_neighbour_route,
    within_trip_limits,
)


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    route = nearest_neighbour_route(parcel, context)
    _, distance = evaluate_route(route, parcel, context)

    departure = context["current_time"] + context["departure_delay"]

    # Accept at most three improving moves.
    for _ in range(3):
        improved = False

        for i in range(len(route) - 1):
            for j in range(i + 1, len(route)):
                candidate = (
                    route[:i] + route[i:j + 1][::-1] + route[j + 1:]
                )

                all_on_time, new_distance = evaluate_route(
                    candidate, parcel, context
                )

                if not within_trip_limits(new_distance, departure, context):
                    continue

                # small tolerance for float rounding when summing in a different order
                shorter = new_distance < distance - 1e-8

                if all_on_time and shorter:
                    route = candidate
                    distance = new_distance
                    improved = True
                    break

            if improved:
                break

        if not improved:
            break

    return route