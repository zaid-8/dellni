from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, time, timedelta
from difflib import get_close_matches
from pathlib import Path
from typing import Any

from .timezone_utils import get_timezone
from .brt_router import Stop, TransitData, find_optimal_brt_route, haversine_m
from .data_loader import RouteMeta, filter_transit_data_for_routes, load_amman_brt_json

AMMAN_TZ = get_timezone("Asia/Amman")
WALKING_SPEED_MPS = 1.25
WALK_TO_STOP_THRESHOLD_S = 10 * 60
WALK_TO_STOP_DISTANCE_THRESHOLD_M = 1000.0
URBAN_CAR_SPEED_MPS = 8.0  # about 29 km/h in city streets, MVP estimate
CAR_ACCESS_BUFFER_S = 75
NEAR_ROUTE_ACCESS_RADIUS_M = 850.0
MAX_BOARDING_SEARCH_M = 6500.0
BOARDING_CANDIDATE_LIMIT = 18
GEOCODER_TIMEOUT_S = 4
AMMAN_VIEWBOX = "35.75,32.15,36.15,31.80"  # west,north,east,south for Nominatim


@dataclass(frozen=True)
class ResolvedLocation:
    name: str
    lat: float
    lon: float
    stop_id: str | None = None
    matched_by: str = "text"
    confidence: float = 1.0

    def point(self) -> tuple[float, float]:
        return (self.lat, self.lon)


class JsonStore:
    def __init__(self, path: str | Path, root_key: str):
        self.path = Path(path)
        self.root_key = root_key
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text(json.dumps({root_key: []}, ensure_ascii=False, indent=2), encoding="utf-8")

    def read(self) -> dict[str, Any]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if self.root_key not in data:
                data[self.root_key] = []
            return data
        except Exception:
            return {self.root_key: []}

    def write(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class CrowdStore(JsonStore):
    def __init__(self, path: str | Path):
        super().__init__(path, "ratings")

    def add_rating(self, route_id: str, rating: int, note: str = "") -> dict[str, Any]:
        rating = max(1, min(5, int(rating)))
        data = self.read()
        data.setdefault("ratings", []).append({
            "route_id": route_id,
            "rating": rating,
            "note": note[:160],
            "created_at": datetime.now(AMMAN_TZ).isoformat(timespec="seconds"),
        })
        self.write(data)
        return self.summary(route_id)

    def summary(self, route_id: str) -> dict[str, Any]:
        ratings = [r for r in self.read().get("ratings", []) if r.get("route_id") == route_id]
        if not ratings:
            return {"route_id": route_id, "count": 0, "average": None, "label_ar": "لا يوجد تقييم بعد", "label_en": "No ratings yet"}
        avg = sum(int(r.get("rating", 3)) for r in ratings) / len(ratings)
        if avg >= 4.4:
            ar = "مريح غالبا"
            en = "Usually comfortable"
        elif avg >= 3.7:
            ar = "ازدحام متوسط"
            en = "Moderate crowding"
        else:
            ar = "قد يكون مزدحما"
            en = "May be crowded"
        return {"route_id": route_id, "count": len(ratings), "average": round(avg, 1), "label_ar": ar, "label_en": en}


class TripFeedbackStore(JsonStore):
    def __init__(self, path: str | Path):
        super().__init__(path, "trip_ratings")

    def add(self, payload: dict[str, Any]) -> dict[str, Any]:
        rating = max(1, min(5, int(payload.get("rating", 5))))
        data = self.read()
        data.setdefault("trip_ratings", []).append({
            "rating": rating,
            "route_ids": payload.get("route_ids", []),
            "origin": payload.get("origin", ""),
            "destination": payload.get("destination", ""),
            "note": str(payload.get("note", ""))[:240],
            "created_at": datetime.now(AMMAN_TZ).isoformat(timespec="seconds"),
        })
        self.write(data)
        return {"status": "ok", "message_ar": "تم حفظ تقييم الرحلة. شكرا لمساعدتك في تحسين دلني.", "message_en": "Trip rating saved. Thank you for improving Dellni."}


class DellniRouteService:
    def __init__(self, data_path: str | Path, feedback_path: str | Path, apply_realtime_sample: bool = True) -> None:
        self.data, self.route_meta, self.metadata = load_amman_brt_json(data_path, apply_realtime_sample=apply_realtime_sample)
        self.feedback = CrowdStore(feedback_path)
        self.trip_feedback = TripFeedbackStore(Path(feedback_path).with_name("trip_feedback.json"))
        self.alias_to_stop: dict[str, str] = {}
        self.area_locations: dict[str, ResolvedLocation] = {}
        self.landmarks_ar: dict[str, str] = {}
        self.landmarks_en: dict[str, str] = {}
        self._cache: dict[str, dict[str, Any]] = {}
        self._geocode_cache: dict[str, ResolvedLocation | None] = {}
        self._build_location_index()

    @staticmethod
    def _normalize(text: str) -> str:
        text = str(text or "").strip().lower()
        text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ة", "ه")
        text = re.sub(r"[ـًٌٍَُِّْ]", "", text)
        text = re.sub(r"[^\w\s\u0600-\u06ff]+", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def _contains_arabic(text: str) -> bool:
        return any("\u0600" <= ch <= "\u06ff" for ch in str(text or ""))

    def _build_location_index(self) -> None:
        manual_aliases = {
            "صويلح": "sweileh_terminal", "مجمع صويلح": "sweileh_terminal", "sweileh": "sweileh_terminal", "sweileh terminal": "sweileh_terminal",
            "الجامعة الأردنية": "university_jordan", "الجامعة الاردنية": "university_jordan", "مسجد الجامعة": "university_jordan", "university of jordan": "university_jordan", "uj": "university_jordan",
            "التعليم العالي": "higher_education", "higher education": "higher_education", "queen rania": "higher_education",
            "دوار الصحافة": "sahafa_roundabout", "الصحافة": "sahafa_roundabout", "sahafa": "sahafa_roundabout",
            "المدينة الرياضية": "sports_city", "مدينة الحسين": "sports_city", "دوار المدينة": "sports_city", "دوار المدينة الرياضية": "sports_city", "sports city": "sports_city",
            "حدائق الملك عبدالله": "king_abdullah_gardens", "حدائق الملك عبد الله": "king_abdullah_gardens", "king abdullah gardens": "king_abdullah_gardens",
            "وادي صقرة": "wadi_saqra_intersection", "تقاطع وادي صقرة": "wadi_saqra_intersection", "wadi saqra": "wadi_saqra_intersection",
            "المركز العربي الطبي": "arab_medical_center", "المركز العربي": "arab_medical_center", "arab medical center": "arab_medical_center",
            "امديست": "amideast_wadi_saqra", "أمديست": "amideast_wadi_saqra", "amideast": "amideast_wadi_saqra",
            "42 عمان": "forty_two_amman", "42 عمّان": "forty_two_amman", "٤٢ عمان": "forty_two_amman", "٤٢ عمّان": "forty_two_amman", "42 amman": "forty_two_amman", "school 42 amman": "forty_two_amman",
            "رأس العين": "ras_al_ain_park", "راس العين": "ras_al_ain_park", "ras al ain": "ras_al_ain_park",
            "أمانة عمان": "greater_amman_municipality", "امانة عمان": "greater_amman_municipality", "امانة عمان الكبرى": "greater_amman_municipality", "greater amman municipality": "greater_amman_municipality",
            "مركز الحسين الثقافي": "hussein_cultural_center", "الحسين الثقافي": "hussein_cultural_center", "hussein cultural center": "hussein_cultural_center", "al hussein cultural center": "hussein_cultural_center",
            "العبدلي": "interior_circle", "دوار الداخلية": "interior_circle", "البوليفارد": "interior_circle", "abdali": "interior_circle", "interior circle": "interior_circle",
            "متحف الأردن": "jordan_museum_terminal", "متحف الاردن": "jordan_museum_terminal", "راس العين": "jordan_museum_terminal", "jordan museum": "jordan_museum_terminal",
            "المحطة": "mahata_terminal", "مجمع المحطة": "mahata_terminal", "mahata": "mahata_terminal", "mahatta": "mahata_terminal",
            "رغدان": "raghadan_terminal", "وسط البلد": "raghadan_terminal", "downtown": "raghadan_terminal", "raghadan": "raghadan_terminal",
            "طارق": "tariq_terminal", "طبربور": "tariq_terminal", "محطة طارق": "tariq_terminal", "tariq": "tariq_terminal", "tabarbour": "tariq_terminal",
            "ماركا": "marka_brt_station", "marka": "marka_brt_station", "الرصيفة": "russeifa", "russeifa": "russeifa",
            "الزرقاء": "zarqa_terminal", "زرقاء": "zarqa_terminal", "zarqa": "zarqa_terminal",
            # Salt/Balqa route options were removed from the current submission dataset because they are outside the validated Amman station set.
            "مادبا": "madaba_secondary_school_boys", "madaba": "madaba_secondary_school_boys",
            "مستشفى حمزة": "hamza_hospital_tariq", "مستشفى الأمير حمزة": "hamza_hospital_tariq", "hamza hospital": "hamza_hospital_tariq",
            "خلدا": "khalda_circle", "دوار خلدا": "khalda_circle", "khalda": "khalda_circle",
            "سيتي مول": "city_mall", "ستي مول": "city_mall", "city mall": "city_mall",
            "مجمع الأعمال": "business_park", "مجمع الاعمال": "business_park", "business park": "business_park",
            "مرج الحمام": "marj_al_hammam", "marj al hammam": "marj_al_hammam",
            "عبدون": "abdoun_circle", "دوار عبدون": "abdoun_circle", "abdoun": "abdoun_circle",
            "الدوار الأول": "first_circle", "الدوار الاول": "first_circle", "first circle": "first_circle",
            "الدوار الثاني": "second_circle", "second circle": "second_circle",
            "الدوار الثالث": "third_circle", "third circle": "third_circle",
            "الدوار الرابع": "fourth_circle", "fourth circle": "fourth_circle",
            "الدوار الخامس": "fifth_circle", "fifth circle": "fifth_circle",
            "الدوار السادس": "sixth_circle", "sixth circle": "sixth_circle",
            "الدوار السابع": "seventh_circle", "seventh circle": "seventh_circle",
            "الدوار الثامن": "eighth_circle", "eighth circle": "eighth_circle",
            "المستشفى الإسلامي": "islamic_hospital", "المستشفى الاسلامي": "islamic_hospital", "islamic hospital": "islamic_hospital",
            "الاذاعة والتلفزيون": "radio_tv", "الإذاعة والتلفزيون": "radio_tv", "radio and television": "radio_tv",
            "أم أذينة": "umm_uthaina", "ام اذينة": "umm_uthaina", "umm uthaina": "umm_uthaina",
        }
        areas = {
            "الجبيهة": ("الجبيهة", 32.0248, 35.8759),
            "jubaiha": ("الجبيهة", 32.0248, 35.8759),
            "ضاحية الرشيد": ("ضاحية الرشيد", 32.0091, 35.8624),
            "تلاع العلي": ("تلاع العلي", 31.9986, 35.8447),
            "المدينة الطبية": ("المدينة الطبية", 31.9990, 35.8261),
            "شميساني": ("الشميساني", 31.9732, 35.9021),
            "جبل عمان": ("جبل عمان", 31.9509, 35.9184),
            "اللويبدة": ("اللويبدة", 31.9575, 35.9272),
            "الصويفية": ("الصويفية", 31.9588, 35.8612),
            "مرج الحمام": ("مرج الحمام", 31.8998, 35.8457),
            "البيادر": ("البيادر", 31.9577, 35.8330),
            "نزال": ("نزال", 31.9356, 35.9173),
            "القويسمة": ("القويسمة", 31.9109, 35.9493),
            "الوحدات": ("الوحدات", 31.9308, 35.9439),
            "طبربور": ("طبربور", 31.9995, 35.9348),
            # Common map-search landmarks that users often type but that are not bus stops.
            # 42 Amman's public campus listing places it in Abdun; we keep it as a coordinate
            # landmark, then the router selects the nearest usable bus station.
            "تاج مول": ("تاج مول - عبدون", 31.9510, 35.8848),
            "taj mall": ("Taj Mall - Abdoun", 31.9510, 35.8848),
            "عبدلي مول": ("عبدلي مول", 31.9670, 35.9065),
            "abdali mall": ("Abdali Mall", 31.9670, 35.9065),
            "مكة مول": ("مكة مول", 31.9776, 35.8434),
            "mecca mall": ("Mecca Mall", 31.9776, 35.8434),
            "حدائق الحسين": ("حدائق الحسين", 31.9843, 35.8318),
            "king hussein park": ("King Hussein Park", 31.9843, 35.8318),
        }
        for stop_id, stop in self.data.stops.items():
            for alias in {stop_id, stop.name, getattr(stop, "name_en", ""), stop.name.replace("/", " "), stop.name.replace("-", " ")}:
                if alias:
                    self.alias_to_stop[self._normalize(alias)] = stop_id
        for alias, stop_id in manual_aliases.items():
            self.alias_to_stop[self._normalize(alias)] = stop_id
        for alias, (name, lat, lon) in areas.items():
            self.area_locations[self._normalize(alias)] = ResolvedLocation(name=name, lat=lat, lon=lon, matched_by="area", confidence=0.78)
        for stop_id, stop in self.data.stops.items():
            self.landmarks_ar[stop_id] = self._landmark_ar(stop_id, stop.name)
            self.landmarks_en[stop_id] = stop.name

    def _landmark_ar(self, stop_id: str, name: str) -> str:
        custom = {
            "sweileh_terminal": "عند مجمع صويلح للباص السريع",
            "university_jordan": "قرب البوابة الرئيسية للجامعة الأردنية",
            "sports_city": "قرب جسر ومداخل المدينة الرياضية",
            "interior_circle": "قرب دوار الداخلية باتجاه العبدلي",
            "jordan_museum_terminal": "عند رأس العين قرب متحف الأردن",
            "mahata_terminal": "داخل منطقة مجمع المحطة",
            "tariq_terminal": "عند محطة طارق باتجاه طبربور",
            "zarqa_terminal": "عند مجمع الزرقاء الرئيسي",
            "city_mall": "قرب سيتي مول ومركز زها",
            "king_abdullah_gardens": "عند حدائق الملك عبدالله على مسار الباص السريع 99",
            "wadi_saqra_intersection": "عند تقاطع وادي صقرة",
            "arab_medical_center": "قرب المركز العربي الطبي والدوار الخامس",
            "amideast_wadi_saqra": "قرب أمديست ووادي صقرة",
            "forty_two_amman": "مقابل 42 عمّان / عبدون الشمالي",
            "ras_al_ain_park": "قرب حدائق رأس العين",
            "greater_amman_municipality": "قرب مبنى أمانة عمان الكبرى",
            "hussein_cultural_center": "قرب مركز الحسين الثقافي في رأس العين",
        }
        return custom.get(stop_id, name)

    def locations_catalog(self) -> list[dict[str, Any]]:
        # The datalist shown to users should contain only validated bus/BRT stations.
        # Generic neighborhoods still work when typed, but they are not suggested as
        # selectable destinations because the user asked to hide places with no station.
        rows: list[dict[str, Any]] = []
        for stop_id, stop in self.data.stops.items():
            rows.append({
                "stop_id": stop_id,
                "type": "stop",
                "name": stop.name,
                "lat": stop.lat,
                "lon": stop.lon,
                "landmark": self.landmarks_ar.get(stop_id, stop.name),
                "station_rating": getattr(stop, "station_rating", None),
            })
        return sorted(rows, key=lambda x: x["name"])

    def routes_catalog(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        def route_sort(item: tuple[str, RouteMeta]) -> tuple[int, str]:
            digits = re.sub(r"\D", "", item[1].route_no or "999")
            return (int(digits or "999"), item[0])
        for route_id, meta in sorted(self.route_meta.items(), key=route_sort):
            rows.append({
                "route_id": route_id,
                "route_no": meta.route_no,
                "name": meta.name,
                "direction": meta.direction,
                "fare_jd": meta.fare_jd,
                "service_summary": self._frequency_summary(route_id),
                "source_note": meta.source_note,
                "crowd": self.feedback.summary(route_id),
                "stops": [self._stop_public(sid) for sid in meta.stop_ids if sid in self.data.stops],
            })
        return rows

    def _stop_public(self, stop_id: str) -> dict[str, Any]:
        stop = self.data.stops[stop_id]
        return {
            "stop_id": stop_id,
            "name": stop.name,
            "lat": stop.lat,
            "lon": stop.lon,
            "landmark": self.landmarks_ar.get(stop_id, stop.name),
            "station_rating": getattr(stop, "station_rating", None),
            "shelter_score": getattr(stop, "shelter_score", None),
            "accessibility_score": getattr(stop, "accessibility_score", None),
        }

    def data_quality(self) -> dict[str, Any]:
        return {
            "metadata": self.metadata,
            "counts": {
                "stops": len(self.data.stops),
                "route_directions": len(self.data.routes),
                "trips": len(self.data.trips),
                "footpaths": sum(len(v) for v in self.data.footpaths.values()),
            },
            "ai_boundary_ar": "الذكاء الاصطناعي في دلني لا يحسب المسار ولا يخترع محطات أو أسعار. الحساب من JSON ومحرك التوجيه فقط؛ والـ AI يصيغ أو يفهم الكلام عند توفر API key.",
            "ai_boundary_en": "AI does not compute routes or invent stops/fares. The deterministic engine and JSON data compute the journey; AI only parses or rewrites language when an API key is configured.",
            "geocoder_note_ar": "إذا كتب المستخدم معلما غير موجود في JSON، يحاول دلني تحديده عبر OpenStreetMap/Nominatim ثم يختار أقرب محطة مناسبة من بيانات الباص.",
            "geocoder_note_en": "If the user types an unmapped landmark, Dellni can resolve it through OpenStreetMap/Nominatim, then select the nearest usable bus station from the local network.",
        }

    def _frequency_summary(self, route_id: str) -> str:
        for rule in self.metadata.get("frequency_rules", []):
            if rule.get("route_id") == route_id:
                blocks = rule.get("generated_from", [])
                if not blocks:
                    return rule.get("note", "جدول داخل JSON")
                return "؛ ".join([f"{b.get('start')}–{b.get('end')} كل {b.get('headway_min')} دقيقة" for b in blocks])
        return "جدول محمّل من ملف JSON"

    def _geocode_external(self, text: str) -> ResolvedLocation | None:
        """Resolve unmapped landmarks through OpenStreetMap/Nominatim.

        This is a map-search fallback, not route calculation. It only turns a user phrase
        such as "42 عمان" or "Taj Mall" into coordinates. The deterministic routing engine
        still chooses the nearest usable stop, route, fare and timing from the JSON network.
        """
        text = str(text or "").strip()
        norm = self._normalize(text)
        if not norm or len(norm) < 2:
            return None
        if norm in self._geocode_cache:
            return self._geocode_cache[norm]

        # Try the original phrase, then variants with Amman/Jordan context.
        variants = []
        for q in [text, text.replace("عمّان", "عمان"), text.replace("عمان", "Amman"), f"{text}, Amman, Jordan", f"{text}, عمّان, الأردن"]:
            q = re.sub(r"\s+", " ", q).strip()
            if q and q not in variants:
                variants.append(q)

        headers = {"User-Agent": "DellniHackathonMVP/1.0 map-search geocoder"}
        for query in variants:
            params = urllib.parse.urlencode({
                "q": query,
                "format": "jsonv2",
                "addressdetails": "1",
                "limit": "3",
                "countrycodes": "jo",
                "bounded": "1",
                "viewbox": AMMAN_VIEWBOX,
            })
            url = f"https://nominatim.openstreetmap.org/search?{params}"
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=GEOCODER_TIMEOUT_S) as response:
                    rows = json.loads(response.read().decode("utf-8"))
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
                continue
            for row in rows or []:
                try:
                    lat = float(row.get("lat"))
                    lon = float(row.get("lon"))
                except (TypeError, ValueError):
                    continue
                if not (31.75 <= lat <= 32.20 and 35.65 <= lon <= 36.25):
                    continue
                display = str(row.get("display_name") or text)
                short_name = display.split(",")[0].strip() or text
                loc = ResolvedLocation(
                    name=short_name,
                    lat=lat,
                    lon=lon,
                    matched_by="openstreetmap_geocoder",
                    confidence=float(row.get("importance") or 0.68),
                )
                self._geocode_cache[norm] = loc
                return loc
        self._geocode_cache[norm] = None
        return None

    def resolve_location(self, value: Any, *, field_name: str = "location") -> ResolvedLocation:
        if isinstance(value, dict):
            lat = value.get("lat")
            lon = value.get("lon")
            if lat is not None and lon is not None:
                return ResolvedLocation(
                    name=str(value.get("name") or ("موقع حالي" if field_name.startswith("start") else "وجهة محددة")),
                    lat=float(lat), lon=float(lon), stop_id=value.get("stop_id"), matched_by="coordinates", confidence=1.0,
                )
        text = str(value or "").strip()
        norm = self._normalize(text)
        if not norm:
            raise ValueError("اكتب الموقع أو اختره من الخريطة.")
        if norm in self.alias_to_stop:
            return self._stop_location(self.alias_to_stop[norm], matched_by="alias", confidence=1.0)
        if norm in self.area_locations:
            return self.area_locations[norm]
        close = get_close_matches(norm, list(self.alias_to_stop), n=1, cutoff=0.78)
        if close:
            return self._stop_location(self.alias_to_stop[close[0]], matched_by="fuzzy", confidence=0.83)
        area_close = get_close_matches(norm, list(self.area_locations), n=1, cutoff=0.78)
        if area_close:
            return self.area_locations[area_close[0]]
        external = self._geocode_external(text)
        if external is not None:
            return external
        raise ValueError(f"لم أتعرف على '{text}'. جرّب اسم منطقة أو معلم داخل عمّان مثل صويلح، العبدلي، الجامعة الأردنية، 42 عمّان، مركز الحسين الثقافي، خلدا.")

    def _stop_location(self, stop_id: str, *, matched_by: str = "stop", confidence: float = 1.0) -> ResolvedLocation:
        stop = self.data.stops[stop_id]
        return ResolvedLocation(name=stop.name, lat=stop.lat, lon=stop.lon, stop_id=stop_id, matched_by=matched_by, confidence=confidence)

    def parse_prompt(self, prompt: str) -> dict[str, Any]:
        text = str(prompt or "").strip()
        norm = self._normalize(text)
        result: dict[str, Any] = {"language": "ar" if self._contains_arabic(text) else "en", "priority": "lowest_cost"}
        arabic_digits = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
        normalized_time_text = text.translate(arabic_digits)
        time_match = re.search(r"(\d{1,2})[:٫.](\d{2})", normalized_time_text)
        if not time_match:
            hour_match = re.search(r"(?:الساعه|الساعة)\s*(\d{1,2})", normalized_time_text)
            if hour_match:
                result["departure_time"] = f"{int(hour_match.group(1)):02d}:00"
        if time_match:
            result["departure_time"] = f"{int(time_match.group(1)):02d}:{time_match.group(2)}"
        # Arabic patterns: من X إلى/ل/لل Y. Allow no space after the destination preposition.
        m = re.search(r"(?:من|انا في|أنا في|موقعي)\s+(.+?)\s+(?:الى|إلى|لل|ل|على|ع(?=\s))\s*(.+?)(?:\s+الساعه|\s+الساعة|\s+بكرا|\s+اليوم|$)", text)
        if m:
            result["origin_text"] = m.group(1).strip(" ؟?،,")
            result["destination_text"] = m.group(2).strip(" ؟?،,")
            return result
        # English patterns
        m = re.search(r"from\s+(.+?)\s+to\s+(.+?)(?:\s+at\s+|$)", text, re.I)
        if m:
            result["origin_text"] = m.group(1).strip(" ?,.!")
            result["destination_text"] = m.group(2).strip(" ?,.!")
            return result
        # If no pattern, try discovering two known aliases in the prompt, in order.
        hits: list[tuple[int, str]] = []
        for alias, sid in self.alias_to_stop.items():
            if len(alias) < 3:
                continue
            pos = norm.find(alias)
            if pos >= 0:
                hits.append((pos, self.data.stops[sid].name))
        hits = sorted(hits, key=lambda x: x[0])
        if len(hits) >= 2:
            result["origin_text"] = hits[0][1]
            result["destination_text"] = hits[1][1]
        return result

    def _optional_ai_parse(self, prompt: str) -> dict[str, Any]:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {}
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            known = [row["name"] for row in self.locations_catalog()[:120]]
            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                temperature=0,
                messages=[
                    {"role": "system", "content": "Extract routing fields only. Return compact JSON with origin_text, destination_text, departure_time if present, language. Keep place names exactly as the user wrote them, even if they are not in the known list; the backend map geocoder will resolve unknown landmarks. Do not invent routes, fares, coordinates, or station names."},
                    {"role": "user", "content": json.dumps({"prompt": prompt, "known_locations": known}, ensure_ascii=False)},
                ],
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content or "{}"
            parsed = json.loads(raw)
            return {k: parsed.get(k) for k in ["origin_text", "destination_text", "departure_time", "language"] if parsed.get(k)}
        except Exception:
            return {}

    @staticmethod
    def _parse_departure(value: Any) -> datetime:
        if not value:
            return datetime.now(AMMAN_TZ)
        if isinstance(value, datetime):
            return value.astimezone(AMMAN_TZ) if value.tzinfo else value.replace(tzinfo=AMMAN_TZ)
        text = str(value).strip()
        try:
            dt = datetime.fromisoformat(text)
            return dt.astimezone(AMMAN_TZ) if dt.tzinfo else dt.replace(tzinfo=AMMAN_TZ)
        except ValueError:
            pass
        m = re.fullmatch(r"(\d{1,2}):(\d{2})", text)
        if m:
            today = datetime.now(AMMAN_TZ).date()
            return datetime.combine(today, time(int(m.group(1)), int(m.group(2))), tzinfo=AMMAN_TZ)
        return datetime.now(AMMAN_TZ)

    def route_from_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        parsed: dict[str, Any] = {}
        prompt = str(payload.get("prompt") or "").strip()
        if prompt:
            parsed = self.parse_prompt(prompt)
            if not parsed.get("origin_text") or not parsed.get("destination_text"):
                ai_parsed = self._optional_ai_parse(prompt)
                if ai_parsed:
                    parsed.update({k: v for k, v in ai_parsed.items() if v})
                    parsed["ai_parser_attempted"] = True
        language = payload.get("language") or parsed.get("language") or "ar"
        language = "en" if str(language).lower().startswith("en") else "ar"
        priority = "lowest_cost"
        landmark_mode = True

        origin_value: Any = None
        if payload.get("origin_coords"):
            origin_value = payload["origin_coords"]
        elif payload.get("origin"):
            origin_value = payload["origin"]
        elif parsed.get("origin_text"):
            origin_value = parsed["origin_text"]

        destination_value: Any = None
        if payload.get("destination_coords"):
            destination_value = payload["destination_coords"]
        elif payload.get("destination"):
            destination_value = payload["destination"]
        elif parsed.get("destination_text"):
            destination_value = parsed["destination_text"]

        if not origin_value or not destination_value:
            return {
                "status": "input_error",
                "message": "حدد نقطة البداية والوجهة. يمكنك استخدام المايك أو موقعي الحالي أو الضغط على الخريطة." if language == "ar" else "Please set both start and destination.",
                "parsed": parsed,
            }
        try:
            origin = self.resolve_location(origin_value, field_name="start")
            destination = self.resolve_location(destination_value, field_name="destination")
        except ValueError as exc:
            return {"status": "input_error", "message": str(exc), "parsed": parsed}

        departure = self._parse_departure(payload.get("departure_time") or parsed.get("departure_time"))
        cache_key = json.dumps({
            "origin": asdict(origin), "destination": asdict(destination),
            "departure": departure.isoformat(timespec="minutes"), "language": language,
        }, sort_keys=True, ensure_ascii=False)
        if cache_key in self._cache:
            cached = json.loads(json.dumps(self._cache[cache_key]))
            cached["cache_hit"] = True
            return cached

        result = self._find_best_saving_route(origin=origin, destination=destination, departure=departure)
        if result.get("status") != "ok":
            fallback = self._fallback(origin, destination, language)
            self._cache[cache_key] = fallback
            return fallback
        enriched = self._enrich_result(result, origin, destination, priority, landmark_mode, language)
        enriched["origin"] = asdict(origin)
        enriched["destination"] = asdict(destination)
        enriched["parsed"] = parsed
        enriched["cache_hit"] = False
        self._cache[cache_key] = json.loads(json.dumps(enriched))
        return enriched

    def _find_best_saving_route(self, *, origin: ResolvedLocation, destination: ResolvedLocation, departure: datetime) -> dict[str, Any]:
        """
        Savings-only routing with a realistic first-mile rule.

        The old MVP allowed the transit router to silently add a long walking leg from
        the user's exact GPS point to any stop inside a large radius. That felt wrong in
        the UI, because the user read it as "the bus passes near me".

        This version first checks whether a public-transport route is actually close to
        the user. If not, it searches for the nearest usable boarding station that can
        connect to the destination, then explicitly explains:
          1) how far that station is from the user,
          2) how long it takes by walking,
          3) how long it roughly takes by car,
          4) what bus route to take after reaching the station.
        """
        near_candidates = self._route_candidates_from_point(
            origin=origin,
            destination=destination,
            departure=departure,
            access_walk_radius_m=NEAR_ROUTE_ACCESS_RADIUS_M,
            egress_walk_radius_m=2600.0,
            direct_walk_limit_m=900.0,
        )
        if near_candidates:
            best_near = min(near_candidates, key=lambda r: r["route_score"])
            # If the first public-transport stop is close enough, return it normally.
            first_walk_m = self._first_leg_walk_distance(best_near, origin, destination)
            if first_walk_m <= NEAR_ROUTE_ACCESS_RADIUS_M:
                # Even when the station is close, show the first-mile data explicitly:
                # distance, walking time, and car time to reach the boarding stop.
                self._promote_first_walk_to_station_access(best_near, origin, destination)
                best_near["access_strategy"] = "nearby_transit_stop"
                return best_near

        via_station = self._best_route_via_nearest_usable_station(origin=origin, destination=destination, departure=departure)
        if via_station.get("status") == "ok":
            return via_station

        # Last attempt: allow the old wider radius, but still mark the first leg as an
        # explicit station access leg so the user sees the stop access time clearly.
        wide_candidates = self._route_candidates_from_point(
            origin=origin,
            destination=destination,
            departure=departure,
            access_walk_radius_m=2600.0,
            egress_walk_radius_m=2600.0,
            direct_walk_limit_m=900.0,
        )
        if wide_candidates:
            best_wide = min(wide_candidates, key=lambda r: r["route_score"])
            self._promote_first_walk_to_station_access(best_wide, origin, destination)
            best_wide["access_strategy"] = "wide_radius_station_access"
            return best_wide

        return {"status": "no_route_found", "reason": "لا يوجد مسار ضمن بيانات الباص الحالية."}

    def _route_candidates_from_point(
        self,
        *,
        origin: ResolvedLocation,
        destination: ResolvedLocation,
        departure: datetime,
        access_walk_radius_m: float,
        egress_walk_radius_m: float,
        direct_walk_limit_m: float,
    ) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        seen: set[str] = set()
        for max_rides in range(0, 5):
            result = find_optimal_brt_route(
                origin=origin.point(), destination=destination.point(), departure_datetime=departure,
                data=self.data, origin_name=origin.name, destination_name=destination.name,
                max_bus_rides=max_rides, access_walk_radius_m=access_walk_radius_m, egress_walk_radius_m=egress_walk_radius_m,
                transfer_buffer_s=60, arrival_tolerance_s=0, direct_walk_limit_m=direct_walk_limit_m,
                timezone_name="Asia/Amman",
            )
            if result.get("status") != "ok":
                continue
            if int(result.get("bus_rides", 0)) == 0:
                direct_walk_m = self._estimate_walking_distance(result, origin, destination)
                if direct_walk_m > max(25.0, direct_walk_limit_m):
                    continue
            signature = json.dumps([(leg.get("mode"), leg.get("route_id"), leg.get("from_name"), leg.get("to_name")) for leg in result.get("legs", [])], sort_keys=True, ensure_ascii=False)
            if signature in seen:
                continue
            seen.add(signature)
            fare = self._estimate_fare(result)
            walk_m = self._estimate_walking_distance(result, origin, destination)
            time_min = float(result.get("total_duration_minutes", 0.0))
            transfers = int(result.get("transfers", 0))
            score = fare * 10000 + walk_m * 0.8 + transfers * 450 + time_min * 12
            result["fare_jd"] = round(fare, 2)
            result["route_score"] = round(score, 2)
            result["score_mode"] = "lowest_cost"
            result["max_bus_rides_scanned"] = max_rides
            candidates.append(result)
        return candidates

    def _best_route_via_nearest_usable_station(self, *, origin: ResolvedLocation, destination: ResolvedLocation, departure: datetime) -> dict[str, Any]:
        best: dict[str, Any] | None = None
        destination_direct_point = destination.point()
        stops_by_distance = self._stops_by_distance(origin.point(), max_distance_m=MAX_BOARDING_SEARCH_M, limit=BOARDING_CANDIDATE_LIMIT)
        for distance_m, stop in stops_by_distance:
            access = self._station_access_advice(origin.point(), stop)
            # The baseline calculation assumes the user walks to the station because this
            # is savings mode. We still show the car time as information, not as a private
            # transport option.
            station_departure = departure + self._seconds_delta(access["walk_seconds"])
            station_origin = ResolvedLocation(name=stop.name, lat=stop.lat, lon=stop.lon, stop_id=stop.id, matched_by="nearest_usable_station")
            direct_candidates = self._direct_stop_to_stop_candidates(stop, destination, station_departure)
            candidates = self._route_candidates_from_point(
                origin=station_origin,
                destination=destination,
                departure=station_departure,
                access_walk_radius_m=90.0,
                egress_walk_radius_m=2600.0,
                direct_walk_limit_m=0.0,
            )
            if direct_candidates:
                candidates.extend(direct_candidates)
            if not candidates:
                # For destinations far from the graph, try to route between the selected
                # boarding station and a destination-side station, then add an egress walk.
                best_dest_stop = self._nearest_usable_destination_stop(destination_direct_point, station_origin, station_departure)
                if best_dest_stop is not None:
                    candidates = [best_dest_stop]
            if not candidates:
                continue
            route = min(candidates, key=lambda r: r["route_score"])
            if not any(leg.get("mode") == "bus" for leg in route.get("legs", [])):
                continue
            route = json.loads(json.dumps(route, ensure_ascii=False))
            self._strip_zero_station_walk(route, stop)
            self._prepend_station_access_leg(route, origin, stop, access, departure)
            route["access_to_first_stop"] = access
            route["access_strategy"] = "nearest_usable_boarding_station"
            route["boarding_station_selected"] = {k: access[k] for k in ["stop_id", "name", "lat", "lon", "distance_m", "walk_minutes", "car_minutes", "recommended_access_mode"]}
            # If the user has a car or can get dropped off at the station, show the
            # same public-transit plan with an estimated car first-mile instead of walking.
            route["car_access_to_station_estimate"] = self._car_access_summary(route, access)
            access["car_to_station_then_bus"] = route["car_access_to_station_estimate"]
            fare = self._estimate_fare(route)
            walking_m = access["distance_m"] + self._estimate_walking_distance(route, origin, destination)
            time_min = float(route.get("total_duration_minutes", 0.0))
            transfers = int(route.get("transfers", 0))
            # Keep fare dominant, then prefer the closest station that actually connects.
            route["fare_jd"] = round(fare, 2)
            route["route_score"] = round(fare * 10000 + distance_m * 0.55 + transfers * 450 + time_min * 12 + walking_m * 0.1, 2)
            route["score_mode"] = "nearest_usable_station_then_lowest_cost"
            # Stops are scanned by physical distance from the user. The first valid one is
            # the nearest station that can actually connect to the destination.
            return route
        return {"status": "no_route_found", "reason": "لا توجد محطة قريبة يمكنها الوصول للوجهة ضمن الداتا الحالية."}

    @staticmethod
    def _seconds_delta(seconds: int):
        from datetime import timedelta
        return timedelta(seconds=int(seconds))

    def _direct_stop_to_stop_candidates(self, origin_stop: Stop, destination: ResolvedLocation, departure: datetime) -> list[dict[str, Any]]:
        """Cheapest direct bus candidates between two known stops.

        RAPTOR returns the earliest-arrival journey. In savings mode, a slightly slower
        direct bus with a lower fare can be the better answer. This helper adds those
        direct same-line alternatives when both the boarding station and destination stop
        are known.
        """
        if not destination.stop_id or destination.stop_id not in self.data.stops:
            return []
        dest_stop_id = destination.stop_id
        if dest_stop_id == origin_stop.id:
            return []
        local = departure.astimezone(AMMAN_TZ) if departure.tzinfo else departure.replace(tzinfo=AMMAN_TZ)
        service_date = local.date()
        ready_seconds = local.hour * 3600 + local.minute * 60 + local.second
        weekday = local.weekday()
        candidates: list[dict[str, Any]] = []
        for route_id in self.data.routes_by_stop.get(origin_stop.id, []):
            route = self.data.routes.get(route_id)
            if not route or dest_stop_id not in route.stop_ids:
                continue
            try:
                i = route.stop_ids.index(origin_stop.id)
                j = route.stop_ids.index(dest_stop_id)
            except ValueError:
                continue
            if i >= j:
                continue
            trip_info = self.data.first_trip_after(route_id, origin_stop.id, ready_seconds, weekday)
            if not trip_info:
                continue
            trip_id, departure_seconds = trip_info
            arrival_seconds = self.data.arrival(trip_id, dest_stop_id)
            if arrival_seconds is None or arrival_seconds < departure_seconds:
                continue
            meta = self.route_meta.get(route_id)
            fare = meta.fare_jd if meta else 0.0
            wait_min = max(0, departure_seconds - ready_seconds) / 60.0
            duration_min = round((arrival_seconds - departure_seconds) / 60.0, 1)
            total_min = round((arrival_seconds - ready_seconds) / 60.0, 1)
            dest_stop = self.data.stops[dest_stop_id]
            result = {
                "status": "ok",
                "departure_time": self._service_time_string(service_date, ready_seconds),
                "arrival_time": self._service_time_string(service_date, arrival_seconds),
                "total_duration_minutes": total_min,
                "bus_rides": 1,
                "transfers": 0,
                "walking_minutes": 0.0,
                "waiting_minutes": round(wait_min, 1),
                "fare_jd": round(fare, 2),
                "route_score": round(fare * 10000 + total_min * 12, 2),
                "score_mode": "direct_same_line_lowest_cost",
                "legs": [{
                    "mode": "bus",
                    "route_id": route_id,
                    "route_name": route.name,
                    "trip_id": trip_id,
                    "from_name": origin_stop.name,
                    "to_name": dest_stop.name,
                    "departure_time": self._service_time_string(service_date, departure_seconds),
                    "arrival_time": self._service_time_string(service_date, arrival_seconds),
                    "duration_minutes": duration_min,
                }],
            }
            candidates.append(result)
        return candidates

    @staticmethod
    def _service_time_string(service_date, seconds: int) -> str:
        return (datetime.combine(service_date, time(0, 0), tzinfo=AMMAN_TZ) + timedelta(seconds=int(seconds))).strftime("%Y-%m-%d %H:%M:%S")

    def _nearest_usable_destination_stop(self, destination_point: tuple[float, float], station_origin: ResolvedLocation, departure: datetime) -> dict[str, Any] | None:
        # Try a small number of destination-side stops. This is a fallback for places that
        # are not within the normal egress radius of a route but still have a nearby stop.
        best: dict[str, Any] | None = None
        for distance_m, dest_stop in self._stops_by_distance(destination_point, max_distance_m=MAX_BOARDING_SEARCH_M, limit=10):
            dest_loc = ResolvedLocation(name=dest_stop.name, lat=dest_stop.lat, lon=dest_stop.lon, stop_id=dest_stop.id, matched_by="nearest_destination_station")
            candidates = self._route_candidates_from_point(
                origin=station_origin,
                destination=dest_loc,
                departure=departure,
                access_walk_radius_m=90.0,
                egress_walk_radius_m=90.0,
                direct_walk_limit_m=0.0,
            )
            if not candidates:
                continue
            route = min(candidates, key=lambda r: r["route_score"])
            if not any(leg.get("mode") == "bus" for leg in route.get("legs", [])):
                continue
            route = json.loads(json.dumps(route, ensure_ascii=False))
            egress = self._station_egress_advice(destination_point, dest_stop)
            self._append_station_egress_leg(route, dest_stop, egress)
            route["egress_from_last_stop"] = egress
            route["route_score"] = float(route.get("route_score", 0)) + distance_m * 0.35
            if best is None or route["route_score"] < best["route_score"]:
                best = route
        return best

    def _stops_by_distance(self, point: tuple[float, float], *, max_distance_m: float, limit: int) -> list[tuple[float, Stop]]:
        rows: list[tuple[float, Stop]] = []
        for stop in self.data.stops.values():
            dist = haversine_m(point, (stop.lat, stop.lon))
            if dist <= max_distance_m:
                rows.append((dist, stop))
        rows.sort(key=lambda item: item[0])
        return rows[:limit]

    def _station_access_advice(self, origin_point: tuple[float, float], stop: Stop) -> dict[str, Any]:
        dist = haversine_m(origin_point, (stop.lat, stop.lon))
        walk_seconds = int(round(dist / WALKING_SPEED_MPS))
        car_seconds = self._estimate_car_access_seconds(dist)
        distance_int = int(round(dist))
        recommend_walk = distance_int <= WALK_TO_STOP_DISTANCE_THRESHOLD_M
        walk_min = round(walk_seconds / 60.0, 1)
        car_min = round(car_seconds / 60.0, 1)
        return {
            "stop_id": stop.id,
            "name": stop.name,
            "lat": stop.lat,
            "lon": stop.lon,
            "distance_m": distance_int,
            "walk_seconds": walk_seconds,
            "walk_minutes": walk_min,
            "car_seconds": car_seconds,
            "car_minutes": car_min,
            "car_distance_m": distance_int,
            "recommended_access_mode": "walk" if recommend_walk else "car_recommended",
            "label_ar": (
                f"المحطة قريبة: {distance_int} متر، يعني كيلو أو أقل. الأفضل تمشي للمحطة عشان توفر."
                if recommend_walk else
                f"المحطة تبعد {distance_int} متر، وهذا أكثر من كيلو. بنصحك تروح بسيارة من موقعك إلى المحطة ثم تكمل بالباص."
            ),
            "label_en": (
                f"The station is {distance_int} m away, 1 km or less. Walking is recommended to save cost."
                if recommend_walk else
                f"The station is {distance_int} m away, more than 1 km. Consider going by car/drop-off to the station, then continue by bus."
            ),
            "walk_option_ar": f"المسافة إلى المحطة: {distance_int} متر، ووقت المشي حوالي {walk_min} دقيقة.",
            "car_option_ar": f"بالسيارة إلى المحطة: حوالي {car_min} دقيقة لنفس المسافة التقريبية {distance_int} متر.",
            "walk_option_en": f"Distance to the station: {distance_int} m, about {walk_min} min walking.",
            "car_option_en": f"Car/drop-off to the station: about {car_min} min for the same approximate {distance_int} m.",
            "station_rating": getattr(stop, "station_rating", None),
        }

    def _station_egress_advice(self, destination_point: tuple[float, float], stop: Stop) -> dict[str, Any]:
        dist = haversine_m((stop.lat, stop.lon), destination_point)
        walk_seconds = int(round(dist / WALKING_SPEED_MPS))
        car_seconds = self._estimate_car_access_seconds(dist)
        distance_int = int(round(dist))
        recommend_walk = distance_int <= WALK_TO_STOP_DISTANCE_THRESHOLD_M
        return {
            "stop_id": stop.id,
            "name": stop.name,
            "lat": stop.lat,
            "lon": stop.lon,
            "distance_m": distance_int,
            "walk_seconds": walk_seconds,
            "walk_minutes": round(walk_seconds / 60.0, 1),
            "car_seconds": car_seconds,
            "car_minutes": round(car_seconds / 60.0, 1),
            "recommended_access_mode": "walk" if recommend_walk else "car_recommended",
            "label_ar": (
                f"من محطة النزول إلى الوجهة: {distance_int} متر، كيلو أو أقل؛ امشِ هذا الجزء لتوفير التكلفة."
                if recommend_walk else
                f"من محطة النزول إلى الوجهة: {distance_int} متر، أكثر من كيلو؛ بنصحك تستخدم سيارة لهذا الجزء الأخير."
            ),
            "label_en": (
                f"From the exit stop to the destination: {distance_int} m, 1 km or less; walking is recommended."
                if recommend_walk else
                f"From the exit stop to the destination: {distance_int} m, more than 1 km; consider car/drop-off for this final leg."
            ),
            "station_rating": getattr(stop, "station_rating", None),
        }

    @staticmethod
    def _estimate_car_access_seconds(distance_m: float) -> int:
        if distance_m <= 35:
            return 0
        return int(round(max(75, distance_m / URBAN_CAR_SPEED_MPS + CAR_ACCESS_BUFFER_S)))

    def _strip_zero_station_walk(self, result: dict[str, Any], stop: Stop) -> None:
        legs = result.get("legs", [])
        while legs:
            first = legs[0]
            if first.get("mode") != "walk":
                break
            same_from = self._normalize(first.get("from_name")) == self._normalize(stop.name)
            same_to = self._normalize(first.get("to_name")) == self._normalize(stop.name)
            tiny = float(first.get("duration_minutes") or 0) <= 0.5
            if tiny and (same_from or same_to):
                legs.pop(0)
            else:
                break
        result["legs"] = legs

    def _prepend_station_access_leg(self, result: dict[str, Any], origin: ResolvedLocation, stop: Stop, access: dict[str, Any], departure: datetime) -> None:
        if access["distance_m"] <= 25:
            return
        start_dt = departure.astimezone(AMMAN_TZ) if departure.tzinfo else departure.replace(tzinfo=AMMAN_TZ)
        end_dt = start_dt + self._seconds_delta(access["walk_seconds"])
        leg = {
            "mode": "walk",
            "is_access_leg": True,
            "from_name": origin.name,
            "to_name": stop.name,
            "departure_time": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "arrival_time": end_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_minutes": round(access["walk_seconds"] / 60.0, 1),
            "distance_m": access["distance_m"],
            "car_seconds": access.get("car_seconds"),
            "car_minutes": access["car_minutes"],
            "car_distance_m": access.get("car_distance_m", access["distance_m"]),
            "recommended_access_mode": access["recommended_access_mode"],
            "access_label_ar": access["label_ar"],
            "access_label_en": access["label_en"],
            "walk_option_ar": access.get("walk_option_ar"),
            "car_option_ar": access.get("car_option_ar"),
            "walk_option_en": access.get("walk_option_en"),
            "car_option_en": access.get("car_option_en"),
            "from_coord": [origin.lat, origin.lon],
            "to_coord": [stop.lat, stop.lon],
            "geometry": [[origin.lat, origin.lon], [stop.lat, stop.lon]],
        }
        result.setdefault("legs", []).insert(0, leg)
        result["total_duration_minutes"] = round(float(result.get("total_duration_minutes", 0.0)) + access["walk_minutes"], 1)
        result["walking_minutes"] = round(float(result.get("walking_minutes", 0.0)) + access["walk_minutes"], 1)

    def _append_station_egress_leg(self, result: dict[str, Any], stop: Stop, egress: dict[str, Any]) -> None:
        if egress["distance_m"] <= 25:
            return
        # Preserve the existing arrival string if possible. This leg is primarily for map
        # and user guidance; exact minute arithmetic is handled in the summary fields.
        leg = {
            "mode": "walk",
            "is_egress_leg": True,
            "from_name": stop.name,
            "to_name": "الوجهة المحددة",
            "departure_time": result.get("arrival_time"),
            "arrival_time": result.get("arrival_time"),
            "duration_minutes": egress["walk_minutes"],
            "distance_m": egress["distance_m"],
            "car_minutes": egress["car_minutes"],
            "recommended_access_mode": egress["recommended_access_mode"],
            "access_label_ar": egress["label_ar"],
            "access_label_en": egress["label_en"],
            "from_coord": [stop.lat, stop.lon],
            "to_coord": None,
            "geometry": [],
        }
        result.setdefault("legs", []).append(leg)
        result["total_duration_minutes"] = round(float(result.get("total_duration_minutes", 0.0)) + egress["walk_minutes"], 1)
        result["walking_minutes"] = round(float(result.get("walking_minutes", 0.0)) + egress["walk_minutes"], 1)

    def _first_leg_walk_distance(self, result: dict[str, Any], origin: ResolvedLocation, destination: ResolvedLocation) -> float:
        for leg in result.get("legs", []):
            if leg.get("mode") == "bus":
                return 0.0
            if leg.get("mode") == "walk":
                a = self._coord_for_name(leg.get("from_name"), origin, destination)
                b = self._coord_for_name(leg.get("to_name"), origin, destination)
                if a and b:
                    return haversine_m(a, b)
        return 0.0

    def _promote_first_walk_to_station_access(self, result: dict[str, Any], origin: ResolvedLocation, destination: ResolvedLocation) -> None:
        legs = result.get("legs", [])
        if not legs or legs[0].get("mode") != "walk":
            return
        first = legs[0]
        to_coord = self._coord_for_name(first.get("to_name"), origin, destination)
        if not to_coord:
            return
        stop_id = None
        norm = self._normalize(first.get("to_name"))
        if norm in self.alias_to_stop:
            stop_id = self.alias_to_stop[norm]
        else:
            for sid, stop in self.data.stops.items():
                if self._normalize(stop.name) == norm:
                    stop_id = sid
                    break
        if not stop_id:
            return
        stop = self.data.stops[stop_id]
        access = self._station_access_advice(origin.point(), stop)
        first["is_access_leg"] = True
        first["distance_m"] = access["distance_m"]
        first["car_seconds"] = access.get("car_seconds")
        first["car_minutes"] = access["car_minutes"]
        first["car_distance_m"] = access.get("car_distance_m", access["distance_m"])
        first["recommended_access_mode"] = access["recommended_access_mode"]
        first["access_label_ar"] = access["label_ar"]
        first["access_label_en"] = access["label_en"]
        first["walk_option_ar"] = access.get("walk_option_ar")
        first["car_option_ar"] = access.get("car_option_ar")
        first["walk_option_en"] = access.get("walk_option_en")
        first["car_option_en"] = access.get("car_option_en")
        result["access_to_first_stop"] = access
        result["boarding_station_selected"] = {k: access[k] for k in ["stop_id", "name", "lat", "lon", "distance_m", "walk_minutes", "car_minutes", "recommended_access_mode"]}


    def _car_access_summary(self, route: dict[str, Any], access: dict[str, Any]) -> dict[str, Any]:
        """Information-only alternative for users who can drive/get dropped off
        at the selected boarding station. This does not add a private vehicle booking mode to
        the route; it only compares first-mile access time to the station.
        """
        walk_min = float(access.get("walk_minutes") or 0.0)
        car_min = float(access.get("car_minutes") or 0.0)
        total_min = float(route.get("total_duration_minutes") or 0.0)
        adjusted_total = max(0.0, total_min - walk_min + car_min)
        first_bus = next((leg for leg in route.get("legs", []) if leg.get("mode") == "bus"), {})
        return {
            "station_name": access.get("name"),
            "station_id": access.get("stop_id"),
            "distance_m": access.get("distance_m"),
            "walk_minutes_to_station": round(walk_min, 1),
            "car_minutes_to_station": round(car_min, 1),
            "estimated_total_minutes_if_car_to_station": round(adjusted_total, 1),
            "public_transport_fare_jd": round(self._estimate_fare(route), 2),
            "first_bus_route_no": first_bus.get("route_no") or first_bus.get("route_id"),
            "first_bus_from": first_bus.get("from_name"),
            "first_bus_to": first_bus.get("to_name"),
            "note_ar": "إذا معك سيارة، استخدمها فقط للوصول للمحطة ثم كمّل بالباص لتوفير التكلفة.",
            "note_en": "If you have a car, use it only to reach the station, then continue by bus to save cost.",
        }

    def _estimate_fare(self, result: dict[str, Any]) -> float:
        total = 0.0
        used_route_ids: set[str] = set()
        for leg in result.get("legs", []):
            route_id = leg.get("route_id")
            if leg.get("mode") == "bus" and route_id:
                # Count each boarding, not unique route. Flat fares may repeat because official tariff is often flat.
                meta = self.route_meta.get(route_id)
                total += meta.fare_jd if meta else 0.0
                used_route_ids.add(route_id)
        return total

    def _estimate_walking_distance(self, result: dict[str, Any], origin: ResolvedLocation, destination: ResolvedLocation) -> float:
        total = 0.0
        for leg in result.get("legs", []):
            if leg.get("mode") != "walk":
                continue
            a = self._coord_for_name(leg.get("from_name"), origin, destination)
            b = self._coord_for_name(leg.get("to_name"), origin, destination)
            if a and b:
                total += haversine_m(a, b)
        return total

    def _enrich_result(self, result: dict[str, Any], origin: ResolvedLocation, destination: ResolvedLocation, priority: str, landmark_mode: bool, language: str) -> dict[str, Any]:
        result = json.loads(json.dumps(result, ensure_ascii=False))
        # Always convert the first walking leg into an explicit station-access leg
        # when the journey uses public transport. This answers: "how do I reach the
        # nearest suitable station if I walk, and how long if I go by car?"
        if any(leg.get("mode") == "bus" for leg in result.get("legs", [])):
            self._promote_first_walk_to_station_access(result, origin, destination)
            if result.get("access_to_first_stop"):
                result["car_access_to_station_estimate"] = self._car_access_summary(result, result["access_to_first_stop"])
                result["access_to_first_stop"]["car_to_station_then_bus"] = result["car_access_to_station_estimate"]
        bus_routes: list[str] = []
        stop_markers: list[dict[str, Any]] = []
        walking_distance_m = 0
        for leg in result.get("legs", []):
            if leg.get("mode") == "bus":
                self._enrich_bus_leg(leg)
                if leg.get("route_id"):
                    bus_routes.append(leg["route_id"])
            else:
                self._enrich_walk_leg(leg, origin, destination)
                walking_distance_m += int(leg.get("distance_m") or 0)
            for key in ["from", "to"]:
                coord_key = f"{key}_coord"
                if leg.get(coord_key):
                    stop_markers.append({"name": leg.get(f"{key}_name"), "lat": leg[coord_key][0], "lon": leg[coord_key][1], "kind": key})
        result["bus_routes"] = sorted(set(bus_routes))
        result["fare_jd"] = round(self._estimate_fare(result), 2)
        result["public_transport_fare_jd"] = result["fare_jd"]
        result["walking_distance_m"] = walking_distance_m
        result["walking_km"] = round(walking_distance_m / 1000.0, 2)
        result["journey_type"] = "walk_only" if not bus_routes else "public_transport_saving"
        result["crowd_warnings"] = [self.feedback.summary(rid) for rid in sorted(set(bus_routes))]
        result["route_quality"] = self._route_quality(bus_routes)
        result["map"] = {
            "origin": {"name": origin.name, "lat": origin.lat, "lon": origin.lon},
            "destination": {"name": destination.name, "lat": destination.lat, "lon": destination.lon},
            "legs": result.get("legs", []), "stop_markers": stop_markers,
        }
        result["nearest"] = {"origin": self._nearest_stop(origin.point()), "destination": self._nearest_stop(destination.point())}
        result["proximity_target"] = self._proximity_target(result, destination)
        result["assistant_text"] = self._assistant_text(result, language)
        result["ai_layer"] = "openai_optional_language_wrapper" if os.getenv("OPENAI_API_KEY") else "local_deterministic_template"
        result["data_notice"] = self.metadata.get("important_note", "")
        return result

    def _enrich_bus_leg(self, leg: dict[str, Any]) -> None:
        route_id = leg.get("route_id")
        meta = self.route_meta.get(route_id) if route_id else None
        if meta:
            leg["route_no"] = meta.route_no
            leg["route_name"] = meta.name
            leg["fare_jd"] = meta.fare_jd
            leg["direction"] = meta.direction
            leg["crowd"] = self.feedback.summary(route_id)
        from_stop_id, to_stop_id = self._infer_leg_stop_ids(leg)
        leg["from_stop_id"] = from_stop_id
        leg["to_stop_id"] = to_stop_id
        if from_stop_id:
            stop = self.data.stops[from_stop_id]
            leg["from_coord"] = [stop.lat, stop.lon]
            leg["from_landmark"] = self.landmarks_ar.get(from_stop_id, stop.name)
            leg["from_station_rating"] = getattr(stop, "station_rating", None)
        if to_stop_id:
            stop = self.data.stops[to_stop_id]
            leg["to_coord"] = [stop.lat, stop.lon]
            leg["to_landmark"] = self.landmarks_ar.get(to_stop_id, stop.name)
            leg["to_station_rating"] = getattr(stop, "station_rating", None)
        geometry: list[list[float]] = []
        via: list[dict[str, Any]] = []
        if route_id and from_stop_id and to_stop_id and route_id in self.data.routes:
            stop_ids = list(self.data.routes[route_id].stop_ids)
            try:
                i, j = stop_ids.index(from_stop_id), stop_ids.index(to_stop_id)
                segment = stop_ids[i:j + 1] if i <= j else stop_ids[j:i + 1]
                geometry = [[self.data.stops[sid].lat, self.data.stops[sid].lon] for sid in segment]
                via = [self._stop_public(sid) for sid in segment]
            except ValueError:
                pass
        leg["geometry"] = geometry
        leg["intermediate_stops"] = via

    def _infer_leg_stop_ids(self, leg: dict[str, Any]) -> tuple[str | None, str | None]:
        route_id = leg.get("route_id")
        if not route_id or route_id not in self.data.routes:
            return None, None
        route = self.data.routes[route_id]
        name_to_ids: dict[str, list[str]] = {}
        for sid in route.stop_ids:
            stop = self.data.stops[sid]
            name_to_ids.setdefault(stop.name, []).append(sid)
        def match(name: str | None) -> str | None:
            if not name:
                return None
            if name in name_to_ids:
                return name_to_ids[name][0]
            norm = self._normalize(name)
            if norm in self.alias_to_stop and self.alias_to_stop[norm] in route.stop_ids:
                return self.alias_to_stop[norm]
            return None
        return match(leg.get("from_name")), match(leg.get("to_name"))

    def _enrich_walk_leg(self, leg: dict[str, Any], origin: ResolvedLocation, destination: ResolvedLocation) -> None:
        from_coord = self._coord_for_name(leg.get("from_name"), origin, destination)
        to_coord = self._coord_for_name(leg.get("to_name"), origin, destination)
        leg["from_coord"] = list(from_coord) if from_coord else None
        leg["to_coord"] = list(to_coord) if to_coord else None
        leg["geometry"] = [list(from_coord), list(to_coord)] if from_coord and to_coord else []
        if from_coord and to_coord:
            dist = haversine_m(from_coord, to_coord)
            distance_int = int(round(dist))
            car_seconds = self._estimate_car_access_seconds(dist)
            recommend_walk = distance_int <= WALK_TO_STOP_DISTANCE_THRESHOLD_M
            leg["distance_m"] = distance_int
            leg["distance_label"] = f"{distance_int} م"
            leg["car_seconds"] = car_seconds
            leg["car_minutes"] = round(car_seconds / 60.0, 1)
            leg["recommended_access_mode"] = "walk" if recommend_walk else "car_recommended"
            leg["access_label_ar"] = (
                f"المسافة {distance_int} متر، كيلو أو أقل؛ الأفضل تمشي هذا الجزء."
                if recommend_walk else
                f"المسافة {distance_int} متر، أكثر من كيلو؛ بنصحك تستخدم سيارة لهذا الجزء."
            )
            leg["access_label_en"] = (
                f"Distance {distance_int} m, 1 km or less; walking is recommended."
                if recommend_walk else
                f"Distance {distance_int} m, more than 1 km; consider car/drop-off for this segment."
            )
            leg["map_hint_ar"] = "سيتم رسم مسار المشي على شوارع OpenStreetMap عند توفر الإنترنت."
            leg["map_hint_en"] = "Walking path is drawn from OpenStreetMap/OSRM when online."

    def _coord_for_name(self, name: str | None, origin: ResolvedLocation, destination: ResolvedLocation) -> tuple[float, float] | None:
        if not name:
            return None
        if name == origin.name or self._normalize(name) == self._normalize(origin.name):
            return origin.point()
        if name == destination.name or self._normalize(name) == self._normalize(destination.name):
            return destination.point()
        norm = self._normalize(name)
        if norm in self.alias_to_stop:
            s = self.data.stops[self.alias_to_stop[norm]]
            return (s.lat, s.lon)
        for stop in self.data.stops.values():
            if stop.name == name or self._normalize(stop.name) == norm:
                return (stop.lat, stop.lon)
        return None

    def _route_quality(self, route_ids: list[str]) -> dict[str, Any]:
        if not route_ids:
            return {"average": None, "label_ar": "رحلة مشي فقط", "label_en": "Walking only"}
        vals = [self.feedback.summary(rid).get("average") for rid in route_ids]
        vals = [v for v in vals if v is not None]
        if not vals:
            return {"average": None, "label_ar": "لا توجد تقييمات كافية", "label_en": "Not enough ratings"}
        avg = round(sum(vals) / len(vals), 1)
        return {"average": avg, "label_ar": "مريح غالبا" if avg >= 4.4 else "متوسط" if avg >= 3.7 else "قد يكون مزدحما", "label_en": "Usually comfortable" if avg >= 4.4 else "Moderate" if avg >= 3.7 else "May be crowded"}

    def _nearest_stop(self, point: tuple[float, float]) -> dict[str, Any]:
        best: tuple[float, Stop] | None = None
        for stop in self.data.stops.values():
            dist = haversine_m(point, (stop.lat, stop.lon))
            if best is None or dist < best[0]:
                best = (dist, stop)
        assert best is not None
        dist, stop = best
        walk_seconds = int(round(dist / WALKING_SPEED_MPS))
        car_seconds = self._estimate_car_access_seconds(dist)
        return {
            "stop_id": stop.id, "name": stop.name, "lat": stop.lat, "lon": stop.lon,
            "distance_m": round(dist), "walk_minutes": round(walk_seconds / 60.0, 1),
            "car_minutes": round(car_seconds / 60.0, 1),
            "recommended_mode": "walk" if round(dist) <= WALK_TO_STOP_DISTANCE_THRESHOLD_M else "car_recommended",
            "label_ar": "امشي للمحطة لأنها كيلو أو أقل" if round(dist) <= WALK_TO_STOP_DISTANCE_THRESHOLD_M else "المحطة أبعد من كيلو؛ بنصحك تروح لها بسيارة ثم تكمل بالباص",
            "label_en": "Walk to the stop because it is 1 km or less" if round(dist) <= WALK_TO_STOP_DISTANCE_THRESHOLD_M else "The stop is more than 1 km away; consider car/drop-off to the stop",
            "station_rating": getattr(stop, "station_rating", None),
        }

    def nearest_stop_from_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            lat = float(payload.get("lat"))
            lon = float(payload.get("lon"))
        except Exception:
            return {"status": "error", "message": "lat/lon required"}
        return {"status": "ok", "nearest": self._nearest_stop((lat, lon))}

    def _proximity_target(self, result: dict[str, Any], destination: ResolvedLocation) -> dict[str, Any] | None:
        bus_legs = [leg for leg in result.get("legs", []) if leg.get("mode") == "bus" and leg.get("to_coord")]
        if not bus_legs:
            return None
        last = bus_legs[-1]
        lat, lon = last["to_coord"]
        return {
            "name": last.get("to_name") or destination.name,
            "lat": lat, "lon": lon, "radius_m": 250,
            "message_ar": f"اقتربت من محطة النزول: {last.get('to_name')}. جهّز حالك للنزول.",
            "message_en": f"You are near your exit stop: {last.get('to_name')}. Get ready to exit.",
        }

    def _assistant_text(self, result: dict[str, Any], language: str) -> str:
        if os.getenv("OPENAI_API_KEY"):
            text = self._optional_ai_text(result, language)
            if text:
                return text
        if language == "en":
            return self._assistant_text_en(result)
        return self._assistant_text_ar(result)

    def _assistant_text_ar(self, result: dict[str, Any]) -> str:
        if result.get("journey_type") == "walk_only":
            return f"أوفر خيار هو المشي مباشرة. المسافة حوالي {result.get('walking_distance_m', 0)} متر، والوقت التقريبي {result.get('total_duration_minutes')} دقيقة، والتكلفة 0 دينار."
        lines = [f"أوفر مسار مقترح بالباص: التكلفة {result.get('fare_jd', 0):.2f} دينار، الوقت التقريبي {result.get('total_duration_minutes')} دقيقة، وإجمالي المشي حوالي {result.get('walking_distance_m', 0)} متر."]
        access = result.get("access_to_first_stop")
        if access:
            if access.get("recommended_access_mode") == "walk":
                lines.append(f"من موقعك، أقرب محطة مناسبة للمسار هي {access.get('name')}. المسافة إليها حوالي {access.get('distance_m')} متر، وهذا كيلو أو أقل. وقت المشي تقريباً {access.get('walk_minutes')} دقيقة، فالأفضل تمشي للمحطة عشان توفر.")
            else:
                car_alt = access.get('car_to_station_then_bus') or {}
                extra = f" لو وصلت للمحطة بالسيارة، الرحلة كاملة قد تصير حوالي {car_alt.get('estimated_total_minutes_if_car_to_station')} دقيقة." if car_alt.get('estimated_total_minutes_if_car_to_station') else ""
                lines.append(f"من موقعك، أقرب محطة مناسبة للمسار هي {access.get('name')}. المسافة التي ستمشيها للمحطة حوالي {access.get('distance_m')} متر، وهذا أكثر من كيلو. بنصحك تروح بسيارة من موقعك إلى {access.get('name')}؛ وقت السيارة التقريبي {access.get('car_minutes')} دقيقة، وبعدها تبدأ رحلة الباص من هناك.{extra}")
        nearest = result.get("nearest", {})
        origin_near = nearest.get("origin")
        if origin_near and not access:
            lines.append(f"أقرب محطة للبداية: {origin_near['name']}، تبعد {origin_near['walk_minutes']} دقيقة مشي، أو تقريباً {origin_near.get('car_minutes', '--')} دقيقة بالسيارة.")
        for i, leg in enumerate(result.get("legs", []), 1):
            if leg.get("mode") == "bus":
                lines.append(f"{i}. اركب خط {leg.get('route_no')} من {leg.get('from_name')} إلى {leg.get('to_name')}، التعرفة {float(leg.get('fare_jd', 0)):.2f} دينار.")
            elif leg.get("is_access_leg"):
                lines.append(f"{i}. اذهب من موقعك إلى محطة {leg.get('to_name')}: مشي {leg.get('duration_minutes')} دقيقة، أو سيارة حوالي {leg.get('car_minutes')} دقيقة.")
            else:
                walk_m = float(leg.get('distance_m') or 0)
                if walk_m > WALK_TO_STOP_DISTANCE_THRESHOLD_M:
                    lines.append(f"{i}. من {leg.get('from_name')} إلى {leg.get('to_name')} المسافة حوالي {leg.get('distance_m', 0)} متر، وهذا أكثر من كيلو؛ بنصحك تستخدم سيارة لهذا الجزء. وقت السيارة التقريبي {leg.get('car_minutes', '--')} دقيقة.")
                else:
                    lines.append(f"{i}. امشِ من {leg.get('from_name')} إلى {leg.get('to_name')} لمسافة {leg.get('distance_m', 0)} متر تقريبا لأنها كيلو أو أقل.")
        return "\n".join(lines)

    def _assistant_text_en(self, result: dict[str, Any]) -> str:
        if result.get("journey_type") == "walk_only":
            return f"The cheapest option is to walk directly: about {result.get('walking_distance_m', 0)} m, {result.get('total_duration_minutes')} min, 0 JD."
        lines = [f"Lowest-cost public-transport route: fare {result.get('fare_jd', 0):.2f} JD, duration {result.get('total_duration_minutes')} min, walking {result.get('walking_distance_m', 0)} m."]
        access = result.get("access_to_first_stop")
        if access:
            if access.get("recommended_access_mode") == "walk":
                lines.append(f"Nearest suitable boarding stop: {access.get('name')}. It is about {access.get('distance_m')} m away, 1 km or less, so walking is recommended. Walking time is about {access.get('walk_minutes')} min.")
            else:
                lines.append(f"Nearest suitable boarding stop: {access.get('name')}. The walk is about {access.get('distance_m')} m, more than 1 km, so consider going by car/drop-off to the station first. Estimated car time is {access.get('car_minutes')} min, then continue by bus.")
        for i, leg in enumerate(result.get("legs", []), 1):
            if leg.get("mode") == "bus":
                lines.append(f"{i}. Take line {leg.get('route_no')} from {leg.get('from_name')} to {leg.get('to_name')}; fare {float(leg.get('fare_jd', 0)):.2f} JD.")
            elif leg.get("is_access_leg"):
                lines.append(f"{i}. Go from your location to {leg.get('to_name')}: {leg.get('duration_minutes')} min walking, or about {leg.get('car_minutes')} min by car.")
            else:
                walk_m = float(leg.get('distance_m') or 0)
                if walk_m > WALK_TO_STOP_DISTANCE_THRESHOLD_M:
                    lines.append(f"{i}. From {leg.get('from_name')} to {leg.get('to_name')}, the remaining distance is about {leg.get('distance_m', 0)} m, more than 1 km; consider car/drop-off for this segment. Estimated car time: {leg.get('car_minutes', '--')} min.")
                else:
                    lines.append(f"{i}. Walk from {leg.get('from_name')} to {leg.get('to_name')} for about {leg.get('distance_m', 0)} m because it is 1 km or less.")
        return "\n".join(lines)

    def _optional_ai_text(self, result: dict[str, Any], language: str) -> str:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            compact = {k: result.get(k) for k in ["fare_jd", "total_duration_minutes", "walking_distance_m", "bus_routes", "legs", "nearest", "access_to_first_stop", "boarding_station_selected"]}
            system = "You are Dellni, a professional public transport assistant. Use ONLY the JSON facts. Do not invent stops, fares, times, or coordinates. No private transport brands. Respond in Arabic only." if language == "ar" else "You are Dellni. Use ONLY the JSON facts. Do not invent stops, fares, times, or coordinates. No private transport brands. Respond in English only."
            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0.2,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": json.dumps(compact, ensure_ascii=False)}],
            )
            return (response.choices[0].message.content or "").strip()
        except Exception:
            return ""


    def ai_chat(self, payload: dict[str, Any]) -> dict[str, Any]:
        language = payload.get("language") or "ar"
        language = "en" if str(language).lower().startswith("en") else "ar"
        message = str(payload.get("message") or payload.get("prompt") or "").strip()
        if not message:
            return {"status": "ok", "assistant_text": self._chat_greeting(language), "route": None}

        parsed = self.parse_prompt(message)
        if parsed.get("origin_text") and parsed.get("destination_text"):
            route_payload = {
                "prompt": message,
                "language": language,
                "departure_time": payload.get("departure_time") or parsed.get("departure_time"),
                "priority": "lowest_cost",
            }
            route = self.route_from_payload(route_payload)
            text = route.get("assistant_text") or route.get("message") or self._chat_greeting(language)
            return {"status": "route", "assistant_text": text, "route": route}

        text = self._optional_ai_chat_text(message, language, payload.get("current_route"))
        if not text:
            text = self._local_chat_text(message, language, payload.get("current_route"))
        return {"status": "ok", "assistant_text": text, "route": None}

    def _chat_greeting(self, language: str) -> str:
        if language == "en":
            return "Hi, I’m Dellni. Tell me your start, destination, and time, and I’ll guide you to the lowest-cost bus route. You can also press the mic and speak."
        return "أهلًا! أنا دلني. احكيلي من وين بدك تطلع، لوين بدك تروح، والساعة كم. إذا المكان مش موجود بالقائمة، بدوّره على الخريطة وبعدين بحسبلك أوفر مسار بالباص وأقرب محطة."

    def _local_chat_text(self, message: str, language: str, current_route: Any = None) -> str:
        norm = self._normalize(message)
        if any(word in norm for word in ["مرحبا", "هلا", "السلام", "اهلا", "هاي", "hello", "hi"]):
            return self._chat_greeting(language)
        if current_route and isinstance(current_route, dict) and current_route.get("status") == "ok":
            access = current_route.get("access_to_first_stop") or {}
            if "سياره" in norm or "سيارة" in message or "car" in norm:
                if access:
                    car_alt = access.get("car_to_station_then_bus") or current_route.get("car_access_to_station_estimate") or {}
                    distance = float(access.get('distance_m') or 0)
                    if distance <= WALK_TO_STOP_DISTANCE_THRESHOLD_M:
                        return (
                            f"أقرب محطة مناسبة هي {access.get('name')}. المسافة حوالي {access.get('distance_m')} متر، يعني كيلو أو أقل، "
                            f"فالأفضل تمشي لها عشان توفر. وقت المشي حوالي {access.get('walk_minutes')} دقيقة."
                        )
                    return (
                        f"إذا معك سيارة: أقرب محطة مناسبة هي {access.get('name')}. المسافة حوالي {access.get('distance_m')} متر، "
                        f"وهذا أكثر من كيلو، فبنصحك تروح بسيارة من موقعك إلى {access.get('name')}. "
                        f"الوقت بالسيارة حوالي {access.get('car_minutes')} دقيقة. بعدها كمّل بالباص، والتكلفة العامة للباص "
                        f"{current_route.get('fare_jd', 0):.2f} دينار. "
                        f"التقدير الكامل إذا وصلت للمحطة بالسيارة: {car_alt.get('estimated_total_minutes_if_car_to_station', current_route.get('total_duration_minutes'))} دقيقة."
                    )
            return "المسار الحالي ظاهر على الخريطة. إذا بدك تعديل، احكيلي مثلًا: من صويلح للعبدلي الساعة ٨، أو اضغط على المايك واحكيها."
        return "تمام. اكتبلي الجملة بهذا الشكل: من [مكان البداية] إلى [الوجهة] الساعة [الوقت]. تقدر تكتب محطة أو معلم مش بالقائمة مثل: من صويلح إلى 42 عمان الساعة ٨، وأنا بدوّر المعلم على الخريطة ثم بحسب أقرب مسار."

    def _optional_ai_chat_text(self, message: str, language: str, current_route: Any = None) -> str:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return ""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            facts = {}
            if isinstance(current_route, dict):
                facts = {k: current_route.get(k) for k in ["fare_jd", "total_duration_minutes", "walking_distance_m", "bus_routes", "access_to_first_stop", "car_access_to_station_estimate", "legs"]}
            system = (
                "You are Dellni, a polished Arabic public-transport assistant for Amman. "
                "Answer in Arabic only unless the user explicitly asks English. "
                "Use only supplied route facts. Never invent stops, routes, fares, coordinates, or live data. "
                "Do not mention private transport brand names. If the user asks for a route and did not give both origin and destination, ask for the missing field. "
                "If car access data exists, explain it only as reaching the station by private car/drop-off, then continuing by bus."
            )
            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                temperature=0.25,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": json.dumps({"message": message, "route_facts": facts}, ensure_ascii=False)},
                ],
            )
            return (response.choices[0].message.content or "").strip()
        except Exception:
            return ""

    def _fallback(self, origin: ResolvedLocation, destination: ResolvedLocation, language: str) -> dict[str, Any]:
        nearest_origin = self._nearest_stop(origin.point())
        nearest_dest = self._nearest_stop(destination.point())
        direct_distance = haversine_m(origin.point(), destination.point())
        walk_seconds = int(round(direct_distance / WALKING_SPEED_MPS))
        car_seconds = self._estimate_car_access_seconds(direct_distance)
        if language == "en":
            text = (
                f"I could not find a complete bus route in the current dataset. "
                f"Nearest start stop: {nearest_origin['name']} ({nearest_origin['walk_minutes']} min walking, "
                f"about {nearest_origin.get('car_minutes')} min by car). "
                f"Nearest destination-side stop: {nearest_dest['name']} ({nearest_dest['walk_minutes']} min walking)."
            )
        else:
            text = (
                f"لم أجد مسارا كاملا ضمن بيانات الباص الحالية. أقرب محطة للبداية هي {nearest_origin['name']}، "
                f"وتبعد {nearest_origin['distance_m']} متر: مشي {nearest_origin['walk_minutes']} دقيقة، "
                f"أو حوالي {nearest_origin.get('car_minutes')} دقيقة بالسيارة. أقرب محطة للوجهة هي {nearest_dest['name']} "
                f"وتبعد {nearest_dest['walk_minutes']} دقيقة مشي."
            )
        return {
            "status": "no_route_found",
            "message": text,
            "assistant_text": text,
            "origin": asdict(origin), "destination": asdict(destination),
            "nearest": {"origin": nearest_origin, "destination": nearest_dest},
            "direct_walk": {"distance_m": round(direct_distance), "walk_minutes": round(walk_seconds / 60.0, 1), "car_minutes": round(car_seconds / 60.0, 1), "recommended": walk_seconds <= WALK_TO_STOP_THRESHOLD_S},
        }

    def submit_crowd_feedback(self, route_id: str, rating: int, note: str = "") -> dict[str, Any]:
        if route_id not in self.route_meta:
            return {"status": "error", "message": "Unknown route_id"}
        return {"status": "ok", "summary": self.feedback.add_rating(route_id, rating, note)}

    def submit_trip_feedback(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.trip_feedback.add(payload)
