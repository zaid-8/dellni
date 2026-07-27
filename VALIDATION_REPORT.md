# Dellni Validation Report - Professional Submission Build

## Scope

This build focuses on a polished public-transport saving experience:

1. Map-first home screen.
2. Precise browser geolocation with visible accuracy radius.
3. Start/destination selection from map or typed area names.
4. Savings-only optimization.
5. Public transport and walking only.
6. Voice AI entry point.
7. Exit alert at 250 m.
8. Trip rating after the journey.
9. Arabic-first UI with a single header toggle to English.

## Data validation boundary

- Route numbers and fares were checked against published Amman Bus / Vision City Bus tariff documents.
- Selected route timing blocks were aligned with published schedule PDFs where available.
- The Vision City Bus app listing confirms that the official app provides trip planning, current location as starting point, map route, stops, times, fare, and nearest stops.
- No official open GTFS/AVL feed was found for direct live integration; therefore the JSON file remains an MVP dataset.
- Coordinates and stop-to-stop times must be replaced with official open GTFS/AVL data when GAM or the operator provides it.

## AI safety boundary

OpenAI, when configured, is used only to parse or rewrite the user's language. The backend deterministic route engine calculates:

- nearest stops,
- walking time and distance,
- bus route sequence,
- fares,
- arrival estimates,
- exit-alert target.

The AI prompt explicitly forbids inventing stops, fares, times, coordinates, or private transport options.

## Local smoke test examples

- صويلح -> متحف الأردن
- الجامعة الأردنية -> الزرقاء
- مستشفى الأمير حمزة -> مادبا
- خلدا -> الدوار الثاني
- الجبيهة -> العبدلي

## Known production upgrade

For production accuracy, replace `data/amman_brt_verified_mvp_data.json` with an official GTFS feed or approved route/station dataset from the transport operator.


## Route 99 landmark correction
This build expands BRT Route 99 with the major published landmarks used by riders between Sweileh and Jordan Museum: University of Jordan, Sports City, King Abdullah Gardens, Wadi Saqra, Arab Medical Center, Amideast, Ras Al Ain, GAM, and Jordan Museum. It also adds demo aliases for 42 Amman and Al Hussein Cultural Center so queries like "من صويلح إلى 42 عمان" and "من الجامعة الأردنية إلى مركز الحسين الثقافي" return a direct Route 99 journey when appropriate.

## Street-following map lines
The frontend now asks OpenStreetMap/OSRM to draw bus legs along roads instead of drawing only straight lines between stop coordinates. If OSRM is unavailable, the app falls back to the local route geometry.
