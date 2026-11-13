"""Nearest neighbour policy (on-time parcels only)."""

from typing import Dict, List

from simulator.models import Parcel, SimulationContext
from solution.policies.helpers import nearest_neighbour_route


def dispatch(parcel: Dict[str, Parcel], context: SimulationContext) -> List[str]:
    """Route building is shared with the 2-opt policy, see helpers.nearest_neighbour_route."""
    return nearest_neighbour_route(parcel, context)
