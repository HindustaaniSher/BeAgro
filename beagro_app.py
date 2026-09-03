from flask import Flask, jsonify, render_template, request, Response, send_file


import csv
import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet

from app.database import get_connection, init_db
from app.simulation import FarmSimulation
from app.recommendations import (
    analyze_zone,
    generate_recommendations
)
from app.ml_model import (
    predict_crop_health,
    get_ml_metrics
)


app = Flask(__name__)

simulation = FarmSimulation()


# =========================================================
# SAVE FARM DATA
# =========================================================

def save_farm_data(data):

    connection = get_connection()

    # Save overall farm reading
    connection.execute(
        """
        INSERT INTO farm_readings (
            soil_moisture,
            temperature,
            humidity,
            soil_ph,
            rainfall_probability,
            crop_health,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["soil_moisture"],
            data["temperature"],
            data["humidity"],
            data["soil_ph"],
            data["rainfall_probability"],
            data["crop_health"],
            data["updated_at"],
        ),
    )

    # Save individual zone readings
    for zone in data["zones"]:

        connection.execute(
            """
            INSERT INTO zone_readings (
                zone_name,
                soil_moisture,
                crop_health,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                zone["name"],
                zone["moisture"],
                zone["health"],
                data["updated_at"],
            ),
        )

    connection.commit()
    connection.close()


# =========================================================
# HOME
# =========================================================

@app.route("/")
def index():

    return render_template("index.html")


# =========================================================
# FARM DATA
# =========================================================

@app.route("/api/farm-data")
def farm_data():

    data = simulation.update()

    save_farm_data(data)

    return jsonify(data)


# =========================================================
# IRRIGATION
# =========================================================

@app.route(
    "/api/irrigate/<zone_name>",
    methods=["POST"]
)
def irrigate(zone_name):

    data = simulation.irrigate_zone(
        zone_name
    )

    if data is None:

        return jsonify({
            "success": False,
            "message": "Zone not found"
        }), 404


    save_farm_data(data)


    connection = get_connection()

    connection.execute(
        """
        INSERT INTO irrigation_events (
            zone_name,
            water_used_litres,
            created_at
        )
        VALUES (?, ?, ?)
        """,
        (
            zone_name,
            20.0,
            data["updated_at"]
        )
    )


    connection.commit()
    connection.close()


    return jsonify({

        "success": True,

        "message":
            f"{zone_name} irrigated successfully",

        "water_used_litres":
            20.0,

        "data":
            data
    })


# =========================================================
# RECOMMENDATIONS
# =========================================================

@app.route("/api/recommendations")
def recommendations():

    state = simulation.get_state()


    recommendations = generate_recommendations(
        state["zones"],
        state["rainfall_probability"]
    )


    return jsonify({

        "recommendations":
            recommendations,

        "count":
            len(recommendations),

        "rainfall_probability":
            state["rainfall_probability"]

    })


# =========================================================
# FARM HISTORY
# =========================================================

@app.route("/api/history")
def history():

    connection = get_connection()


    rows = connection.execute(
        """
        SELECT *
        FROM farm_readings
        ORDER BY id DESC
        LIMIT 20
        """
    ).fetchall()


    connection.close()


    return jsonify([
        dict(row)
        for row in rows
    ])


# =========================================================
# IRRIGATION HISTORY
# =========================================================

@app.route("/api/irrigation-history")
def irrigation_history():

    connection = get_connection()


    rows = connection.execute(
        """
        SELECT *
        FROM irrigation_events
        ORDER BY id DESC
        LIMIT 50
        """
    ).fetchall()


    connection.close()


    return jsonify([
        dict(row)
        for row in rows
    ])


# =========================================================
# ANALYTICS
# =========================================================

@app.route("/api/analytics")
def analytics():

    connection = get_connection()

    # -----------------------------------------------------
    # Total water used
    # -----------------------------------------------------

    total_water = connection.execute(
        """
        SELECT COALESCE(
            SUM(water_used_litres),
            0
        )
        FROM irrigation_events
        """
    ).fetchone()[0]


    # -----------------------------------------------------
    # Total irrigation events
    # -----------------------------------------------------

    total_events = connection.execute(
        """
        SELECT COUNT(*)
        FROM irrigation_events
        """
    ).fetchone()[0]


    # -----------------------------------------------------
    # Most irrigated zone
    # -----------------------------------------------------

    most_irrigated = connection.execute(
        """
        SELECT
            zone_name,
            COUNT(*) AS irrigation_count

        FROM irrigation_events

        GROUP BY zone_name

        ORDER BY irrigation_count DESC

        LIMIT 1
        """
    ).fetchone()


    # -----------------------------------------------------
    # Average farm health
    # -----------------------------------------------------

    average_health = connection.execute(
        """
        SELECT COALESCE(
            AVG(crop_health),
            0
        )
        FROM farm_readings
        """
    ).fetchone()[0]


    # -----------------------------------------------------
    # Average soil moisture
    # -----------------------------------------------------

    average_moisture = connection.execute(
        """
        SELECT COALESCE(
            AVG(soil_moisture),
            0
        )
        FROM farm_readings
        """
    ).fetchone()[0]


    # -----------------------------------------------------
    # Zone performance
    # -----------------------------------------------------

    zone_rows = connection.execute(
        """
        SELECT
            zone_name,
            AVG(soil_moisture) AS avg_moisture,
            AVG(crop_health) AS avg_health,
            COUNT(*) AS readings

        FROM zone_readings

        GROUP BY zone_name

        ORDER BY avg_health DESC
        """
    ).fetchall()


    # -----------------------------------------------------
    # Irrigation by zone
    # -----------------------------------------------------

    irrigation_rows = connection.execute(
        """
        SELECT
            zone_name,
            COUNT(*) AS irrigation_count,
            COALESCE(
                SUM(water_used_litres),
                0
            ) AS water_used

        FROM irrigation_events

        GROUP BY zone_name

        ORDER BY irrigation_count DESC
        """
    ).fetchall()


    connection.close()


    # -----------------------------------------------------
    # Calculate simple water efficiency indicator
    # -----------------------------------------------------

    if total_water > 0:

        water_efficiency = (
            average_health / total_water
        ) * 1000

    else:

        water_efficiency = 0


    return jsonify({

        "total_water_used_litres":
            round(total_water, 2),

        "total_irrigation_events":
            total_events,

        "most_irrigated_zone":
            (
                most_irrigated["zone_name"]
                if most_irrigated
                else None
            ),

        "most_irrigated_count":
            (
                most_irrigated["irrigation_count"]
                if most_irrigated
                else 0
            ),

        "average_crop_health":
            round(average_health, 2),

        "average_soil_moisture":
            round(average_moisture, 2),

        "water_efficiency_index":
            round(water_efficiency, 2),

        "zone_performance":
            [
                {
                    "zone":
                        row["zone_name"],

                    "average_moisture":
                        round(
                            row["avg_moisture"],
                            2
                        ),

                    "average_health":
                        round(
                            row["avg_health"],
                            2
                        ),

                    "readings":
                        row["readings"]
                }

                for row in zone_rows
            ],

        "irrigation_by_zone":
            [
                {
                    "zone":
                        row["zone_name"],

                    "irrigation_count":
                        row["irrigation_count"],

                    "water_used":
                        round(
                            row["water_used"],
                            2
                        )
                }

                for row in irrigation_rows
            ]

    })


# =========================================================
# ML PREDICTION
# =========================================================

@app.route("/api/ml-prediction")
def ml_prediction():

    state = simulation.get_state()


    prediction = predict_crop_health(
        state
    )


    if prediction is None:

        return jsonify({

            "success":
                False,

            "message":
                "Not enough historical data to train the model.",

            "prediction":
                None

        })


    return jsonify({

        "success":
            True,

        "predicted_crop_health":
            prediction,

        "model":
            "Random Forest Regression"

    })

@app.route("/api/ml-metrics")
def ml_metrics():

    metrics = get_ml_metrics()

    if metrics is None:
        return jsonify({
            "success": False,
            "message":
                "At least 20 farm readings are required "
                "for model evaluation."
        })

    return jsonify(metrics)

# =========================================================
# ZONE DETAILS
# =========================================================

@app.route("/api/zone/<zone_name>")
def zone_details(zone_name):

    state = simulation.get_state()


    # Find requested zone
    zone = next(
        (
            item
            for item in state["zones"]
            if item["name"].lower()
            == zone_name.lower()
        ),
        None
    )


    if zone is None:

        return jsonify({

            "success":
                False,

            "message":
                "Zone not found"

        }), 404


    # -----------------------------------------------------
    # Zone history
    # -----------------------------------------------------

    connection = get_connection()


    history_rows = connection.execute(
        """
        SELECT
            id,
            zone_name,
            soil_moisture,
            crop_health,
            created_at

        FROM zone_readings

        WHERE LOWER(zone_name)
            = LOWER(?)

        ORDER BY id DESC

        LIMIT 30
        """,
        (zone_name,)
    ).fetchall()


    # -----------------------------------------------------
    # Zone irrigation history
    # -----------------------------------------------------

    irrigation_rows = connection.execute(
        """
        SELECT
            id,
            zone_name,
            water_used_litres,
            created_at

        FROM irrigation_events

        WHERE LOWER(zone_name)
            = LOWER(?)

        ORDER BY id DESC

        LIMIT 20
        """,
        (zone_name,)
    ).fetchall()


    connection.close()


    # -----------------------------------------------------
    # Recommendation
    # -----------------------------------------------------

    recommendation = analyze_zone(
        zone,
        state["rainfall_probability"]
    )


    # -----------------------------------------------------
    # Zone ML prediction
    # -----------------------------------------------------

    zone_prediction_data = {

        "soil_moisture":
            zone["moisture"],

        "temperature":
            state["temperature"],

        "humidity":
            state["humidity"],

        "soil_ph":
            state["soil_ph"],

        "rainfall_probability":
            state["rainfall_probability"],

        "crop_health":
            zone["health"],

        "zones":
            state["zones"]

    }


    ml_prediction_value = predict_crop_health(
        zone_prediction_data
    )


    # -----------------------------------------------------
    # Response
    # -----------------------------------------------------

    return jsonify({

        "success":
            True,

        "zone":
            zone,

        "temperature":
            state["temperature"],

        "humidity":
            state["humidity"],

        "soil_ph":
            state["soil_ph"],

        "rainfall_probability":
            state["rainfall_probability"],

        "recommendation":
            recommendation,

        "ml_prediction":
            ml_prediction_value,

        "history":
            [
                dict(row)
                for row in history_rows
            ],

        "irrigation_history":
            [
                dict(row)
                for row in irrigation_rows
            ]

    })


# =========================================================
# HEALTH CHECK
# =========================================================



@app.route("/api/scenario", methods=["POST"])
def run_scenario():

    payload = request.get_json(silent=True) or {}

    scenario = payload.get(
        "scenario",
        "normal"
    )

    success = simulation.apply_scenario(
        scenario
    )

    if not success:
        return jsonify({
            "success": False,
            "message": "Unknown scenario."
        }), 400

    data = simulation.get_state()

    save_farm_data(data)

    return jsonify({
        "success": True,
        "scenario": scenario,
        "data": data
    })





def calculate_farm_health(data):
    moisture = float(data.get("soil_moisture", 0))
    crop_health = float(data.get("crop_health", 0))
    temperature = float(data.get("temperature", 0))
    rainfall = float(data.get("rainfall_probability", 0))

    moisture_score = max(
        0,
        100 - abs(moisture - 65) * 1.5
    )

    temperature_score = max(
        0,
        100 - abs(temperature - 28) * 5
    )

    rainfall_score = max(
        0,
        100 - abs(rainfall - 40)
    )

    score = (
        crop_health * 0.45 +
        moisture_score * 0.25 +
        temperature_score * 0.15 +
        rainfall_score * 0.15
    )

    score = max(0, min(100, score))

    if score >= 80:
        status = "Excellent"
    elif score >= 65:
        status = "Good"
    elif score >= 50:
        status = "Moderate"
    else:
        status = "Needs Attention"

    return {
        "score": round(score, 1),
        "status": status
    }

@app.route("/api/farm-health")
def farm_health():

    data = simulation.get_state()

    health = calculate_farm_health(data)

    return jsonify({
        "success": True,
        **health
    })




@app.route("/api/alerts")
def farm_alerts():

    data = simulation.get_state()

    alerts = []

    for zone in data["zones"]:

        moisture = zone["moisture"]
        health = zone["health"]

        if moisture < 30:
            alerts.append({
                "zone": zone["name"],
                "level": "critical",
                "message":
                    "Critical soil moisture detected.",
                "action":
                    "Immediate irrigation recommended."
            })

        elif moisture < 45:
            alerts.append({
                "zone": zone["name"],
                "level": "warning",
                "message":
                    "Low soil moisture detected.",
                "action":
                    "Consider irrigation."
            })

        elif moisture > 85:
            alerts.append({
                "zone": zone["name"],
                "level": "warning",
                "message":
                    "Excessive soil moisture detected.",
                "action":
                    "Avoid irrigation."
            })

        elif health < 50:
            alerts.append({
                "zone": zone["name"],
                "level": "warning",
                "message":
                    "Crop health is below safe level.",
                "action":
                    "Monitor zone closely."
            })

    return jsonify({
        "success": True,
        "count": len(alerts),
        "alerts": alerts
    })




@app.route("/api/export/csv")
def export_csv():

    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            id,
            soil_moisture,
            temperature,
            humidity,
            soil_ph,
            rainfall_probability,
            crop_health,
            created_at
        FROM farm_readings
        ORDER BY id DESC
        """
    ).fetchall()

    connection.close()

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow([
        "ID",
        "Soil Moisture (%)",
        "Temperature (C)",
        "Humidity (%)",
        "Soil pH",
        "Rainfall Probability (%)",
        "Crop Health (%)",
        "Created At"
    ])

    for row in rows:
        writer.writerow([
            row["id"],
            row["soil_moisture"],
            row["temperature"],
            row["humidity"],
            row["soil_ph"],
            row["rainfall_probability"],
            row["crop_health"],
            row["created_at"]
        ])

    response = Response(
        output.getvalue(),
        mimetype="text/csv"
    )

    response.headers["Content-Disposition"] = (
        "attachment; filename=beagro_farm_data.csv"
    )

    return response




@app.route("/api/export/pdf")
def export_pdf():

    data = simulation.get_state()
    health = calculate_farm_health(data)

    buffer = io.BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    story = []

    story.append(
        Paragraph(
            "BeAgro - Digital Twin Farm Report",
            styles["Title"]
        )
    )

    story.append(
        Spacer(1, 12)
    )

    story.append(
        Paragraph(
            "Generated: " +
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            styles["Normal"]
        )
    )

    story.append(
        Spacer(1, 15)
    )

    story.append(
        Paragraph(
            "Farm Health Score: "
            f"{health['score']} / 100 "
            f"({health['status']})",
            styles["Heading2"]
        )
    )

    story.append(
        Spacer(1, 12)
    )

    summary = [
        ["Parameter", "Value"],
        [
            "Soil Moisture",
            f"{data['soil_moisture']}%"
        ],
        [
            "Temperature",
            f"{data['temperature']} C"
        ],
        [
            "Humidity",
            f"{data['humidity']}%"
        ],
        [
            "Soil pH",
            f"{data['soil_ph']}"
        ],
        [
            "Rainfall Probability",
            f"{data['rainfall_probability']}%"
        ],
        [
            "Crop Health",
            f"{data['crop_health']}%"
        ]
    ]

    table = Table(
        summary,
        colWidths=[220, 180]
    )

    table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),
            (
                "PADDING",
                (0, 0),
                (-1, -1),
                6
            )
        ])
    )

    story.append(table)

    story.append(
        Spacer(1, 20)
    )

    story.append(
        Paragraph(
            "Zone Status",
            styles["Heading2"]
        )
    )

    zone_data = [
        [
            "Zone",
            "Moisture",
            "Health"
        ]
    ]

    for zone in data["zones"]:
        zone_data.append([
            zone["name"],
            f"{zone['moisture']}%",
            f"{zone['health']}%"
        ])

    zone_table = Table(
        zone_data,
        colWidths=[150, 150, 150]
    )

    zone_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),
            (
                "PADDING",
                (0, 0),
                (-1, -1),
                6
            )
        ])
    )

    story.append(zone_table)

    story.append(
        Spacer(1, 20)
    )

    story.append(
        Paragraph(
            "This report is generated from simulated "
            "farm data for academic demonstration. "
            "It is not intended for direct real-world "
            "agricultural decision making.",
            styles["Normal"]
        )
    )

    document.build(story)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="beagro_farm_report.pdf",
        mimetype="application/pdf"
    )


@app.route("/health")
def health():

    return jsonify({

        "status":
            "healthy",

        "project":
            "BeAgro"

    })


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    init_db()

    app.run(
        debug=True
    )
