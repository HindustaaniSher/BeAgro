# 🌾 BeAgro – Digital Twin for Precision Farming

BeAgro is a web-based digital twin platform for precision farming.  
It uses simulated agricultural data to monitor farm conditions, analyse crop health, generate irrigation recommendations, and support data-driven farming decisions.

🌐 [Live App](https://beagro.onrender.com/)

---

## Features

- Real-time simulated farm sensor data.
- Soil moisture, temperature, humidity, soil pH, rainfall probability, and crop-health monitoring.
- Farm health overview.
- Zone-wise farm monitoring.
- Irrigation recommendations.
- Agricultural alerts.
- Farm analytics and visualisations.
- Soil-moisture and crop-health heatmaps.
- What-if scenario simulation.
- Machine-learning-based crop-health prediction.
- CSV and PDF data export.
- Responsive web dashboard.
- SQLite database for storing farm readings and irrigation events.

---

## Sustainable Development Goal

BeAgro supports:

**SDG 2 – Zero Hunger**

The project promotes precision farming by helping farmers make better decisions about irrigation, crop health, and resource utilisation.

---

## How to Use?

- Open the [Live App](https://beagro.onrender.com/).
- View the simulated farm conditions on the dashboard.
- Check the current soil moisture, temperature, humidity, soil pH, and crop-health values.
- Review irrigation recommendations and alerts.
- Select a farm zone to inspect its individual readings.
- Use the scenario simulator to understand how different conditions may affect the farm.
- Export the available data for further analysis.

---

## How it Works?

BeAgro uses a digital-twin approach to represent a virtual farm.

The system generates simulated sensor readings for different farm conditions, including:

- Soil moisture
- Temperature
- Humidity
- Soil pH
- Rainfall probability
- Crop health

The Flask backend stores and processes these readings using SQLite. The dashboard retrieves the latest information through API endpoints and displays it using charts, cards, tables, and heatmaps.

The recommendation engine analyses the simulated conditions and provides irrigation suggestions. The machine-learning module uses available farm data to estimate crop-health conditions.

The system does not require physical agricultural hardware because the project uses simulated data for demonstration and academic purposes.

---

## Want to Use Locally?

```bash
git clone https://github.com/HindustaaniSher/BeAgro.git
cd BeAgro

python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

pip install -r requirements.txt
python beagro_app.py
```

Then open the application at:

```text
http://127.0.0.1:5000
```

---

## Disclaimer!

BeAgro is an academic demonstration project that uses simulated agricultural data.  
Its recommendations are not a replacement for professional agricultural advice or real-world field measurements.
