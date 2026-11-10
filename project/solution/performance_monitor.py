"""Calculate performance metrics from one simulation run's event log."""

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from simulator.loaders import day_input_paths


def _to_minutes(hhmm: str) -> float:
    """Convert an "HH:MM" string to minutes after midnight, e.g. "17:00" -> 1020."""
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)
 
 
def calculate_metrics(
    parcels: List[Dict[str, str]],
    distances: List[Dict[str, str]],
    config: Dict[str, Any],
    events: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Main metric: on-time delivery rate.
 
    A parcel is on time if it is delivered with
    window_start <= delivery time <= window_end (both ends included).
    The rate divides by ALL parcels in the day's file, so undelivered
    parcels count as not on time and a policy cannot score well by
    delivering only a few easy parcels.
 
    Secondary metrics: parcels delivered, early, late and undelivered,
    and kilometres driven per delivered parcel.
    """
 
    # Parcel ID -> its record, for O(1) lookup when matching delivery events.
    parcel_by_id = {row["parcel_id"]: row for row in parcels}
 
    # (origin, destination) -> distance in km.
    distance = {
        (row["location_1"], row["location_2"]): float(row["dist"])
        for row in distances
    }
 
    on_time = early = late = 0
    trip_stops: Dict[Any, List[str]] = {}  # (vehicle, trip) -> locations in delivery order
 
    for event in events:
        if event["event_type"] == "hub_departure":
            trip_stops[(event["vehicle_id"], event["trip_id"])] = []
 
        elif event["event_type"] == "delivery":
            record = parcel_by_id[event["parcel_id"]]
            start = _to_minutes(record["delivery_window_start"])
            end = _to_minutes(record["delivery_window_end"])
 
            if event["time"] < start:
                early += 1
            elif event["time"] > end:
                late += 1
            else:
                on_time += 1
 
            trip_stops[(event["vehicle_id"], event["trip_id"])].append(
                record["delivery_location_id"]
            )
 
    # Distance driven: HUB -> each stop in order -> HUB, for every trip.
    total_km = 0.0
    for stops in trip_stops.values():
        location = "HUB"
        for stop in stops + ["HUB"]:
            total_km += distance[(location, stop)]
            location = stop
 
    total = len(parcels)
    delivered = on_time + early + late
 
    return {
        "on_time_rate": round(on_time / total, 4) if total else 0.0,
        "on_time_parcels": on_time,
        "total_parcels": total,
        "delivered_parcels": delivered,
        "early_parcels": early,
        "late_parcels": late,
        "undelivered_parcels": total - delivered,
        "km_driven": round(total_km, 1),
        "km_per_delivered_parcel": round(total_km / delivered, 3) if delivered else 0.0,
    }


def main(argv: Optional[List[str]] = None) -> int:
    """Load one day's inputs and event log, then write the metrics report."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"),
                        help="directory containing dist.csv, config.json and demand/")
    parser.add_argument("--day", required=True, help="day identifier, for example day_001")
    parser.add_argument("--log", type=Path, required=True,
                        help="event log from a simulator run")
    parser.add_argument("--output", type=Path,
                        help="JSON report (default: metrics.json beside the selected log)")
    args = parser.parse_args(argv)
    try:
        parcel_path, distance_path, config_path = day_input_paths(args.data, args.day)
        output = args.output if args.output is not None else args.log.with_name("metrics.json")
        # The input files all live in the data directory, so this also protects them.
        if output.resolve() == args.data.resolve() or args.data.resolve() in output.resolve().parents:
            raise ValueError("report output must be outside the input data directory")
        if output.resolve() == args.log.resolve():
            raise ValueError("report output must not overwrite the log")
        with parcel_path.open(newline="", encoding="utf-8-sig") as stream:
            parcels = list(csv.DictReader(stream))
        with distance_path.open(newline="", encoding="utf-8-sig") as stream:
            distances = list(csv.DictReader(stream))
        config = json.loads(config_path.read_text(encoding="utf-8-sig"))
        with args.log.open(encoding="utf-8") as stream:
            events = [json.loads(line) for line in stream if line.strip()]
        metrics = calculate_metrics(parcels, distances, config, events)
        report = json.dumps(metrics, indent=2, allow_nan=False) + "\n"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report, encoding="utf-8")
    except (OSError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")
    print(f"Metrics report: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
