from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .brt_router import Footpath, RoutePattern, Stop, StopTime, TransitData, Trip, parse_hhmm_to_seconds


@dataclass(frozen=True)
class RouteMeta:
    route_id: str
    route_no: str
    name: str
    direction: str
    fare_jd: float
    stop_ids: tuple[str, ...]
    source_note: str = ""


def load_amman_brt_json(path: str | Path, apply_realtime_sample: bool = True) -> tuple[TransitData, dict[str, RouteMeta], dict[str, Any]]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    realtime_by_trip: dict[str, dict[str, Any]] = {}
    if apply_realtime_sample:
        realtime_by_trip = {u["trip_id"]: u for u in raw.get("realtime_updates_sample", [])}

    cancelled_trip_ids = {trip_id for trip_id, update in realtime_by_trip.items() if update.get("status") == "cancelled"}
    delay_by_trip = {
        trip_id: int(update.get("delay_seconds", 0))
        for trip_id, update in realtime_by_trip.items()
        if update.get("status") != "cancelled"
    }

    stops = {
        s["stop_id"]: Stop(
            id=s["stop_id"],
            name=s["name"],
            lat=float(s["lat"]),
            lon=float(s["lon"]),
            station_rating=float(s["station_rating"]) if s.get("station_rating") is not None else None,
            shelter_score=float(s["shelter_score"]) if s.get("shelter_score") is not None else None,
            accessibility_score=float(s["accessibility_score"]) if s.get("accessibility_score") is not None else None,
        )
        for s in raw["stops"]
    }

    routes: dict[str, RoutePattern] = {}
    route_meta: dict[str, RouteMeta] = {}
    for r in raw["routes"]:
        route_id = r["route_id"]
        route_no = str(r.get("route_no", route_id))
        direction = str(r.get("direction", ""))
        readable_name = f"{route_no} - {r['name']} ({direction})".strip()
        routes[route_id] = RoutePattern(id=route_id, name=readable_name, stop_ids=tuple(r["stops"]))
        route_meta[route_id] = RouteMeta(
            route_id=route_id,
            route_no=route_no,
            name=str(r["name"]),
            direction=direction,
            fare_jd=float(r.get("fare_jd", 0.0)),
            stop_ids=tuple(r["stops"]),
            source_note=str(r.get("source_note") or ""),
        )

    stop_times_by_trip: dict[str, list[tuple[int, StopTime]]] = defaultdict(list)
    for row in raw["stop_times"]:
        trip_id = row["trip_id"]
        if trip_id in cancelled_trip_ids:
            continue
        delay = delay_by_trip.get(trip_id, 0)
        stop_times_by_trip[trip_id].append(
            (
                int(row["sequence"]),
                StopTime(
                    stop_id=row["stop_id"],
                    arrival=parse_hhmm_to_seconds(row["arrival"]) + delay,
                    departure=parse_hhmm_to_seconds(row["departure"]) + delay,
                ),
            )
        )

    trips: dict[str, Trip] = {}
    for row in raw["trips"]:
        trip_id = row["trip_id"]
        if trip_id in cancelled_trip_ids:
            continue
        ordered = tuple(st for _, st in sorted(stop_times_by_trip[trip_id], key=lambda x: x[0]))
        if not ordered:
            continue
        service_days_raw = row.get("service_days")
        service_days = None if service_days_raw is None else frozenset(int(x) for x in service_days_raw)
        trips[trip_id] = Trip(id=trip_id, route_id=row["route_id"], stop_times=ordered, service_days=service_days)

    footpaths: dict[str, list[Footpath]] = defaultdict(list)
    for fp in raw.get("footpaths", []):
        footpaths[fp["from_stop"]].append(
            Footpath(from_stop_id=fp["from_stop"], to_stop_id=fp["to_stop"], walk_time=int(fp["walking_time_seconds"]))
        )

    metadata = dict(raw.get("metadata", {}))
    metadata["frequency_rules"] = raw.get("frequency_rules", [])
    metadata["source_file"] = path.name

    return TransitData(stops=stops, routes=routes, trips=trips, footpaths=dict(footpaths)), route_meta, metadata


def filter_transit_data_for_routes(data: TransitData, allowed_route_ids: set[str]) -> TransitData:
    routes = {rid: route for rid, route in data.routes.items() if rid in allowed_route_ids}
    trips = {tid: trip for tid, trip in data.trips.items() if trip.route_id in routes}
    return TransitData(stops=data.stops, routes=routes, trips=trips, footpaths=data.footpaths)
