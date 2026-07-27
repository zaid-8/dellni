from __future__ import annotations

from pathlib import Path
import os

from flask import Flask, jsonify, render_template, request

from core.route_service import DellniRouteService

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "amman_brt_verified_mvp_data.json"
FEEDBACK_PATH = BASE_DIR / "data" / "crowd_feedback.json"

app = Flask(__name__)
service = DellniRouteService(DATA_PATH, FEEDBACK_PATH, apply_realtime_sample=True)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "dataset": service.metadata,
        "stops": len(service.data.stops),
        "routes": len(service.data.routes),
        "trips": len(service.data.trips),
    })


@app.get("/api/locations")
def locations():
    return jsonify({"locations": service.locations_catalog()})


@app.get("/api/routes")
def routes():
    return jsonify({"routes": service.routes_catalog()})


@app.get("/api/data-quality")
def data_quality():
    return jsonify(service.data_quality())


@app.post("/api/route")
def route():
    payload = request.get_json(silent=True) or {}
    return jsonify(service.route_from_payload(payload))


@app.post("/api/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    return jsonify(service.route_from_payload(payload))


@app.post("/api/nearest-stop")
def nearest_stop():
    payload = request.get_json(silent=True) or {}
    return jsonify(service.nearest_stop_from_payload(payload))


@app.post("/api/ai-chat")
def ai_chat():
    payload = request.get_json(silent=True) or {}
    return jsonify(service.ai_chat(payload))


@app.post("/api/crowd-feedback")
def crowd_feedback():
    payload = request.get_json(silent=True) or {}
    route_id = str(payload.get("route_id", ""))
    rating = int(payload.get("rating", 3))
    note = str(payload.get("note", ""))
    return jsonify(service.submit_crowd_feedback(route_id, rating, note))


@app.post("/api/trip-feedback")
def trip_feedback():
    payload = request.get_json(silent=True) or {}
    return jsonify(service.submit_trip_feedback(payload))


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
