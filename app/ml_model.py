import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from app.database import get_connection


FEATURES = [
    "soil_moisture",
    "temperature",
    "humidity",
    "soil_ph",
    "rainfall_probability"
]


def load_training_data():
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            soil_moisture,
            temperature,
            humidity,
            soil_ph,
            rainfall_probability,
            crop_health
        FROM farm_readings
        ORDER BY id
        """
    ).fetchall()

    connection.close()

    return pd.DataFrame(
        [dict(row) for row in rows]
    )


def build_model():
    return RandomForestRegressor(
        n_estimators=100,
        random_state=42
    )


def train_model():
    data = load_training_data()

    if len(data) < 5:
        return None

    X = data[FEATURES]
    y = data["crop_health"]

    model = build_model()
    model.fit(X, y)

    return model


def evaluate_model():
    data = load_training_data()

    if len(data) < 20:
        return None

    X = data[FEATURES]
    y = data["crop_health"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42
    )

    model = build_model()

    model.fit(
        X_train,
        y_train
    )

    predictions = model.predict(X_test)

    mae = mean_absolute_error(
        y_test,
        predictions
    )

    r2 = r2_score(
        y_test,
        predictions
    )

    return {
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "mae": round(float(mae), 2),
        "r2_score": round(float(r2), 3)
    }


def get_feature_importance():
    data = load_training_data()

    if len(data) < 5:
        return []

    X = data[FEATURES]
    y = data["crop_health"]

    model = build_model()

    model.fit(
        X,
        y
    )

    importance = []

    for feature, value in zip(
        FEATURES,
        model.feature_importances_
    ):
        importance.append({
            "feature": feature,
            "importance": round(
                float(value),
                4
            )
        })

    importance.sort(
        key=lambda item: item["importance"],
        reverse=True
    )

    return importance


def get_ml_metrics():
    data = load_training_data()

    if len(data) < 5:
        return None

    evaluation = evaluate_model()

    return {
        "success": True,
        "model": "Random Forest Regression",
        "total_samples": len(data),
        "evaluation": evaluation,
        "feature_importance":
            get_feature_importance()
    }


def predict_crop_health(sensor_data):
    model = train_model()

    if model is None:
        return None

    input_data = pd.DataFrame(
        [{
            feature: sensor_data[feature]
            for feature in FEATURES
        }]
    )

    prediction = model.predict(
        input_data
    )[0]

    return round(
        max(
            0,
            min(
                100,
                prediction
            )
        ),
        2
    )
