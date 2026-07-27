from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, date, time, timedelta, tzinfo

from .timezone_utils import get_timezone
from math import radians, sin, cos, sqrt, atan2
from bisect import bisect_left
from collections import defaultdict, deque
from typing import Optional, Any


INF = 10**15


def parse_hhmm_to_seconds(value: str) -> int:
    """
    Converts HH:MM or HH:MM:SS into seconds after service-day midnight.
    Allows GTFS-style hours above 24, e.g. '24:15:00'.
    """
    parts = value.strip().split(":")

    if len(parts) == 2:
        h, m = map(int, parts)
        s = 0
    elif len(parts) == 3:
        h, m, s = map(int, parts)
    else:
        raise ValueError(f"Invalid time format: {value!r}")

    return h * 3600 + m * 60 + s


def seconds_to_datetime_string(service_date: date, seconds: int, tz: tzinfo) -> str:
    dt = datetime.combine(service_date, time(0, 0), tzinfo=tz) + timedelta(seconds=seconds)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    """
    Distance in meters between two latitude/longitude points.
    Each point is represented as: (lat, lon)
    """
    lat1, lon1 = a
    lat2, lon2 = b

    earth_radius_m = 6_371_000.0

    p1 = radians(lat1)
    p2 = radians(lat2)
    dp = radians(lat2 - lat1)
    dl = radians(lon2 - lon1)

    x = sin(dp / 2) ** 2 + cos(p1) * cos(p2) * sin(dl / 2) ** 2

    return 2 * earth_radius_m * atan2(sqrt(x), sqrt(1 - x))


@dataclass(frozen=True)
class Stop:
    id: str
    name: str
    lat: float
    lon: float
    station_rating: float | None = None
    shelter_score: float | None = None
    accessibility_score: float | None = None


@dataclass(frozen=True)
class RoutePattern:
    """
    One route direction only.
    """
    id: str
    name: str
    stop_ids: tuple[str, ...]


@dataclass(frozen=True)
class StopTime:
    stop_id: str
    arrival: int
    departure: int


@dataclass(frozen=True)
class Trip:
    id: str
    route_id: str
    stop_times: tuple[StopTime, ...]

    # Python weekday numbers:
    # Monday=0, Tuesday=1, Wednesday=2, Thursday=3,
    # Friday=4, Saturday=5, Sunday=6.
    # Use None if the trip runs every day.
    service_days: Optional[frozenset[int]] = None

    def runs_on(self, weekday: int) -> bool:
        return self.service_days is None or weekday in self.service_days


@dataclass(frozen=True)
class Footpath:
    from_stop_id: str
    to_stop_id: str
    walk_time: int


@dataclass(frozen=True)
class LabelStats:
    walking_time: int = 0
    waiting_time: int = 0
    bus_rides: int = 0


@dataclass(frozen=True)
class ParentStep:
    kind: str
    prev_round: Optional[int] = None
    prev_stop_id: Optional[str] = None

    from_stop_id: Optional[str] = None
    to_stop_id: Optional[str] = None

    route_id: Optional[str] = None
    trip_id: Optional[str] = None

    departure: Optional[int] = None
    arrival: Optional[int] = None
    duration: Optional[int] = None


@dataclass(frozen=True)
class SolutionCandidate:
    round_number: int
    final_stop_id: Optional[str]
    final_arrival: int
    final_walk: int
    stats: LabelStats
    direct_walk: bool = False


@dataclass
class TransitData:
    stops: dict[str, Stop]
    routes: dict[str, RoutePattern]
    trips: dict[str, Trip]
    footpaths: dict[str, list[Footpath]] = field(default_factory=dict)

    routes_by_stop: dict[str, list[str]] = field(init=False)
    trips_by_route: dict[str, list[str]] = field(init=False)
    stop_time_by_trip_stop: dict[tuple[str, str], StopTime] = field(init=False)
    departures_by_route_stop: dict[tuple[str, str], list[tuple[int, str]]] = field(init=False)

    def __post_init__(self) -> None:
        self.routes_by_stop = defaultdict(list)

        for route_id, route in self.routes.items():
            for stop_id in route.stop_ids:
                self.routes_by_stop[stop_id].append(route_id)

        self.trips_by_route = defaultdict(list)
        self.stop_time_by_trip_stop = {}
        self.departures_by_route_stop = defaultdict(list)

        for trip_id, trip in self.trips.items():
            if trip.route_id not in self.routes:
                raise ValueError(
                    f"Trip {trip_id!r} references unknown route {trip.route_id!r}"
                )

            self.trips_by_route[trip.route_id].append(trip_id)

            for stop_time in trip.stop_times:
                if stop_time.stop_id not in self.stops:
                    raise ValueError(
                        f"Trip {trip_id!r} references unknown stop {stop_time.stop_id!r}"
                    )

                self.stop_time_by_trip_stop[(trip_id, stop_time.stop_id)] = stop_time

                self.departures_by_route_stop[(trip.route_id, stop_time.stop_id)].append(
                    (stop_time.departure, trip_id)
                )

        for key in self.departures_by_route_stop:
            self.departures_by_route_stop[key].sort()

        for stop_id in self.stops:
            self.footpaths.setdefault(stop_id, [])

    def arrival(self, trip_id: str, stop_id: str) -> Optional[int]:
        stop_time = self.stop_time_by_trip_stop.get((trip_id, stop_id))
        return None if stop_time is None else stop_time.arrival

    def departure(self, trip_id: str, stop_id: str) -> Optional[int]:
        stop_time = self.stop_time_by_trip_stop.get((trip_id, stop_id))
        return None if stop_time is None else stop_time.departure

    def first_trip_after(
        self,
        route_id: str,
        stop_id: str,
        ready_time: int,
        weekday: int,
    ) -> Optional[tuple[str, int]]:
        """
        Returns:
            (trip_id, departure_time)

        Meaning:
            The first trip on route_id at stop_id departing at or after ready_time.
        """
        departures = self.departures_by_route_stop.get((route_id, stop_id), [])
        index = bisect_left(departures, (ready_time, ""))

        while index < len(departures):
            departure_time, trip_id = departures[index]

            if self.trips[trip_id].runs_on(weekday):
                return trip_id, departure_time

            index += 1

        return None

    def generate_footpaths(
        self,
        max_walk_m: float = 450.0,
        walking_speed_mps: float = 1.25,
    ) -> None:
        """
        Optional helper.

        Generates walking transfer links between nearby stops.
        Use this if you do not already have transfer links between stations.
        """
        stop_items = list(self.stops.items())

        existing = {
            (fp.from_stop_id, fp.to_stop_id)
            for paths in self.footpaths.values()
            for fp in paths
        }

        for from_id, from_stop in stop_items:
            for to_id, to_stop in stop_items:
                if from_id == to_id:
                    continue

                if (from_id, to_id) in existing:
                    continue

                distance_m = haversine_m(
                    (from_stop.lat, from_stop.lon),
                    (to_stop.lat, to_stop.lon),
                )

                if distance_m <= max_walk_m:
                    walk_time = int(round(distance_m / walking_speed_mps))

                    self.footpaths.setdefault(from_id, []).append(
                        Footpath(
                            from_stop_id=from_id,
                            to_stop_id=to_id,
                            walk_time=walk_time,
                        )
                    )


def _nearby_stops(
    point: tuple[float, float],
    data: TransitData,
    radius_m: float,
    walking_speed_mps: float,
) -> list[tuple[str, int]]:
    nearby: list[tuple[str, int]] = []

    for stop_id, stop in data.stops.items():
        distance_m = haversine_m(point, (stop.lat, stop.lon))

        if distance_m <= radius_m:
            walk_time = int(round(distance_m / walking_speed_mps))
            nearby.append((stop_id, walk_time))

    nearby.sort(key=lambda item: item[1])
    return nearby


def _label_is_better(
    new_time: int,
    new_stats: LabelStats,
    old_time: int,
    old_stats: Optional[LabelStats],
) -> bool:
    if new_time < old_time:
        return True

    if new_time == old_time and old_stats is not None:
        return (
            new_stats.bus_rides,
            new_stats.walking_time,
            new_stats.waiting_time,
        ) < (
            old_stats.bus_rides,
            old_stats.walking_time,
            old_stats.waiting_time,
        )

    return False


def _solution_is_better(
    new: SolutionCandidate,
    old: Optional[SolutionCandidate],
    arrival_tolerance_s: int,
) -> bool:
    if old is None:
        return True

    if new.final_arrival + arrival_tolerance_s < old.final_arrival:
        return True

    if old.final_arrival + arrival_tolerance_s < new.final_arrival:
        return False

    return (
        new.stats.bus_rides,
        new.stats.walking_time,
        new.stats.waiting_time,
        new.final_arrival,
    ) < (
        old.stats.bus_rides,
        old.stats.walking_time,
        old.stats.waiting_time,
        old.final_arrival,
    )


def _make_leg(
    *,
    mode: str,
    departure: int,
    arrival: int,
    service_date: date,
    tz: tzinfo,
    **kwargs: Any,
) -> dict[str, Any]:
    duration = max(0, arrival - departure)

    return {
        "mode": mode,
        "departure_time": seconds_to_datetime_string(service_date, departure, tz),
        "arrival_time": seconds_to_datetime_string(service_date, arrival, tz),
        "duration_minutes": round(duration / 60, 1),
        **kwargs,
    }


def _reconstruct_route(
    *,
    solution: SolutionCandidate,
    parent: dict[tuple[int, str], ParentStep],
    data: TransitData,
    origin_name: str,
    destination_name: str,
    departure_seconds: int,
    service_date: date,
    tz: tzinfo,
) -> list[dict[str, Any]]:
    if solution.direct_walk:
        return [
            _make_leg(
                mode="walk",
                from_name=origin_name,
                to_name=destination_name,
                departure=departure_seconds,
                arrival=solution.final_arrival,
                service_date=service_date,
                tz=tz,
            )
        ]

    if solution.final_stop_id is None:
        return []

    reversed_legs: list[dict[str, Any]] = []
    key = (solution.round_number, solution.final_stop_id)

    while True:
        step = parent.get(key)

        if step is None:
            break

        if step.kind == "carry":
            key = (step.prev_round, step.prev_stop_id)
            continue

        if step.kind == "origin_walk":
            to_stop = data.stops[step.to_stop_id]

            if step.arrival > departure_seconds:
                reversed_legs.append(
                    _make_leg(
                        mode="walk",
                        from_name=origin_name,
                        to_name=to_stop.name,
                        departure=departure_seconds,
                        arrival=step.arrival,
                        service_date=service_date,
                        tz=tz,
                    )
                )
            break

        if step.kind == "walk_transfer":
            from_stop = data.stops[step.from_stop_id]
            to_stop = data.stops[step.to_stop_id]

            reversed_legs.append(
                _make_leg(
                    mode="walk",
                    from_name=from_stop.name,
                    to_name=to_stop.name,
                    departure=step.departure,
                    arrival=step.arrival,
                    service_date=service_date,
                    tz=tz,
                )
            )

            key = (step.prev_round, step.prev_stop_id)
            continue

        if step.kind == "ride":
            route = data.routes[step.route_id]
            from_stop = data.stops[step.from_stop_id]
            to_stop = data.stops[step.to_stop_id]

            reversed_legs.append(
                _make_leg(
                    mode="bus",
                    route_id=route.id,
                    route_name=route.name,
                    trip_id=step.trip_id,
                    from_name=from_stop.name,
                    to_name=to_stop.name,
                    departure=step.departure,
                    arrival=step.arrival,
                    service_date=service_date,
                    tz=tz,
                )
            )

            key = (step.prev_round, step.prev_stop_id)
            continue

        raise ValueError(f"Unknown step kind: {step.kind!r}")

    legs = list(reversed(reversed_legs))

    if solution.final_walk > 0 and solution.final_stop_id is not None:
        final_stop = data.stops[solution.final_stop_id]
        final_walk_departure = solution.final_arrival - solution.final_walk

        legs.append(
            _make_leg(
                mode="walk",
                from_name=final_stop.name,
                to_name=destination_name,
                departure=final_walk_departure,
                arrival=solution.final_arrival,
                service_date=service_date,
                tz=tz,
            )
        )

    return legs


def find_optimal_brt_route(
    *,
    origin: tuple[float, float],
    destination: tuple[float, float],
    departure_datetime: datetime,
    data: TransitData,
    origin_name: str = "Origin",
    destination_name: str = "Destination",
    max_bus_rides: int = 4,
    access_walk_radius_m: float = 800.0,
    egress_walk_radius_m: float = 800.0,
    first_boarding_buffer_s: int = 0,
    transfer_buffer_s: int = 60,
    walking_speed_mps: float = 1.25,
    arrival_tolerance_s: int = 180,
    direct_walk_limit_m: float = 1200.0,
    timezone_name: str = "Asia/Amman",
) -> dict[str, Any]:
    """
    Finds the optimal BRT/bus route from origin to destination.
    """

    if max_bus_rides < 0:
        raise ValueError("max_bus_rides must be non-negative")

    tz = get_timezone(timezone_name)

    if departure_datetime.tzinfo is None:
        local_dt = departure_datetime.replace(tzinfo=tz)
    else:
        local_dt = departure_datetime.astimezone(tz)

    service_date = local_dt.date()
    weekday = local_dt.weekday()

    departure_seconds = (
        local_dt.hour * 3600
        + local_dt.minute * 60
        + local_dt.second
    )

    origin_stops = _nearby_stops(
        origin,
        data,
        access_walk_radius_m,
        walking_speed_mps,
    )

    destination_stops = _nearby_stops(
        destination,
        data,
        egress_walk_radius_m,
        walking_speed_mps,
    )

    if not origin_stops:
        return {
            "status": "no_route_found",
            "reason": "No BRT or bus stop found within the access walking radius.",
        }

    if not destination_stops:
        return {
            "status": "no_route_found",
            "reason": "No BRT or bus stop found within the egress walking radius.",
        }

    best_arrival: list[dict[str, int]] = [
        defaultdict(lambda: INF) for _ in range(max_bus_rides + 1)
    ]

    parent: dict[tuple[int, str], ParentStep] = {}
    stats: dict[tuple[int, str], LabelStats] = {}

    marked_stops: set[str] = set()

    best_solution: Optional[SolutionCandidate] = None

    direct_distance_m = haversine_m(origin, destination)

    if direct_distance_m <= direct_walk_limit_m:
        direct_walk_time = int(round(direct_distance_m / walking_speed_mps))

        best_solution = SolutionCandidate(
            round_number=0,
            final_stop_id=None,
            final_arrival=departure_seconds + direct_walk_time,
            final_walk=direct_walk_time,
            stats=LabelStats(
                walking_time=direct_walk_time,
                waiting_time=0,
                bus_rides=0,
            ),
            direct_walk=True,
        )

    # Round 0: walk from origin to nearby stops.
    for stop_id, walk_time in origin_stops:
        arrival = departure_seconds + walk_time

        new_stats = LabelStats(
            walking_time=walk_time,
            waiting_time=0,
            bus_rides=0,
        )

        if _label_is_better(
            arrival,
            new_stats,
            best_arrival[0].get(stop_id, INF),
            stats.get((0, stop_id)),
        ):
            best_arrival[0][stop_id] = arrival
            stats[(0, stop_id)] = new_stats

            parent[(0, stop_id)] = ParentStep(
                kind="origin_walk",
                to_stop_id=stop_id,
                departure=departure_seconds,
                arrival=arrival,
                duration=walk_time,
            )

            marked_stops.add(stop_id)

    # Check walking-only access to destination through a nearby stop.
    for stop_id, final_walk in destination_stops:
        if best_arrival[0].get(stop_id, INF) >= INF:
            continue

        stop_stats = stats[(0, stop_id)]

        candidate = SolutionCandidate(
            round_number=0,
            final_stop_id=stop_id,
            final_arrival=best_arrival[0][stop_id] + final_walk,
            final_walk=final_walk,
            stats=LabelStats(
                walking_time=stop_stats.walking_time + final_walk,
                waiting_time=stop_stats.waiting_time,
                bus_rides=stop_stats.bus_rides,
            ),
        )

        if _solution_is_better(candidate, best_solution, arrival_tolerance_s):
            best_solution = candidate

    # Main RAPTOR search.
    # Each round allows one additional bus ride.
    for round_number in range(1, max_bus_rides + 1):
        current_arrival: dict[str, int] = dict(best_arrival[round_number - 1])

        # Carry previous labels forward.
        for stop_id in current_arrival:
            previous_key = (round_number - 1, stop_id)
            current_key = (round_number, stop_id)

            stats[current_key] = stats[previous_key]

            parent[current_key] = ParentStep(
                kind="carry",
                prev_round=round_number - 1,
                prev_stop_id=stop_id,
            )

        next_marked_stops: set[str] = set()

        candidate_routes: set[str] = set()

        for stop_id in marked_stops:
            candidate_routes.update(data.routes_by_stop.get(stop_id, []))

        for route_id in candidate_routes:
            route = data.routes[route_id]

            current_trip_id: Optional[str] = None
            boarding_stop_id: Optional[str] = None
            boarding_time: Optional[int] = None
            boarding_reach_time: Optional[int] = None
            boarding_stats: Optional[LabelStats] = None

            for stop_id in route.stop_ids:
                # Continue riding the selected trip.
                if current_trip_id is not None:
                    arrival_at_stop = data.arrival(current_trip_id, stop_id)

                    if arrival_at_stop is not None:
                        ride_stats = LabelStats(
                            walking_time=boarding_stats.walking_time,
                            waiting_time=(
                                boarding_stats.waiting_time
                                + max(0, boarding_time - boarding_reach_time)
                            ),
                            bus_rides=boarding_stats.bus_rides + 1,
                        )

                        old_time = current_arrival.get(stop_id, INF)
                        old_stats = stats.get((round_number, stop_id))

                        if _label_is_better(
                            arrival_at_stop,
                            ride_stats,
                            old_time,
                            old_stats,
                        ):
                            current_arrival[stop_id] = arrival_at_stop
                            stats[(round_number, stop_id)] = ride_stats

                            parent[(round_number, stop_id)] = ParentStep(
                                kind="ride",
                                prev_round=round_number - 1,
                                prev_stop_id=boarding_stop_id,
                                from_stop_id=boarding_stop_id,
                                to_stop_id=stop_id,
                                route_id=route_id,
                                trip_id=current_trip_id,
                                departure=boarding_time,
                                arrival=arrival_at_stop,
                                duration=arrival_at_stop - boarding_time,
                            )

                            next_marked_stops.add(stop_id)

                # Try boarding a bus at this stop.
                previous_reach_time = best_arrival[round_number - 1].get(stop_id, INF)

                if previous_reach_time >= INF:
                    continue

                if round_number == 1:
                    boarding_buffer = first_boarding_buffer_s
                else:
                    boarding_buffer = transfer_buffer_s

                ready_time = previous_reach_time + boarding_buffer

                next_trip = data.first_trip_after(
                    route_id=route_id,
                    stop_id=stop_id,
                    ready_time=ready_time,
                    weekday=weekday,
                )

                if next_trip is None:
                    continue

                candidate_trip_id, candidate_departure = next_trip

                should_replace_trip = False

                if current_trip_id is None:
                    should_replace_trip = True
                else:
                    current_departure_here = data.departure(current_trip_id, stop_id)

                    if current_departure_here is None:
                        should_replace_trip = True
                    elif candidate_departure < current_departure_here:
                        should_replace_trip = True

                if should_replace_trip:
                    current_trip_id = candidate_trip_id
                    boarding_stop_id = stop_id
                    boarding_time = candidate_departure
                    boarding_reach_time = previous_reach_time
                    boarding_stats = stats[(round_number - 1, stop_id)]

        # Walking transfers after this round's bus rides.
        queue = deque(next_marked_stops)

        while queue:
            from_stop_id = queue.popleft()
            from_time = current_arrival[from_stop_id]
            from_stats = stats[(round_number, from_stop_id)]

            for footpath in data.footpaths.get(from_stop_id, []):
                to_stop_id = footpath.to_stop_id

                new_time = from_time + footpath.walk_time

                new_stats = LabelStats(
                    walking_time=from_stats.walking_time + footpath.walk_time,
                    waiting_time=from_stats.waiting_time,
                    bus_rides=from_stats.bus_rides,
                )

                old_time = current_arrival.get(to_stop_id, INF)
                old_stats = stats.get((round_number, to_stop_id))

                if _label_is_better(
                    new_time,
                    new_stats,
                    old_time,
                    old_stats,
                ):
                    current_arrival[to_stop_id] = new_time
                    stats[(round_number, to_stop_id)] = new_stats

                    parent[(round_number, to_stop_id)] = ParentStep(
                        kind="walk_transfer",
                        prev_round=round_number,
                        prev_stop_id=from_stop_id,
                        from_stop_id=from_stop_id,
                        to_stop_id=to_stop_id,
                        departure=from_time,
                        arrival=new_time,
                        duration=footpath.walk_time,
                    )

                    next_marked_stops.add(to_stop_id)
                    queue.append(to_stop_id)

        best_arrival[round_number] = current_arrival

        # Check destination reachability.
        for stop_id, final_walk in destination_stops:
            arrival_at_stop = current_arrival.get(stop_id, INF)

            if arrival_at_stop >= INF:
                continue

            stop_stats = stats[(round_number, stop_id)]

            candidate = SolutionCandidate(
                round_number=round_number,
                final_stop_id=stop_id,
                final_arrival=arrival_at_stop + final_walk,
                final_walk=final_walk,
                stats=LabelStats(
                    walking_time=stop_stats.walking_time + final_walk,
                    waiting_time=stop_stats.waiting_time,
                    bus_rides=stop_stats.bus_rides,
                ),
            )

            if _solution_is_better(candidate, best_solution, arrival_tolerance_s):
                best_solution = candidate

        marked_stops = next_marked_stops

        if not marked_stops:
            break

    if best_solution is None:
        return {
            "status": "no_route_found",
            "reason": "No feasible route found after scanning available BRT or bus trips.",
        }

    legs = _reconstruct_route(
        solution=best_solution,
        parent=parent,
        data=data,
        origin_name=origin_name,
        destination_name=destination_name,
        departure_seconds=departure_seconds,
        service_date=service_date,
        tz=tz,
    )

    total_duration = best_solution.final_arrival - departure_seconds
    transfers = max(0, best_solution.stats.bus_rides - 1)

    return {
        "status": "ok",
        "departure_time": seconds_to_datetime_string(service_date, departure_seconds, tz),
        "arrival_time": seconds_to_datetime_string(
            service_date,
            best_solution.final_arrival,
            tz,
        ),
        "total_duration_minutes": round(total_duration / 60, 1),
        "bus_rides": best_solution.stats.bus_rides,
        "transfers": transfers,
        "walking_minutes": round(best_solution.stats.walking_time / 60, 1),
        "waiting_minutes": round(best_solution.stats.waiting_time / 60, 1),
        "legs": legs,
    }
