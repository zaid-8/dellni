# Dellni update: car-to-station data + AI chat

## What changed

- Added explicit first-mile station access cards:
  - nearest suitable boarding station
  - walking distance and walking time
  - private-car/drop-off estimated time to the same station
  - estimated total time if the user reaches the station by car, then continues by bus
- Added an AI chat dialog:
  - opens with a greeting
  - accepts typed questions
  - uses browser speech-to-text and writes the recognized speech into the chat box
  - if the user gives a route request, the deterministic backend calculates the route and updates the map
  - if the user asks about the current route, the assistant explains using the route facts only
- Updated logo with a cleaner professional SVG identity.
- Kept the app focused on savings mode and public transport.
- Removed private transport brand names from the UI and docs.

## Architecture rule

AI does not invent routes, stops, fares, timings, or coordinates. Routing and cost calculations still come from the Python backend and JSON transit data. The AI layer is only a conversational interface and explanation layer.
