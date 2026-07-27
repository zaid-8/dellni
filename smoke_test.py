from pathlib import Path
from core.route_service import DellniRouteService

BASE = Path(__file__).resolve().parent
service = DellniRouteService(BASE / "data" / "amman_brt_verified_mvp_data.json", BASE / "data" / "crowd_feedback.json")

cases = [
    ("Sweileh to Jordan Museum", {"origin": "صويلح", "destination": "متحف الأردن", "departure_time": "08:00", "language": "ar"}),
    ("University of Jordan to Zarqa", {"origin": "الجامعة الأردنية", "destination": "الزرقاء", "departure_time": "08:05", "language": "ar"}),
    ("Prince Hamza Hospital to Madaba", {"origin": "مستشفى حمزة", "destination": "مادبا", "departure_time": "07:30", "language": "ar"}),
    ("Khalda to Second Circle", {"origin": "خلدا", "destination": "الدوار الثاني", "departure_time": "09:00", "language": "ar"}),
    ("Jubaiha to Abdali by voice", {"prompt": "من الجبيهة للعبدلي الساعة ٨", "language": "ar"}),
    ("Off-route GPS near Sports City to Sweileh", {"origin_coords": {"lat": 31.9945, "lon": 35.9015, "name": "موقع قريب من دوار المدينة"}, "destination": "صويلح", "departure_time": "08:00", "language": "ar"}),
    ("Sweileh to unmapped landmark 42 Amman", {"prompt": "من صويلح إلى 42 عمان الساعة 08:00", "language": "ar"}),
]

for i, (name, payload) in enumerate(cases, 1):
    result = service.route_from_payload(payload)
    print("=" * 72)
    print(f"Case {i}: {name}")
    print("Payload:", payload)
    print("Status:", result.get("status"))
    print("Fare:", result.get("fare_jd"), "Duration:", result.get("total_duration_minutes"), "Walk m:", result.get("walking_distance_m"))
    access = result.get("access_to_first_stop")
    if access:
        print("Access station:", access.get("name"), access.get("distance_m"), "m", access.get("walk_minutes"), "min walk", access.get("car_minutes"), "min car")
    print((result.get("assistant_text") or result.get("message") or "")[:900])

print("=" * 72)
print("AI chat greeting:")
print(service.ai_chat({"message": "مرحبا", "language": "ar"}).get("assistant_text"))
print("=" * 72)
print("AI chat car access question with current route:")
route = service.route_from_payload({"origin_coords": {"lat": 31.9945, "lon": 35.9015, "name": "موقع قريب من دوار المدينة"}, "destination": "صويلح", "departure_time": "08:00", "language": "ar"})
print(service.ai_chat({"message": "لو معي سيارة كيف أوصل لأقرب محطة؟", "language": "ar", "current_route": route}).get("assistant_text"))
