"""EDF policy: go through waiting parcels by window end, take the ones that pass check_parcel."""

from typing import Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies.helpers import HUB, check_parcel, get_waiting


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    departure = context["current_time"] + context["departure_delay"]

    waiting = get_waiting(parcel)

    # Earliest window end first; arrival time and parcel ID break ties.
    waiting.sort(
        key=lambda parcel_id: (
            parcel[parcel_id]["delivery_window_end"],
            parcel[parcel_id]["arrival_time"],
            parcel_id,
        )
    )

    route = []
    load = 0.0
    # km from the hub to the route's last stop, not counting the return leg.
    travelled = 0.0
    location = HUB

    for parcel_id in waiting:
        record = parcel[parcel_id]
        feasible, leg = check_parcel(record, location, load, travelled, departure, context)
        if not feasible:
            continue

        route.append(parcel_id)
        load = load + record["size"]
        travelled = travelled + leg
        location = record["delivery_location_id"]

    return route