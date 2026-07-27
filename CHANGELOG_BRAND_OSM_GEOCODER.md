# Brand + OSM Geocoder Update

## Changed

- Added the user-provided Dellni logo to the header, dialog, and favicon.
- Rebuilt the visual theme around the logo colors: deep purple, gold, copper, cream, and white.
- Added map-search fallback in the backend using OpenStreetMap/Nominatim for typed landmarks that are not in the local JSON data.
- Added offline aliases for `42 عمان`, `42 عمّان`, `42 Amman`, `Taj Mall`, `Abdali Mall`, `Mecca Mall`, and `King Hussein Park`.
- Improved Arabic route prompt parsing so `42 عمان` is handled as one location.
- Updated the AI parser prompt to keep unknown place names exactly as the user wrote them, so the backend can geocode and route.

## Important boundary

The geocoder only resolves coordinates. It does not calculate bus routes. The deterministic backend still selects the nearest station, route, timing, walking distance, and fare from the JSON transit network.
