"""Greedy nearest-neighbour dispatch. Take a parcel only when it lands inside its window."""

from typing import Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies.helpers import nearest_neighbour_route


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Build one trip by repeatedly appending the closest parcel that is on time.

    Each pass scans the parcels still waiting. Capacity, range and the return
    cutoff are checked the same way as the baseline. A parcel whose arrival
    would fall outside its window is left for a later round. Inputs are
    snapshots and are never modified.
    """
    return nearest_neighbour_route(parcel, context)
