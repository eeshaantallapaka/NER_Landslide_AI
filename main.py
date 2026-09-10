from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import joblib
import os
import requests
from datetime import datetime

app = Flask(__name__)

# ============================================================
# CONFIGURATION
# ============================================================

MODEL_PATH = "landslide_model.pkl"
UPLOAD_FOLDER = "uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024


# ============================================================
# LOAD MACHINE LEARNING MODEL
# ============================================================

try:
    model = joblib.load(MODEL_PATH)
    print("ML model loaded successfully.")
except Exception as e:
    model = None
    print("ERROR loading ML model:", e)


# ============================================================
# RISK LABELS
# ============================================================

RISK_LABELS = {
    0: "LOW",
    1: "MODERATE",
    2: "HIGH",
    3: "CRITICAL"
}


# ============================================================
# ALLOWED MEDIA TYPES
# ============================================================

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "webp",
    "mp4",
    "mov",
    "avi",
    "mkv"
}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# ============================================================
# IN-MEMORY ALERT STORAGE
# ============================================================

alerts = []


# ============================================================
# ROAD CONNECTIVITY DATA
# ============================================================

roads = [
    {
        "id": "RD-001",
        "name": "Shillong–Cherrapunji Road",
        "district": "East Khasi Hills",
        "latitude": 25.28,
        "longitude": 91.73,
        "status": "CRITICAL",
        "score": 92,
        "priority": 1,
        "reason": "High landslide exposure and heavy rainfall",
        "response": "IMMEDIATE"
    },
    {
        "id": "RD-002",
        "name": "Kohima–Imphal Highway",
        "district": "Kohima",
        "latitude": 25.67,
        "longitude": 94.11,
        "status": "CRITICAL",
        "score": 88,
        "priority": 2,
        "reason": "Slope instability and historical landslides",
        "response": "IMMEDIATE"
    },
    {
        "id": "RD-003",
        "name": "Aizawl–Lunglei Road",
        "district": "Aizawl",
        "latitude": 23.73,
        "longitude": 92.72,
        "status": "AT RISK",
        "score": 76,
        "priority": 3,
        "reason": "Steep terrain and saturated soil",
        "response": "HIGH"
    },
    {
        "id": "RD-004",
        "name": "Itanagar–Tawang Road",
        "district": "Itanagar",
        "latitude": 27.08,
        "longitude": 93.62,
        "status": "AT RISK",
        "score": 72,
        "priority": 4,
        "reason": "Mountain terrain and rainfall exposure",
        "response": "HIGH"
    },
    {
        "id": "RD-005",
        "name": "Gangtok–Nathula Road",
        "district": "Gangtok",
        "latitude": 27.33,
        "longitude": 88.61,
        "status": "MONITORED",
        "score": 54,
        "priority": 6,
        "reason": "Moderate slope and rainfall",
        "response": "NORMAL"
    },
    {
        "id": "RD-006",
        "name": "Darjeeling–Siliguri Road",
        "district": "Darjeeling",
        "latitude": 27.04,
        "longitude": 88.26,
        "status": "AT RISK",
        "score": 71,
        "priority": 5,
        "reason": "Steep slopes and recurring rainfall",
        "response": "HIGH"
    },
    {
        "id": "RD-007",
        "name": "Dehradun–Mussoorie Road",
        "district": "Dehradun",
        "latitude": 30.32,
        "longitude": 78.03,
        "status": "AT RISK",
        "score": 69,
        "priority": 7,
        "reason": "Slope instability during rainfall",
        "response": "HIGH"
    },
    {
        "id": "RD-008",
        "name": "Shimla–Manali Highway",
        "district": "Shimla",
        "latitude": 31.10,
        "longitude": 77.17,
        "status": "MONITORED",
        "score": 57,
        "priority": 8,
        "reason": "Mountain terrain under observation",
        "response": "NORMAL"
    },
    {
        "id": "RD-009",
        "name": "Mandi–Kullu Highway",
        "district": "Mandi",
        "latitude": 31.71,
        "longitude": 76.93,
        "status": "AT RISK",
        "score": 73,
        "priority": 4,
        "reason": "Steep slopes and landslide history",
        "response": "HIGH"
    }
]


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def index():
    return render_template("index.html")


# ============================================================
# AI RISK PREDICTION
# ============================================================

@app.route("/predict", methods=["POST"])
def predict():

    try:

        data = request.get_json()

        rainfall = float(data.get("rainfall", 0))
        soil_moisture = float(data.get("soil_moisture", 0))
        slope = float(data.get("slope", 0))
        elevation = float(data.get("elevation", 0))
        historical_landslides = float(
            data.get("historical_landslides", 0)
        )

        location = data.get("location", "Unknown")

        features = pd.DataFrame([{
            "rainfall": rainfall,
            "soil_moisture": soil_moisture,
            "slope": slope,
            "elevation": elevation,
            "historical_landslides": historical_landslides
        }])

        # ----------------------------------------------------
        # MODEL PREDICTION
        # ----------------------------------------------------

        if model is not None:

            prediction = int(model.predict(features)[0])

            probabilities = model.predict_proba(features)[0]

            classes = model.classes_

            probability_map = {}

            for cls, probability in zip(classes, probabilities):
                probability_map[RISK_LABELS[int(cls)]] = round(
                    float(probability) * 100,
                    2
                )

            # Prototype continuous risk score
            risk_score = 0

            for cls, probability in zip(classes, probabilities):
                risk_score += (
                    int(cls) * float(probability) * 33.33
                )

            risk_score = round(
                max(0, min(100, risk_score))
            )

        else:

            # Fallback if model cannot be loaded
            risk_score = min(
                100,
                (
                    rainfall * 0.30
                    + soil_moisture * 0.25
                    + slope * 0.25
                    + historical_landslides * 2
                )
            )

            if risk_score >= 80:
                prediction = 3
            elif risk_score >= 60:
                prediction = 2
            elif risk_score >= 35:
                prediction = 1
            else:
                prediction = 0

            probability_map = {
                "LOW": 0,
                "MODERATE": 0,
                "HIGH": 0,
                "CRITICAL": 0
            }

            probability_map[RISK_LABELS[prediction]] = 100

        risk_level = RISK_LABELS[prediction]

        # ----------------------------------------------------
        # CREATE ALERT FOR HIGH / CRITICAL RISK
        # ----------------------------------------------------

        if risk_level in ["HIGH", "CRITICAL"]:

            alert = {
                "id": len(alerts) + 1,
                "location": location,
                "risk": risk_level,
                "score": risk_score,
                "message": (
                    f"{risk_level} landslide risk detected "
                    f"at {location}"
                ),
                "timestamp": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "status": "ACTIVE"
            }

            alerts.insert(0, alert)

            # Keep latest 50 alerts
            if len(alerts) > 50:
                alerts.pop()

        return jsonify({
            "success": True,
            "risk": risk_level,
            "risk_level": risk_level,
            "class": prediction,
            "risk_score": risk_score,
            "probabilities": probability_map,
            "location": location
        })

    except Exception as e:

        print("Prediction error:", e)

        return jsonify({
            "success": False,
            "error": str(e)
        }), 400


# ============================================================
# LIVE WEATHER
# ============================================================

@app.route("/weather", methods=["GET"])
def weather():

    try:

        # ----------------------------------------------------
        # IMPORTANT:
        # Support BOTH parameter formats.
        #
        # latitude / longitude
        # AND
        # lat / lng
        #
        # This fixes the frontend/backend mismatch.
        # ----------------------------------------------------

        latitude = request.args.get("latitude")

        longitude = request.args.get("longitude")

        if latitude is None:
            latitude = request.args.get("lat")

        if longitude is None:
            longitude = request.args.get("lng")

        # Default location: Dehradun
        if latitude is None:
            latitude = 30.32

        if longitude is None:
            longitude = 78.03

        latitude = float(latitude)
        longitude = float(longitude)

        # ----------------------------------------------------
        # OPEN-METEO REQUEST
        # ----------------------------------------------------

        url = "https://api.open-meteo.com/v1/forecast"

        params = {
            "latitude": latitude,
            "longitude": longitude,

            "current": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "apparent_temperature,"
                "precipitation,"
                "rain,"
                "weather_code,"
                "wind_speed_10m"
            ),

            "hourly": (
                "precipitation,"
                "rain,"
                "soil_moisture_0_to_10cm"
            ),

            "forecast_days": 2,

            "timezone": "auto"
        }

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        api_data = response.json()

        current = api_data.get("current", {})
        hourly = api_data.get("hourly", {})

        # ----------------------------------------------------
        # CURRENT VALUES
        # ----------------------------------------------------

        temperature = current.get("temperature_2m")

        humidity = current.get("relative_humidity_2m")

        apparent_temperature = current.get(
            "apparent_temperature"
        )

        precipitation = current.get("precipitation", 0)

        rain = current.get("rain", 0)

        wind_speed = current.get("wind_speed_10m")

        weather_code = current.get("weather_code")

        # ----------------------------------------------------
        # SOIL MOISTURE
        # ----------------------------------------------------

        soil_values = hourly.get(
            "soil_moisture_0_to_10cm",
            []
        )

        if soil_values:
            soil_moisture = soil_values[0]
        else:
            soil_moisture = None

        # ----------------------------------------------------
        # 24-HOUR RAINFALL
        # ----------------------------------------------------

        precipitation_values = hourly.get(
            "precipitation",
            []
        )

        rain_24h = sum(
            float(value or 0)
            for value in precipitation_values[:24]
        )

        # ----------------------------------------------------
        # 24-HOUR RAIN
        # ----------------------------------------------------

        rain_values = hourly.get(
            "rain",
            []
        )

        rain_24h_actual = sum(
            float(value or 0)
            for value in rain_values[:24]
        )

        # ----------------------------------------------------
        # WEATHER CODE DESCRIPTION
        # ----------------------------------------------------

        weather_description = get_weather_description(
            weather_code
        )

        # ----------------------------------------------------
        # RESPONSE
        #
        # We return BOTH:
        #
        # 1. Flat fields
        # 2. Nested current object
        #
        # So the current frontend works without changing it.
        # ----------------------------------------------------

        weather_data = {

            "success": True,

            "source": "Open-Meteo",

            "live": True,

            "latitude": latitude,

            "longitude": longitude,

            # Flat values
            "temperature": temperature,
            "humidity": humidity,
            "apparent_temperature": apparent_temperature,
            "rainfall": precipitation,
            "rain": rain,
            "wind": wind_speed,
            "wind_speed": wind_speed,
            "soil_moisture": soil_moisture,
            "weather_code": weather_code,
            "weather_description": weather_description,

            "rainfall_24h": round(
                rain_24h,
                2
            ),

            "rain_24h": round(
                rain_24h_actual,
                2
            ),

            # Nested structure
            "current": {
                "temperature_2m": temperature,
                "relative_humidity_2m": humidity,
                "apparent_temperature": apparent_temperature,
                "precipitation": precipitation,
                "rain": rain,
                "wind_speed_10m": wind_speed,
                "weather_code": weather_code,
                "soil_moisture_0_to_10cm": soil_moisture
            },

            "hourly": {
                "precipitation": precipitation_values,
                "rain": rain_values,
                "soil_moisture_0_to_10cm": soil_values
            }

        }

        print(
            f"Weather LIVE: "
            f"{latitude}, {longitude} | "
            f"{temperature}°C | "
            f"Rain: {precipitation} mm | "
            f"Soil: {soil_moisture}"
        )

        return jsonify(weather_data)

    except requests.exceptions.RequestException as e:

        print("Open-Meteo connection error:", e)

        return jsonify({
            "success": False,
            "live": False,
            "error": "Unable to connect to Open-Meteo",
            "message": str(e)
        }), 503

    except Exception as e:

        print("Weather error:", e)

        return jsonify({
            "success": False,
            "live": False,
            "error": str(e)
        }), 500


# ============================================================
# WEATHER DESCRIPTION
# ============================================================

def get_weather_description(code):

    descriptions = {

        0: "Clear sky",

        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",

        45: "Fog",
        48: "Depositing rime fog",

        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",

        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",

        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",

        66: "Light freezing rain",
        67: "Heavy freezing rain",

        71: "Slight snowfall",
        73: "Moderate snowfall",
        75: "Heavy snowfall",

        77: "Snow grains",

        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",

        85: "Slight snow showers",
        86: "Heavy snow showers",

        95: "Thunderstorm",

        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail"
    }

    return descriptions.get(
        code,
        "Unknown conditions"
    )


# ============================================================
# ALERTS
# ============================================================

@app.route("/alerts", methods=["GET"])
def get_alerts():

    return jsonify({
        "success": True,
        "alerts": alerts,
        "count": len(alerts)
    })


# ============================================================
# RESOLVE ALERT
# ============================================================

@app.route(
    "/alerts/<int:alert_id>/resolve",
    methods=["POST"]
)
def resolve_alert(alert_id):

    for alert in alerts:

        if alert["id"] == alert_id:

            alert["status"] = "RESOLVED"

            return jsonify({
                "success": True,
                "message": "Alert resolved",
                "alert": alert
            })

    return jsonify({
        "success": False,
        "message": "Alert not found"
    }), 404


# ============================================================
# ROAD CONNECTIVITY
# ============================================================

@app.route("/roads", methods=["GET"])
def get_roads():

    sorted_roads = sorted(
        roads,
        key=lambda x: x["priority"]
    )

    critical = sum(
        1
        for road in roads
        if road["status"] == "CRITICAL"
    )

    at_risk = sum(
        1
        for road in roads
        if road["status"] == "AT RISK"
    )

    monitored = sum(
        1
        for road in roads
        if road["status"] == "MONITORED"
    )

    return jsonify({

        "success": True,

        "roads": sorted_roads,

        "statistics": {
            "total": len(roads),
            "critical": critical,
            "at_risk": at_risk,
            "monitored": monitored
        }

    })


# ============================================================
# EMERGENCY RESPONSE PRIORITY
# ============================================================

@app.route("/emergency-priority", methods=["GET"])
def emergency_priority():

    priority_roads = sorted(
        roads,
        key=lambda x: (
            x["priority"],
            -x["score"]
        )
    )

    recommendation = (
        "Prioritize immediate response on CRITICAL roads, "
        "followed by AT RISK corridors."
    )

    return jsonify({

        "success": True,

        "priority_roads": priority_roads,

        "recommendation": recommendation

    })


# ============================================================
# CITIZEN / FIELD REPORT
# ============================================================

@app.route("/report", methods=["POST"])
def submit_report():

    try:

        location = request.form.get(
            "location",
            "Unknown"
        )

        latitude = request.form.get(
            "latitude"
        )

        longitude = request.form.get(
            "longitude"
        )

        severity = request.form.get(
            "severity",
            "LOW"
        )

        description = request.form.get(
            "description",
            ""
        )

        media_file = request.files.get(
            "media"
        )

        media_filename = None

        # ----------------------------------------------------
        # SAVE MEDIA
        # ----------------------------------------------------

        if media_file and media_file.filename:

            if not allowed_file(
                media_file.filename
            ):
                return jsonify({
                    "success": False,
                    "error": "Unsupported media type"
                }), 400

            timestamp = datetime.now().strftime(
                "%Y%m%d_%H%M%S"
            )

            original_name = media_file.filename

            safe_name = (
                f"{timestamp}_{original_name}"
            )

            media_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                safe_name
            )

            media_file.save(media_path)

            media_filename = safe_name

        # ----------------------------------------------------
        # CREATE ALERT FOR HIGH / CRITICAL REPORT
        # ----------------------------------------------------

        if severity.upper() in [
            "HIGH",
            "CRITICAL"
        ]:

            alert = {

                "id": len(alerts) + 1,

                "location": location,

                "risk": severity.upper(),

                "score": (
                    90
                    if severity.upper() == "CRITICAL"
                    else 75
                ),

                "message": (
                    f"Citizen/field report: "
                    f"{description}"
                ),

                "timestamp": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),

                "status": "ACTIVE",

                "source": "Citizen / Field Report",

                "latitude": latitude,

                "longitude": longitude

            }

            alerts.insert(
                0,
                alert
            )

        print(
            "Citizen report received:",
            location,
            severity,
            description
        )

        return jsonify({

            "success": True,

            "message": (
                "Report submitted successfully"
            ),

            "report": {

                "location": location,

                "latitude": latitude,

                "longitude": longitude,

                "severity": severity,

                "description": description,

                "media": media_filename

            }

        })

    except Exception as e:

        print("Report error:", e)

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health", methods=["GET"])
def health():

    return jsonify({

        "status": "ONLINE",

        "model": (
            "LOADED"
            if model is not None
            else "UNAVAILABLE"
        ),

        "weather_api": "Open-Meteo",

        "timestamp": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    })


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("NER LANDSLIDE INTELLIGENCE SYSTEM")
    print("=" * 60)

    print(
        "ML Model:",
        "LOADED" if model is not None else "NOT LOADED"
    )

    print(
        "Weather:",
        "Open-Meteo API"
    )

    print(
        "Road monitoring:",
        len(roads),
        "roads"
    )

    print("=" * 60)

    app.run(
        host="0.0.0.0",
        port=5050,
        debug=True
    )