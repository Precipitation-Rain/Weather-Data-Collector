# 🌤️ Weather Data Collector

A production-ready Streamlit application to collect any type of weather data for any city in the world — powered by the [Open-Meteo API](https://open-meteo.com/).

---

## 📌 What It Does

- Select any city in the world using **Country → State → City** cascading dropdowns
- Choose from 5 data types — Historical, Forecast, Air Quality, Marine, Climate Change
- Select daily or hourly frequency
- Pick specific weather variables or select all
- Download data as **CSV or Excel**

---

## 🗂️ Project Structure

```
weather-data-collector/
│
├── app.py               # Main Streamlit application
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

---

## ⚙️ Setup & Installation

### 1. Clone or download the project

```bash
git clone https://github.com/yourusername/weather-data-collector.git
cd weather-data-collector
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
streamlit run app.py
```

App will open at `http://localhost:8501`

---

## 📦 Dependencies

| Library | Purpose |
|---|---|
| `streamlit` | Web UI framework |
| `requests` | API calls to Open-Meteo |
| `pandas` | Data handling and export |
| `openpyxl` | Excel file generation |

Built-in Python libraries used — `json`, `urllib`, `logging`, `time`, `datetime`, `io` — no installation needed.

---

## 🌍 Data Sources

| Data Type | API Endpoint | Coverage |
|---|---|---|
| Historical Weather | archive-api.open-meteo.com | 1940 to ~5 days ago |
| Weather Forecast | api.open-meteo.com | Up to 16 days ahead |
| Air Quality | air-quality-api.open-meteo.com | PM2.5, PM10, AQI, pollen |
| Marine / Ocean | marine-api.open-meteo.com | Wave height, swell, currents |
| Climate Change | climate-api.open-meteo.com | 1950 to 2050 projections |

City coordinates sourced from [dr5hn/countries-states-cities-database](https://github.com/dr5hn/countries-states-cities-database) — 250 countries, 300,000+ cities.

> **Note:** Open-Meteo uses a grid-based reanalysis system (ERA5, ERA5-Land, ECMWF IFS). Small differences in coordinates map to different grid cells and may produce slightly different readings.

---

## 🚀 How to Use

1. **Step 1** — Select Country → State → City from dropdowns
2. **Step 2** — Choose data type (Historical / Forecast / Air Quality / Marine / Climate)
3. **Step 3** — Select date range
4. **Step 4** — Choose Daily or Hourly frequency (where applicable)
5. **Step 5** — Select weather variables or check "Select All"
6. **Step 6** — Choose output format (CSV or Excel)
7. Click **🚀 Fetch Weather Data** → preview table appears → download file

---

## 🛡️ Production Features

- **Retry logic** — All network calls retry up to 3 times before failing
- **Error handling** — Specific handling for timeout, connection error, rate limiting (429), bad request (400)
- **Logging** — All API calls, errors, and responses logged with timestamps
- **Input validation** — Date range validation before API call
- **Caching** — City database cached after first load — no repeated downloads
- **Clean stops** — `st.stop()` after every error — no silent failures
- **Edge cases handled** — Countries with no states, states with no cities, invalid coordinates

---

## ⚠️ Known Limitations

- Open-Meteo free tier is for **non-commercial use only**
- City coordinates come from a third-party dataset — may differ slightly from exact city center coordinates
- Marine data is only available for **ocean/coastal locations** — inland cities will return no data
- Air quality historical data availability varies by region
- Climate projections are model-based estimates — not observed data

---

## 📄 License

This project is for educational and personal use.
Weather data provided by [Open-Meteo](https://open-meteo.com/) — free for non-commercial use.
City database by [dr5hn](https://github.com/dr5hn/countries-states-cities-database) — licensed under Open Database License.