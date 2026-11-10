"""
Shared helper functions for the dispatch policies.

1. all 3 policies use the same waiting-list filter -> get_waiting(parcel)
2. all 3 policies use the same departure time and distance budget -> within_trip_limits(...)
3. EDF + NN use the same capacity + range/return + window check for one parcel -> check_parcel(...)
4. both NN policies use the same route builder -> nearest_neighbour_route(parcel,context)
5. both NN policies use the same arrival and round-trip calc, applied to a full route -> evaluate_route(...)

"""

from typing import Dict, List, Tuple

from simulator.models import Parcel, SimulationContext

HUB = "HUB"


def get_waiting(parcel: Dict[str, Parcel]) -> List[str]:
    """Return the IDs of parcels with no vehicle assigned and no delivery time."""
    waiting = []
    for parcel_id in parcel:
        record = parcel[parcel_id]
        if record["vehicle_assigned"] is None and record["delivery_time"] is None:
            waiting.append(parcel_id)
    return waiting


def within_trip_limits(round_trip: float, departure: float, context: SimulationContext) -> bool:
    """Check range and return cutoff for a trip of round_trip km, including the return leg.

    At 60 km/h, km also equals travel time in minutes.
    """
    if round_trip > context["max_trip_distance_km"]:
        return False
    if departure + round_trip > context["return_cutoff"]:
        return False
    return True


def check_parcel(
    record: Parcel,
    location: str,
    load: float,
    travelled: float,
    departure: float,
    context: SimulationContext,
) -> Tuple[bool, float]:
    """Check whether a parcel can be the vehicle's next stop.

    `travelled` is the km from the hub to the current stop, not counting the
    return leg. Returns (feasible, leg), where leg is the km from the current
    stop to the parcel's location.
    """
    distances = context["travel_distance"]
    destination = record["delivery_location_id"]
    leg = distances[location][destination]
    arrival = departure + travelled + leg
    round_trip = travelled + leg + distances[destination][HUB]

    if load + record["size"] > context["capacity"]:
        return False, leg
    if not within_trip_limits(round_trip, departure, context):
        return False, leg
    if arrival < record["delivery_window_start"] or arrival > record["delivery_window_end"]:
        return False, leg
    return True, leg


def nearest_neighbour_route(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Build one trip by repeatedly appending the closest parcel that is on time.

    Each pass scans the parcels still waiting. Distance ties are broken by the
    earlier window end, then the earlier arrival time, then the parcel ID.
    """
    distances = context["travel_distance"]
    departure = context["current_time"] + context["departure_delay"]
    waiting = get_waiting(parcel)

    route = []
    load = 0.0
    # km from the hub to the route's last stop, not counting the return leg.
    travelled = 0.0
    location = HUB

    while len(waiting) > 0:
        chosen_id = None
        chosen_leg = 0.0
        chosen_window_end = 0.0
        chosen_arrival_time = 0.0

        for parcel_id in waiting:
            record = parcel[parcel_id]
            feasible, leg = check_parcel(record, location, load, travelled, departure, context)
            if not feasible:
                continue

            take_this = False
            if chosen_id is None:
                take_this = True
            elif leg < chosen_leg:
                take_this = True
            elif leg == chosen_leg and record["delivery_window_end"] < chosen_window_end:
                take_this = True
            elif leg == chosen_leg and record["delivery_window_end"] == chosen_window_end and record["arrival_time"] < chosen_arrival_time:
                take_this = True
            elif leg == chosen_leg and record["delivery_window_end"] == chosen_window_end and record["arrival_time"] == chosen_arrival_time and parcel_id < chosen_id:
                take_this = True

            if take_this:
                chosen_id = parcel_id
                chosen_leg = leg
                chosen_window_end = record["delivery_window_end"]
                chosen_arrival_time = record["arrival_time"]

        if chosen_id is None:
            break

        record = parcel[chosen_id]
        destination = record["delivery_location_id"]
        leg = distances[location][destination]
        route.append(chosen_id)
        load = load + record["size"]
        travelled = travelled + leg
        location = destination
        waiting.remove(chosen_id)

    return route


def evaluate_route(
    route: List[str], parcel: Dict[str, Parcel], context: SimulationContext
) -> Tuple[bool, float]:
    """Walk a route from departure, stop by stop.

    Returns (all_on_time, round_trip), where all_on_time is True if every
    parcel arrives inside its window and round_trip is the total km
    including the return to the hub.
    """
    distances = context["travel_distance"]
    departure = context["current_time"] + context["departure_delay"]
    all_on_time = True
    travelled = 0.0
    location = HUB

    for parcel_id in route:
        record = parcel[parcel_id]
        destination = record["delivery_location_id"]
        travelled = travelled + distances[location][destination]
        arrival = departure + travelled
        if arrival < record["delivery_window_start"] or arrival > record["delivery_window_end"]:
            all_on_time = False
        location = destination

    round_trip = travelled + distances[location][HUB]
    return all_on_time, round_trip