#  AquaRoot

AquaRoot is a smart irrigation and soil monitoring system powered by **IoT + Machine Learning**.

It helps farmers make data‑driven decisions by combining real‑time sensor readings (soil moisture, temperature, humidity) with weather data and predictive models to optimize water usage, protect crops, and reduce manual work.

## Project Overview

This system monitors and controls irrigation across a farm using:

- **IoT hardware (ESP32 + sensors)** for real‑time soil and environmental data.
- **Python/ML backend** (in the `farmie/` folder) for analytics and decision support.
- **Flutter mobile app** for monitoring, control, and alerts.

The core capabilities include:

- `real_time_monitoring` – Live dashboards for soil moisture, temperature, and humidity.
- `smart_irrigation` – Automated irrigation recommendations based on rules and ML.
- `alerting` – Notifications when soil is too dry, too wet, or sensors go offline.
- `farm_analytics` – Historical data visualization and basic trends.

---

## Requirements

- **Python 3.10+** (backend and ML under `farmie/`)
- **Flutter 3.x+** (mobile app under `lib/`)
- **Arduino IDE / PlatformIO** (ESP32 firmware in `iot/`)
- **Git**
- **pip, setuptools, wheel**

### Recommended Hardware

- ESP32 development board
- Soil moisture sensor(s)
- DHT22 (or similar) temperature/humidity sensor
- Relays / MOSFETs for pump or valve control
- Water pump(s) or solenoid valve(s)

Minimum: 4GB RAM for development.

---

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/aquaroot.git
cd aquaroot
```

### 2. Backend (Python / ML) setup

The backend and ML components live in the `farmie/` directory.

```bash
cd farmie
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

After installing dependencies, you can run the backend server (adjust if you use a specific framework or entry point):

```bash
python app/main.py
```

Or, if you expose a FastAPI/Flask app:

```bash
uvicorn app.api:app --reload --port 8000
```

### 3. Flutter mobile app setup

From the project root:

```bash
flutter pub get
flutter run
```

This launches the AquaRoot mobile app, which connects to the backend API and displays real‑time sensor data and controls.

### 4. IoT / ESP32 firmware

The firmware lives under `iot/`, typically in `iot/aquaroot.ino`.

Steps:

- Install the **ESP32 board package** in Arduino IDE or set up PlatformIO.
- Open `iot/aquaroot.ino`.
- Configure Wi‑Fi credentials and backend API endpoint (if required).
- Flash the code to the ESP32.

Once flashed, the ESP32 will start reading sensor data and (optionally) controlling irrigation valves.

---

## Data & Models

The backend (in `farmie/`) may include:

- **Data ingestion** from sensors and weather APIs.
- **ML models** for irrigation recommendations (e.g., soil moisture prediction, scheduling).

Typical locations:

- `farmie/app/models/` – ML models and training scripts.
- `farmie/data/` – Sample or collected datasets.

If models are not committed (because of size), you may need to:

1. Train them locally using the scripts in `farmie/app/models/`.
2. Save them under a `models/` directory (e.g., `farmie/models/`).
3. Ensure the backend is configured to load the saved model files.

---

## API Endpoints (example)

Depending on your backend implementation, you might expose endpoints such as:

- `GET /health` – Health check.
- `GET /sensors` – Latest sensor readings.
- `GET /history` – Historical sensor data.
- `POST /irrigation/recommend` – Get ML‑based irrigation recommendation.
- `POST /irrigation/control` – Trigger pump/valve actions.

Refer to the backend code in `farmie/app/` for the exact API contract.

---

## Project Structure

High‑level structure (simplified):

```text
Aquaroot/
├── iot/                 # ESP32 firmware (aquaroot.ino)
├── lib/                 # Flutter app (Dart code)
├── farmie/              # Python backend & ML services
├── assets/              # Images and static assets for Flutter
├── functions/           # (Optional) Cloud Functions / Firebase
├── android/, ios/, web/ # Flutter platform folders
├── pubspec.yaml         # Flutter dependencies
├── README.md            # This file
└── ...
```

See the individual sub‑README files or comments in each module for more details.

---

## Troubleshooting

- **Backend cannot connect to ESP32 or sensors?**
  - Verify ESP32 is on the same network and configured with correct Wi‑Fi credentials.
  - Check serial monitor logs from Arduino IDE / PlatformIO.

- **Flutter app cannot reach backend?**
  - Confirm backend is running (e.g., at `http://127.0.0.1:8000`).
  - On physical devices, use your machine's LAN IP instead of `localhost`.

- **Sensor readings look wrong or constant?**
  - Check wiring and sensor power.
  - Test sensors with a minimal Arduino sketch.

---

## Contributing

Contributions are welcome!

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/my-feature`.
3. Commit your changes: `git commit -m "Add my feature"`.
4. Push to your branch: `git push origin feature/my-feature`.
5. Open a Pull Request.

---

## License

This project is licensed under the **MIT License** – see the [LICENSE](LICENSE) file for details.

---

## Author

**Valerie Najjuma** – Computer Science student at Strathmore University.
