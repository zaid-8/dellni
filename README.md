# Dellni / دلني - Professional Submission Build

Dellni is a map-first public-transport route planner for Greater Amman. The user can choose their current location, pick a start and destination on the map, type a place name, or speak to the AI chat. The backend returns the lowest-cost public-transport route, the nearest suitable boarding station, walking distance, estimated private-car/drop-off time to the station, bus legs, fares, and a 250 m exit alert.

## Run on Windows

```powershell
cd "C:\Users\afars\Desktop\dellni_brand_osm_ai_app"
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Optional OpenAI AI layer

The site works without an API key using local parsing and deterministic text templates. To enable the OpenAI language layer:

```powershell
$env:OPENAI_API_KEY="sk-proj-put_your_real_key_here"
$env:OPENAI_MODEL="gpt-4o-mini"
python app.py
```

The AI layer is intentionally bounded. It may extract location text and rewrite the final route in friendly Arabic, but it is not allowed to invent stops, routes, coordinates, fares, or live bus data.

## Try these prompts

```text
من صويلح إلى 42 عمان الساعة 08:00
من 42 عمان إلى صويلح الساعة 08:00
من صويلح للزرقاء الساعة ثمانية
من دوار المدينة إلى صويلح الساعة ٨
من خلدا للدوار الثاني
```

## Data note

This MVP uses a structured JSON dataset for Amman BRT / Amman Bus-style routes, stops, fares, and generated schedules. It is suitable for a hackathon prototype and can be replaced with official GTFS/AVL data later. For unknown landmarks, the app can use OpenStreetMap/Nominatim to find coordinates, then it routes from/to the nearest usable station in the local network.

## Architecture boundary

- Frontend: HTML, CSS, JavaScript, Leaflet, OpenStreetMap tiles.
- Backend: Python Flask.
- Routing core: deterministic RAPTOR-style routing over JSON data.
- AI: language parser + friendly explanation only.
- Geocoding fallback: OpenStreetMap/Nominatim for unknown landmarks only.




## Street-following map lines
The frontend now asks OpenStreetMap/OSRM to draw bus legs along roads instead of drawing only straight lines between stop coordinates. If OSRM is unavailable, the app falls back to the local route geometry.
