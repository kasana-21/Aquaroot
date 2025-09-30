#  AquaRoot

Smart irrigation and soil monitoring system powered by **IoT + Machine Learning**.
AquaRoot helps farmers make data-driven decisions by integrating real-time sensor data, weather forecasts, and predictive ML models to optimize water usage.

---

##  Features

* **Mobile App + Web UI** – intuitive dashboards for monitoring and control
* **Weather API Integration** – fetches temperature, humidity, and ET (evapotranspiration) rates
* **ML Model** – recommends when to irrigate using sensor + weather data
*  **Hardware Integration** – ESP32, DHT22, and soil moisture and temperature sensors
* **Visualization** – real-time data in the User Interfaces
*  **Documentation** – structured guide for setup and usage

---

## Tech Stack

* **Hardware:** ESP32, DHT22, Soil Moisture Sensor
* **Backend:** Python (Flask / FastAPI), Firebase / InfluxDB
* **Frontend:** Flutter (mobile), React / Streamlit (web)
* **ML:** Scikit-learn, XGBoost, TF-IDF (where applicable)
* **IoT Connectivity:** Wi-Fi

---

## Getting Started

### Clone Repo

```bash
git clone https://github.com/<your-username>/aquaroot.git
cd aquaroot
```

### Hardware Setup

* Connect ESP32 to soil and weather sensors
* Flash the Arduino/ESP32 code using PlatformIO / Arduino IDE

### Backend Setup

```bash
pip install -r requirements.txt
python app.py
```

### Frontend Setup

* For Flutter (mobile):

  ```bash
  flutter pub get
  flutter run
  ```
* For Web UI:

  ```bash
  npm install
  npm start
  ```

---

### Project Structure

```plaintext
aquaroot/
│── hardware/       # ESP32 + Arduino code
│── backend/        # APIs, ML models
│── frontend/       # Flutter app + web UI
│── data/           # Sample datasets & preprocessing
│── docs/           # Documentation
│── README.md       # This file
```

### Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -m "Added new feature"`)
4. Push branch (`git push origin feature/new-feature`)
5. Create a Pull Request 🎉

---
### License

This project is licensed under the **MIT License** – see the [LICENSE](LICENSE) file for details.

---

### Author

**Valerie Najjuma** – Computer Science student at Strathmore University.

