"""Window-aware nearest neighbour + 2-opt.

Build a route with window-aware nearest neighbour, then apply first-improvement
2-opt (reverse the stops between positions i and j) to shorten it. A reversal is
kept only if every parcel still arrives inside its window and the trip stays
within range and the 18:00 return. At most three improving moves are accepted.
"""

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

                # NN only adds on-time parcels, so 2-opt keeps every parcel
                # on time and accepts a reversal only if it shortens the trip.
                # Adding the same distances in a different order can differ by a
                # rounding error, so a route only counts as shorter by a real margin.
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