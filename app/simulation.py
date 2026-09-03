import random
from datetime import datetime


class FarmSimulation:
    def __init__(self):
        self.temperature = 31.0
        self.humidity = 58.0
        self.soil_ph = 6.5
        self.rainfall_probability = 35.0

        self.zones = [
            {"name": "Zone A", "moisture": 65.0, "health": 78.0},
            {"name": "Zone B", "moisture": 55.0, "health": 68.0},
            {"name": "Zone C", "moisture": 72.0, "health": 84.0},
            {"name": "Zone D", "moisture": 42.0, "health": 51.0},
            {"name": "Zone E", "moisture": 60.0, "health": 73.0},
            {"name": "Zone F", "moisture": 48.0, "health": 59.0},
            {"name": "Zone G", "moisture": 76.0, "health": 88.0},
            {"name": "Zone H", "moisture": 38.0, "health": 45.0},
        ]

    def update(self):
        self.temperature += random.uniform(-0.5, 0.5)
        self.humidity += random.uniform(-1.5, 1.5)
        self.soil_ph += random.uniform(-0.03, 0.03)
        self.rainfall_probability += random.uniform(-4, 4)

        self.temperature = max(15, min(45, self.temperature))
        self.humidity = max(20, min(95, self.humidity))
        self.soil_ph = max(5.5, min(8.0, self.soil_ph))
        self.rainfall_probability = max(
            0, min(100, self.rainfall_probability)
        )

        for zone in self.zones:
            zone["moisture"] += random.uniform(-2.5, 1.0)
            zone["moisture"] = max(0, min(100, zone["moisture"]))

            if zone["moisture"] < 35:
                zone["health"] -= random.uniform(0.5, 1.5)
            elif zone["moisture"] > 80:
                zone["health"] -= random.uniform(0.1, 0.5)
            else:
                zone["health"] += random.uniform(-0.3, 0.6)

            zone["health"] = max(0, min(100, zone["health"]))

        return self.get_state()

    def irrigate_zone(self, zone_name):
        for zone in self.zones:
            if zone["name"].lower() == zone_name.lower():
                zone["moisture"] = min(100, zone["moisture"] + 18)
                zone["health"] = min(100, zone["health"] + 4)
                return self.get_state()

        return None

    def get_state(self):
        average_moisture = sum(
            zone["moisture"] for zone in self.zones
        ) / len(self.zones)

        average_health = sum(
            zone["health"] for zone in self.zones
        ) / len(self.zones)

        return {
            "soil_moisture": round(average_moisture, 2),
            "temperature": round(self.temperature, 2),
            "humidity": round(self.humidity, 2),
            "soil_ph": round(self.soil_ph, 2),
            "rainfall_probability": round(
                self.rainfall_probability, 2
            ),
            "crop_health": round(average_health, 2),
            "zones": [
                {
                    "name": zone["name"],
                    "moisture": round(zone["moisture"], 2),
                    "health": round(zone["health"], 2),
                }
                for zone in self.zones
            ],
            "updated_at": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }

    def apply_scenario(self, scenario):
        scenario = scenario.lower().strip()

        if scenario == "normal":
            self.temperature = 31.0
            self.humidity = 58.0
            self.rainfall_probability = 35.0

            moisture_targets = [
                65, 55, 72, 42,
                60, 48, 76, 38
            ]

        elif scenario == "heatwave":
            self.temperature = 40.0
            self.humidity = 35.0
            self.rainfall_probability = 10.0

            moisture_targets = [
                48, 38, 55, 25,
                43, 31, 58, 22
            ]

        elif scenario == "heavy_rain":
            self.temperature = 27.0
            self.humidity = 88.0
            self.rainfall_probability = 90.0

            moisture_targets = [
                82, 78, 88, 72,
                84, 76, 91, 70
            ]

        elif scenario == "drought":
            self.temperature = 38.0
            self.humidity = 25.0
            self.rainfall_probability = 5.0

            moisture_targets = [
                35, 27, 42, 18,
                32, 23, 45, 15
            ]

        elif scenario == "optimal":
            self.temperature = 26.0
            self.humidity = 65.0
            self.rainfall_probability = 30.0

            moisture_targets = [
                68, 70, 72, 66,
                69, 71, 74, 67
            ]

        else:
            return False

        for zone, moisture in zip(
            self.zones,
            moisture_targets
        ):
            zone["moisture"] = float(moisture)

            if moisture < 30:
                zone["health"] = 45.0
            elif moisture < 45:
                zone["health"] = 58.0
            elif moisture > 85:
                zone["health"] = 70.0
            else:
                zone["health"] = 80.0

        return True

