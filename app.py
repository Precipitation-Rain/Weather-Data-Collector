import streamlit as st
import requests
import pandas as pd
from io import BytesIO
from datetime import date, timedelta
import json
import urllib.request
import urllib.error
import logging
import time
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────────────────
# LOGGING
# ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────
# PAGE CONFIG  — must be the first Streamlit call
# ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="WeatherLens",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ──────────────────────────────────────────────────────────
# PREMIUM THEME
# ──────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── Base ─────────────────────────────────────────────── */
html, body, .stApp {
    font-family: 'DM Sans', -apple-system, sans-serif !important;
    background: #07111e !important;
    color: #d8e4f0 !important;
}
#MainMenu, footer { visibility: hidden; }
[data-testid="stDecoration"], [data-testid="stToolbar"] { display: none; }

/* subtle dot-grid background */
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image: radial-gradient(circle, #1b2d45 1px, transparent 1px);
    background-size: 28px 28px;
    opacity: 0.35;
    pointer-events: none;
    z-index: 0;
}

/* ── Hero ─────────────────────────────────────────────── */
.hero {
    padding: 60px 0 44px;
    text-align: center;
    border-bottom: 1px solid #0f1f33;
    margin-bottom: 52px;
    position: relative;
}
.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    background: rgba(88, 101, 242, 0.10);
    border: 1px solid rgba(88, 101, 242, 0.28);
    border-radius: 100px;
    padding: 5px 16px;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.68rem;
    font-weight: 600;
    color: #9ba8f7;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 22px;
}
.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: 3.4rem;
    font-weight: 800;
    color: #eef2ff;
    letter-spacing: -0.04em;
    line-height: 1.05;
    margin: 0 0 14px;
}
.hero-accent {
    background: linear-gradient(115deg, #7b8cff 0%, #c084fc 55%, #38bdf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-sub {
    font-family: 'DM Sans', sans-serif;
    color: #2e4a67;
    font-size: 1rem;
    line-height: 1.7;
    max-width: 460px;
    margin: 0 auto;
    font-weight: 400;
}

/* ── Step header ──────────────────────────────────────── */
.step-wrap {
    display: flex;
    align-items: center;
    gap: 13px;
    margin: 44px 0 16px;
}
.step-num {
    width: 30px; height: 30px; border-radius: 50%;
    background: linear-gradient(135deg, #5865f2, #9b59f5);
    display: flex; align-items: center; justify-content: center;
    font-family: 'Syne', sans-serif;
    font-size: 0.76rem; font-weight: 700; color: #fff; flex-shrink: 0;
    box-shadow: 0 0 0 5px rgba(88, 101, 242, 0.12);
}
.step-text {
    font-family: 'Syne', sans-serif;
    font-size: 0.98rem; font-weight: 700; color: #eef2ff;
    letter-spacing: -0.01em;
}

/* ── Cards ────────────────────────────────────────────── */
.info-card {
    background: rgba(38, 168, 218, 0.06);
    border: 1px solid rgba(38, 168, 218, 0.15);
    border-radius: 10px;
    padding: 11px 17px;
    color: #6bc8e8;
    font-size: 0.86rem;
    line-height: 1.55;
    margin: 4px 0 12px;
    font-family: 'DM Sans', sans-serif;
}
.ok-card {
    background: rgba(16, 185, 129, 0.07);
    border: 1px solid rgba(16, 185, 129, 0.2);
    border-radius: 10px;
    padding: 11px 18px;
    color: #5edbad;
    font-size: 0.87rem;
    font-weight: 500;
    margin: 8px 0;
    font-family: 'DM Sans', sans-serif;
}

/* ── Stat row ─────────────────────────────────────────── */
.stat-row { display: flex; gap: 12px; margin: 18px 0; }
.stat-box {
    flex: 1;
    background: #0c1929;
    border: 1px solid #0f2035;
    border-radius: 14px;
    padding: 18px 16px;
    text-align: center;
}
.stat-val {
    font-family: 'Syne', sans-serif;
    font-size: 1.6rem; font-weight: 800;
    color: #eef2ff; letter-spacing: -0.03em;
}
.stat-accent { color: #7b8cff; }
.stat-lbl {
    font-size: 0.67rem; color: #2e4a67;
    text-transform: uppercase; letter-spacing: 0.1em;
    font-weight: 600; margin-top: 5px;
    font-family: 'DM Sans', sans-serif;
}

/* ── AI section header ────────────────────────────────── */
.ai-header {
    display: flex; align-items: center; gap: 12px;
    margin: 6px 0 24px;
}
.ai-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: #5865f2; box-shadow: 0 0 10px #5865f2;
    animation: livepulse 2.2s ease-in-out infinite;
}
@keyframes livepulse { 0%,100%{opacity:1;} 50%{opacity:0.3;} }
.ai-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem; font-weight: 700; color: #eef2ff;
}

/* ── Sub-section label ────────────────────────────────── */
.sub-label {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.66rem; font-weight: 700;
    letter-spacing: 0.12em; text-transform: uppercase;
    color: #5865f2; margin-bottom: 12px;
}

/* ── Insight cards ────────────────────────────────────── */
.insight-card {
    background: #09172a;
    border: 1px solid #0f2035;
    border-left: 3px solid #5865f2;
    border-radius: 12px;
    padding: 15px 20px;
    margin: 9px 0;
    color: #b8ccde;
    font-size: 0.92rem;
    line-height: 1.7;
    font-family: 'DM Sans', sans-serif;
    transition: border-left-color 0.22s, background 0.22s;
}
.insight-card:hover {
    border-left-color: #c084fc;
    background: #0c1e35;
}

/* ── Streamlit widget overrides ───────────────────────── */

/* Primary action buttons */
.stButton > button {
    background: linear-gradient(135deg, #5865f2 0%, #9b59f5 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 0.62rem 1.7rem !important;
    box-shadow: 0 4px 20px rgba(88, 101, 242, 0.25) !important;
    transition: all 0.22s !important;
    letter-spacing: 0.01em !important;
}
.stButton > button:hover {
    box-shadow: 0 8px 28px rgba(88, 101, 242, 0.45) !important;
    transform: translateY(-2px) !important;
}

/* Download buttons */
.stDownloadButton > button {
    background: rgba(88, 101, 242, 0.08) !important;
    color: #9ba8f7 !important;
    border: 1px solid rgba(88, 101, 242, 0.28) !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.86rem !important;
    box-shadow: none !important;
}
.stDownloadButton > button:hover {
    background: rgba(88, 101, 242, 0.15) !important;
    transform: none !important;
}

/* Input labels -> small uppercase */
.stSelectbox label, .stRadio label, .stMultiSelect label,
.stDateInput label, .stCheckbox label {
    color: #2e4a67 !important;
    font-size: 0.7rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    font-family: 'DM Sans', sans-serif !important;
}
/* Checkbox label overrides (needs natural case) */
.stCheckbox label {
    color: #7a96b0 !important;
    font-size: 0.87rem !important;
    text-transform: none !important;
    letter-spacing: 0 !important;
    font-weight: 400 !important;
}

/* Select / multiselect containers */
.stSelectbox > div > div,
.stMultiSelect > div > div {
    background: #0c1929 !important;
    border: 1px solid #152336 !important;
    border-radius: 10px !important;
    color: #d8e4f0 !important;
}

/* Radio container */
.stRadio > div {
    background: #0c1929;
    border: 1px solid #152336;
    border-radius: 10px;
    padding: 10px 14px;
}

/* Date inputs */
.stDateInput > div > div {
    background: #0c1929 !important;
    border: 1px solid #152336 !important;
    border-radius: 10px !important;
    color: #d8e4f0 !important;
}

/* DataFrame */
.stDataFrame {
    border-radius: 12px !important;
    border: 1px solid #0f2035 !important;
    overflow: hidden !important;
}

/* Expander */
.streamlit-expanderHeader {
    background: #0c1929 !important;
    border-radius: 10px !important;
    color: #2e4a67 !important;
    font-size: 0.83rem !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* Divider */
hr {
    border: none !important;
    border-top: 1px solid #0f1f33 !important;
    margin: 44px 0 !important;
}

/* Spinner */
.stSpinner > div { border-top-color: #5865f2 !important; }

/* ── Inline chat form — replaces fixed st.chat_input ──── */
[data-testid="stForm"] {
    border: none !important;
    padding: 0 !important;
    background: transparent !important;
}
/* Text input box */
.stTextInput > div > div {
    background: #0c1929 !important;
    border: 1px solid #152336 !important;
    border-radius: 12px !important;
}
.stTextInput input {
    color: #d8e4f0 !important;
    font-family: 'DM Sans', sans-serif !important;
    background: transparent !important;
    font-size: 0.9rem !important;
}
.stTextInput input::placeholder {
    color: #2e4a67 !important;
}
.stTextInput input:focus {
    border-color: #5865f2 !important;
    box-shadow: 0 0 0 2px rgba(88, 101, 242, 0.1) !important;
    outline: none !important;
}

/* Chat messages */
[data-testid="stChatMessage"] {
    background: #0c1929 !important;
    border: 1px solid #0f1f33 !important;
    border-radius: 12px !important;
}

/* Streamlit alert boxes */
.stAlert {
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.88rem !important;
}

/* Caption */
.stCaption, .stCaption p {
    color: #1e3450 !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* Footer */
.footer {
    text-align: center;
    padding: 38px 0 22px;
    color: #142030;
    font-size: 0.76rem;
    letter-spacing: 0.05em;
    font-family: 'DM Sans', sans-serif;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────────────────────
DATASET_URL     = "https://raw.githubusercontent.com/dr5hn/countries-states-cities-database/master/json/countries+states+cities.json"
DATASET_TIMEOUT = 30
API_TIMEOUT     = 20
MAX_RETRIES     = 3
RETRY_DELAY     = 2

API_URL_MAP = {
    "historical":  "https://archive-api.open-meteo.com/v1/archive",
    "forecast":    "https://api.open-meteo.com/v1/forecast",
    "air_quality": "https://air-quality-api.open-meteo.com/v1/air-quality",
    "marine":      "https://marine-api.open-meteo.com/v1/marine",
    "climate":     "https://climate-api.open-meteo.com/v1/climate"
}

DATA_TYPE_OPTIONS = {
    "🕰️ Historical Weather":         "historical",
    "🔮 Weather Forecast":           "forecast",
    "💨 Air Quality":                "air_quality",
    "🌊 Marine / Ocean":             "marine",
    "🌍 Climate Change Projections": "climate"
}

DATA_TYPE_DESCRIPTIONS = {
    "historical":  "Past weather data from 1940 to ~5 days ago. Uses ERA5 reanalysis data.",
    "forecast":    "Future weather forecast up to 16 days ahead.",
    "air_quality": "Hourly air pollution — PM2.5, PM10, ozone, CO, NO2, SO2, pollen, AQI.",
    "marine":      "Ocean and sea data — wave height, direction, period, swell, ocean currents.",
    "climate":     "Long-term climate change projections. Daily data from 1950 to 2050."
}

VARIABLES = {
    "historical_daily": {
        "Max Temperature (°C)":            "temperature_2m_max",
        "Min Temperature (°C)":            "temperature_2m_min",
        "Max Apparent Temperature (°C)":   "apparent_temperature_max",
        "Min Apparent Temperature (°C)":   "apparent_temperature_min",
        "Sunrise":                         "sunrise",
        "Sunset":                          "sunset",
        "Daylight Duration (s)":           "daylight_duration",
        "Sunshine Duration (s)":           "sunshine_duration",
        "Precipitation Sum (mm)":          "precipitation_sum",
        "Rain Sum (mm)":                   "rain_sum",
        "Snowfall Sum (cm)":               "snowfall_sum",
        "Precipitation Hours":             "precipitation_hours",
        "Max Wind Speed 10m (km/h)":       "wind_speed_10m_max",
        "Max Wind Gusts 10m (km/h)":       "wind_gusts_10m_max",
        "Dominant Wind Direction (°)":     "wind_direction_10m_dominant",
        "Shortwave Radiation Sum (MJ/m²)": "shortwave_radiation_sum",
        "ET0 Evapotranspiration (mm)":     "et0_fao_evapotranspiration",
        "Weather Code":                    "weather_code"
    },
    "historical_hourly": {
        "Temperature 2m (°C)":             "temperature_2m",
        "Relative Humidity 2m (%)":        "relative_humidity_2m",
        "Dew Point 2m (°C)":               "dew_point_2m",
        "Apparent Temperature (°C)":       "apparent_temperature",
        "Precipitation (mm)":              "precipitation",
        "Rain (mm)":                       "rain",
        "Snowfall (cm)":                   "snowfall",
        "Snow Depth (m)":                  "snow_depth",
        "Weather Code":                    "weather_code",
        "Sea Level Pressure (hPa)":        "pressure_msl",
        "Surface Pressure (hPa)":          "surface_pressure",
        "Cloud Cover (%)":                 "cloud_cover",
        "Cloud Cover Low (%)":             "cloud_cover_low",
        "Cloud Cover Mid (%)":             "cloud_cover_mid",
        "Cloud Cover High (%)":            "cloud_cover_high",
        "Wind Speed 10m (km/h)":           "wind_speed_10m",
        "Wind Speed 100m (km/h)":          "wind_speed_100m",
        "Wind Direction 10m (°)":          "wind_direction_10m",
        "Wind Direction 100m (°)":         "wind_direction_100m",
        "Wind Gusts 10m (km/h)":           "wind_gusts_10m",
        "Soil Temperature 0-7cm (°C)":     "soil_temperature_0_to_7cm",
        "Soil Temperature 7-28cm (°C)":    "soil_temperature_7_to_28cm",
        "Soil Temperature 28-100cm (°C)":  "soil_temperature_28_to_100cm",
        "Soil Temperature 100-255cm (°C)": "soil_temperature_100_to_255cm",
        "Soil Moisture 0-7cm (m³/m³)":     "soil_moisture_0_to_7cm",
        "Soil Moisture 7-28cm (m³/m³)":    "soil_moisture_7_to_28cm",
        "Soil Moisture 28-100cm (m³/m³)":  "soil_moisture_28_to_100cm",
        "Soil Moisture 100-255cm (m³/m³)": "soil_moisture_100_to_255cm",
        "Shortwave Radiation (W/m²)":      "shortwave_radiation",
        "Vapour Pressure Deficit (kPa)":   "vapour_pressure_deficit",
        "ET0 Evapotranspiration (mm)":     "et0_fao_evapotranspiration"
    },
    "air_quality": {
        "PM10 (μg/m³)":               "pm10",
        "PM2.5 (μg/m³)":             "pm2_5",
        "Carbon Monoxide (μg/m³)":    "carbon_monoxide",
        "Nitrogen Dioxide (μg/m³)":   "nitrogen_dioxide",
        "Sulphur Dioxide (μg/m³)":    "sulphur_dioxide",
        "Ozone (μg/m³)":             "ozone",
        "Aerosol Optical Depth":      "aerosol_optical_depth",
        "Dust (μg/m³)":              "dust",
        "UV Index":                   "uv_index",
        "UV Index Clear Sky":         "uv_index_clear_sky",
        "Alder Pollen (grains/m³)":   "alder_pollen",
        "Birch Pollen (grains/m³)":   "birch_pollen",
        "Grass Pollen (grains/m³)":   "grass_pollen",
        "Mugwort Pollen (grains/m³)": "mugwort_pollen",
        "Olive Pollen (grains/m³)":   "olive_pollen",
        "Ragweed Pollen (grains/m³)": "ragweed_pollen",
        "European AQI":               "european_aqi",
        "US AQI":                     "us_aqi"
    },
    "marine_hourly": {
        "Wave Height (m)":               "wave_height",
        "Wave Direction (°)":            "wave_direction",
        "Wave Period (s)":               "wave_period",
        "Wind Wave Height (m)":          "wind_wave_height",
        "Wind Wave Direction (°)":       "wind_wave_direction",
        "Wind Wave Period (s)":          "wind_wave_period",
        "Wind Wave Peak Period (s)":     "wind_wave_peak_period",
        "Swell Wave Height (m)":         "swell_wave_height",
        "Swell Wave Direction (°)":      "swell_wave_direction",
        "Swell Wave Period (s)":         "swell_wave_period",
        "Swell Wave Peak Period (s)":    "swell_wave_peak_period",
        "Ocean Current Velocity (m/s)":  "ocean_current_velocity",
        "Ocean Current Direction (°)":   "ocean_current_direction"
    },
    "marine_daily": {
        "Max Wave Height (m)":               "wave_height_max",
        "Dominant Wave Direction (°)":       "wave_direction_dominant",
        "Max Wave Period (s)":               "wave_period_max",
        "Max Wind Wave Height (m)":          "wind_wave_height_max",
        "Dominant Wind Wave Direction (°)":  "wind_wave_direction_dominant",
        "Max Wind Wave Period (s)":          "wind_wave_period_max",
        "Max Wind Wave Peak Period (s)":     "wind_wave_peak_period_max",
        "Max Swell Wave Height (m)":         "swell_wave_height_max",
        "Dominant Swell Wave Direction (°)": "swell_wave_direction_dominant",
        "Max Swell Wave Period (s)":         "swell_wave_period_max",
        "Max Swell Wave Peak Period (s)":    "swell_wave_peak_period_max"
    },
    "climate": {
        "Max Temperature 2m (°C)":         "temperature_2m_max",
        "Min Temperature 2m (°C)":         "temperature_2m_min",
        "Mean Temperature 2m (°C)":        "temperature_2m_mean",
        "Max Apparent Temperature (°C)":   "apparent_temperature_max",
        "Min Apparent Temperature (°C)":   "apparent_temperature_min",
        "Mean Apparent Temperature (°C)":  "apparent_temperature_mean",
        "Precipitation Sum (mm)":          "precipitation_sum",
        "Rain Sum (mm)":                   "rain_sum",
        "Snowfall Sum (cm)":               "snowfall_sum",
        "Max Wind Speed 10m (km/h)":       "wind_speed_10m_max",
        "Max Wind Speed 100m (km/h)":      "wind_speed_100m_max",
        "Shortwave Radiation Sum (MJ/m²)": "shortwave_radiation_sum",
        "ET0 Evapotranspiration (mm)":     "et0_fao_evapotranspiration",
        "Max Relative Humidity 2m (%)":    "relative_humidity_2m_max",
        "Min Relative Humidity 2m (%)":    "relative_humidity_2m_min",
        "Soil Moisture 0-10cm (m³/m³)":    "soil_moisture_0_to_10cm_mean",
        "Precipitation Days (≥1mm)":       "precipitation_days",
        "Sunshine Duration (s)":           "sunshine_duration"
    }
}

DEFAULT_VARS = {
    "historical_daily":  ["Max Temperature (°C)", "Min Temperature (°C)", "Precipitation Sum (mm)"],
    "historical_hourly": ["Temperature 2m (°C)", "Relative Humidity 2m (%)", "Precipitation (mm)"],
    "forecast_daily":    ["Max Temperature (°C)", "Min Temperature (°C)", "Precipitation Sum (mm)"],
    "forecast_hourly":   ["Temperature 2m (°C)", "Relative Humidity 2m (%)", "Precipitation (mm)"],
    "air_quality":       ["PM10 (μg/m³)", "PM2.5 (μg/m³)", "Ozone (μg/m³)", "European AQI"],
    "marine_hourly":     ["Wave Height (m)", "Wave Direction (°)", "Wave Period (s)"],
    "marine_daily":      ["Max Wave Height (m)", "Dominant Wave Direction (°)", "Max Wave Period (s)"],
    "climate":           ["Max Temperature 2m (°C)", "Min Temperature 2m (°C)", "Precipitation Sum (mm)"]
}

# ──────────────────────────────────────────────────────────
# UI HELPERS
# ──────────────────────────────────────────────────────────

def step_header(n: int | str, label: str) -> None:
    st.markdown(
        f'<div class="step-wrap">'
        f'<div class="step-num">{n}</div>'
        f'<div class="step-text">{label}</div>'
        f'</div>',
        unsafe_allow_html=True
    )


def info_card(text: str) -> None:
    st.markdown(
        f'<div class="info-card">ℹ &nbsp; {text}</div>',
        unsafe_allow_html=True
    )


def ok_card(html: str) -> None:
    st.markdown(
        f'<div class="ok-card">✅ &nbsp; {html}</div>',
        unsafe_allow_html=True
    )


def sub_label(text: str) -> None:
    st.markdown(f'<div class="sub-label">{text}</div>', unsafe_allow_html=True)


def stat_row(records: int, columns: int, days: int) -> None:
    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-box">
            <div class="stat-val">{records:,}</div>
            <div class="stat-lbl">Records</div>
        </div>
        <div class="stat-box">
            <div class="stat-val">{columns}</div>
            <div class="stat-lbl">Variables</div>
        </div>
        <div class="stat-box">
            <div class="stat-val stat-accent">{days}</div>
            <div class="stat-lbl">Days</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────
# DATA HELPERS
# ──────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def load_world_data() -> list | None:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Loading world dataset — attempt {attempt}")
            with urllib.request.urlopen(DATASET_URL, timeout=DATASET_TIMEOUT) as r:
                data = json.loads(r.read())
            logger.info(f"World dataset loaded — {len(data)} countries")
            return data
        except urllib.error.URLError as e:
            logger.error(f"Network error: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
    return None


def fetch_weather_data(url: str, params: dict) -> tuple[int, dict | None, str]:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"API call — attempt {attempt}")
            r = requests.get(url, params=params, timeout=API_TIMEOUT)
            logger.info(f"Status: {r.status_code}")

            if r.status_code == 200:
                return 200, r.json(), ""
            elif r.status_code == 429:
                if attempt < MAX_RETRIES:
                    time.sleep(30)
                    continue
                return 429, None, "Rate limit hit — please wait a moment and try again."
            elif r.status_code == 400:
                return 400, None, f"Bad request — check your parameters. Details: {r.text}"
            else:
                return r.status_code, None, f"API error {r.status_code}: {r.text}"

        except requests.exceptions.Timeout:
            logger.error(f"Timeout — attempt {attempt}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error — attempt {attempt}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
        except requests.exceptions.RequestException as e:
            return 0, None, f"Network error: {e}"

    return 0, None, "Failed after retries — check your internet connection."


def get_variable_key(data_type: str, frequency: str) -> str:
    if data_type in ["historical", "forecast"]:
        return f"historical_{frequency.lower()}"
    elif data_type == "marine":
        return f"marine_{frequency.lower()}"
    elif data_type == "air_quality":
        return "air_quality"
    elif data_type == "climate":
        return "climate"
    return "historical_daily"


def validate_dates(start: date, end: date, data_type: str) -> str | None:
    if start >= end:
        return "Start date must be before end date."
    if data_type == "historical" and (end - start).days > 365 * 10:
        return "Date range too large — maximum 10 years per request."
    return None


def build_download_filename(city: str, data_type_label: str, start: date, end: date) -> str:
    clean = (
        data_type_label
        .replace("🕰️ ", "").replace("🔮 ", "").replace("💨 ", "")
        .replace("🌊 ", "").replace("🌍 ", "")
        .replace(" ", "_").replace("/", "_")
    )
    return f"{city.replace(' ', '_').replace(',', '')}_{clean}_{start}_{end}"


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    buf.seek(0)
    return buf.getvalue()


# ──────────────────────────────────────────────────────────
# GROQ / AI HELPERS
# ──────────────────────────────────────────────────────────

def get_groq_client() -> Groq | None:
    api_key = os.getenv("GROQ_API_KEY") or ""
    if not api_key:
        try:
            api_key = st.secrets.get("GROQ_API_KEY", "")
        except Exception:
            pass
    return Groq(api_key=api_key) if api_key else None


def build_data_context(df: pd.DataFrame, data_type_label: str, city: str,
                        start_date, end_date, selected_labels: list) -> str:
    num_df = df.select_dtypes(include="number")
    return "\n".join([
        f"Dataset: {data_type_label} for {city}",
        f"Date range: {start_date} -> {end_date}",
        f"Total records: {len(df):,} rows",
        f"Variables: {', '.join(selected_labels)}",
        "",
        "Statistical summary:",
        num_df.describe().round(3).to_string(),
        "",
        "First 20 rows:",
        df.head(20).to_string(index=False),
    ])


def generate_insights(client: Groq, df: pd.DataFrame, data_type_label: str,
                       city: str, start_date, end_date, selected_labels: list) -> list[str]:
    context = build_data_context(df, data_type_label, city, start_date, end_date, selected_labels)

    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a friendly data storyteller. Your job is to explain data insights "
                    "to everyday people — not scientists or data analysts.\n\n"
                    "Generate exactly 5 insights. Obey every rule below strictly.\n\n"

                    "LANGUAGE RULES:\n"
                    "- Write like you're explaining to a smart friend who never studied science\n"
                    "- NEVER use raw scientific units in your output: no μg/m³, hPa, MJ/m², "
                    "  m³/m³, W/m², kPa, mm unless it's a very common measurement like rainfall in mm\n"
                    "- For air quality data: ALWAYS anchor to AQI score and plain categories "
                    "  (Good / Moderate / Unhealthy / Very Unhealthy / Hazardous). "
                    "  Translate PM2.5 / PM10 as 'fine dust' or 'air pollution' — never as raw μg/m³ values\n"
                    "- For temperature: °C is fine; also describe as 'scorching', 'mild', 'freezing' where apt\n"
                    "- For rain/precipitation: say 'rainy days', 'dry stretch', 'heavy monsoon rains' — "
                    "  avoid raw mm unless comparing (e.g. '3x more rain than usual')\n"
                    "- For wind: 'strong winds', 'calm conditions', 'gusty'\n"
                    "- For waves: 'rough seas', 'calm ocean', '3-metre waves'\n"
                    "- For humidity: 'very humid', 'dry air', '80% humidity' is OK\n\n"

                    "INSIGHT STRUCTURE:\n"
                    "- Lead with the CONCLUSION, then back it with a number or comparison\n"
                    "- Good example: '🌫️ January had the worst air quality of the year — AQI hit 280 on several days, "
                    "  levels that are genuinely harmful to breathe for long'\n"
                    "- Good example: '📈 Air quality got roughly 20% worse by December compared to January, "
                    "  suggesting pollution builds up as the year goes on'\n"
                    "- Good example: '🌿 May stood out as the cleanest month — AQI stayed in the Good range almost every day'\n"
                    "- Use % comparisons, season names, and month names to make numbers relatable\n"
                    "- Cover these 5 angles (one each): overall trend, best period, "
                    "  worst period, something surprising or unexpected, a practical takeaway for someone living there\n"
                    "- One clear sentence per insight. No numbering. No bullet points.\n"
                    "- Start each line with a single relevant emoji."
                )
            },
            {
                "role": "user",
                "content": f"Analyze this data and give exactly 5 plain-language insights:\n\n{context}"
            }
        ],
        max_tokens=700,
        temperature=0.7
    )

    raw = resp.choices[0].message.content.strip()
    return [ln.strip() for ln in raw.split("\n") if ln.strip() and len(ln.strip()) > 10][:5]


def get_chat_response(client: Groq, user_msg: str, chat_history: list,
                       df: pd.DataFrame, data_type_label: str, city: str,
                       start_date, end_date, selected_labels: list) -> str:
    context = build_data_context(df, data_type_label, city, start_date, end_date, selected_labels)

    system = (
        f"You are a friendly weather data analyst. You have access to this dataset:\n\n{context}\n\n"
        "When answering:\n"
        "- Reference actual numbers from the data\n"
        "- Explain things in plain English — avoid jargon and raw scientific units\n"
        "- Keep answers to 2-4 sentences unless the user asks for more detail\n"
        "- If the data doesn't contain what the user is asking about, say so clearly"
    )

    messages = [{"role": "system", "content": system}]
    for m in chat_history[-10:]:
        messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": user_msg})

    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        max_tokens=400,
        temperature=0.7
    )
    return resp.choices[0].message.content.strip()


# ══════════════════════════════════════════════════════════
# APP — HERO HEADER
# ══════════════════════════════════════════════════════════
st.markdown("""
<div class="hero">
    <div class="hero-badge">✦ &nbsp; Open-Meteo Powered</div>
    <h1 class="hero-title">Weather<span class="hero-accent">Lens</span></h1>
    <p class="hero-sub">Collect, explore and understand weather data<br>for any city in the world — in seconds.</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# LOAD CITY DATABASE
# ══════════════════════════════════════════════════════════
with st.spinner("Loading city database..."):
    world_data = load_world_data()

if world_data is None:
    st.error(
        "❌ Failed to load the city database after multiple attempts. "
        "Please check your internet connection and refresh."
    )
    st.stop()

# ══════════════════════════════════════════════════════════
# STEP 1 — LOCATION
# ══════════════════════════════════════════════════════════
step_header(1, "Select Location")

country_names  = [c["name"] for c in world_data]
default_idx    = country_names.index("India") if "India" in country_names else 0
selected_country = st.selectbox("Country", country_names, index=default_idx)

country_data = next((c for c in world_data if c["name"] == selected_country), None)
lat, lon, city = None, None, None

if country_data is None:
    st.error("Country data not found — please select another.")
    st.stop()

state_names = [s["name"] for s in country_data.get("states", [])]

if not state_names:
    st.warning(f"No states/provinces found for {selected_country}.")
else:
    selected_state = st.selectbox("State / Province", state_names)
    state_data = next((s for s in country_data["states"] if s["name"] == selected_state), None)

    if state_data is None:
        st.error("State data not found — please select another.")
    else:
        city_names = [c["name"] for c in state_data.get("cities", [])]

        if not city_names:
            st.warning(f"No cities found for {selected_state} — try a neighbouring state.")
        else:
            selected_city = st.selectbox("City", city_names)
            city_data = next((c for c in state_data["cities"] if c["name"] == selected_city), None)

            if city_data is None:
                st.error("City data not found.")
            else:
                try:
                    lat  = float(city_data["latitude"])
                    lon  = float(city_data["longitude"])
                    city = selected_city
                    ok_card(
                        f"<strong>{selected_city}</strong>, {selected_state}, {selected_country}"
                        f" &nbsp;·&nbsp; {lat:.4f}°N &nbsp; {lon:.4f}°E"
                    )
                except (ValueError, KeyError) as e:
                    logger.error(f"Bad coordinates for {selected_city}: {e}")
                    st.error(f"Invalid coordinates for {selected_city} — please pick another city.")

# ══════════════════════════════════════════════════════════
# MAIN FLOW
# ══════════════════════════════════════════════════════════
if lat and lon and city:

    # STEP 2 — DATA TYPE
    step_header(2, "Select Data Type")
    data_type_label = st.selectbox("Data type", list(DATA_TYPE_OPTIONS.keys()))
    data_type       = DATA_TYPE_OPTIONS[data_type_label]
    info_card(DATA_TYPE_DESCRIPTIONS[data_type])

    # STEP 3 — DATE RANGE
    step_header(3, "Select Date Range")
    today = date.today()

    date_configs = {
        "historical":  dict(start_val=date(2025, 1, 1), end_val=date(2025, 12, 31),
                            min_val=date(1940, 1, 1),   max_val=today - timedelta(days=5)),
        "forecast":    dict(start_val=today,             end_val=today + timedelta(days=7),
                            min_val=today,               max_val=today + timedelta(days=16)),
        "climate":     dict(start_val=date(2024, 1, 1), end_val=date(2030, 12, 31),
                            min_val=date(1950, 1, 1),   max_val=date(2050, 12, 31)),
        "air_quality": dict(start_val=date(2025, 1, 1), end_val=today,
                            min_val=None,               max_val=None),
        "marine":      dict(start_val=date(2025, 1, 1), end_val=today,
                            min_val=None,               max_val=None),
    }

    cfg = date_configs[data_type]
    col1, col2 = st.columns(2)

    with col1:
        kw = {"value": cfg["start_val"]}
        if cfg["min_val"]: kw["min_value"] = cfg["min_val"]
        if cfg["max_val"]: kw["max_value"] = cfg["max_val"]
        start_date = st.date_input("Start date", **kw)

    with col2:
        kw = {"value": cfg["end_val"]}
        if cfg["min_val"]: kw["min_value"] = cfg["min_val"]
        if cfg["max_val"]: kw["max_value"] = cfg["max_val"]
        end_date = st.date_input("End date", **kw)

    # STEP 4 — FREQUENCY
    frequency   = None
    step_offset = 0

    if data_type in ["historical", "forecast", "marine"]:
        step_header(4, "Select Frequency")
        frequency = st.radio("Frequency", ["Daily", "Hourly"])
    elif data_type == "air_quality":
        frequency   = "Hourly"
        step_offset = -1
    elif data_type == "climate":
        frequency   = "Daily"
        step_offset = -1

    # STEP 5 — VARIABLES
    step5_num = 5 + step_offset if step_offset else 5
    step_header(step5_num, "Select Variables")

    var_key = get_variable_key(data_type, frequency or "Daily")
    if data_type == "forecast":
        var_key = f"historical_{(frequency or 'Daily').lower()}"

    all_variables   = VARIABLES.get(var_key, {})
    default_var_key = var_key if var_key in DEFAULT_VARS else "historical_daily"
    default_vars    = DEFAULT_VARS.get(default_var_key, [])

    if not all_variables:
        st.error("No variables available for this selection.")
        st.stop()

    select_all = st.checkbox("Select all variables")
    selected_labels = (
        list(all_variables.keys())
        if select_all
        else st.multiselect(
            "Variables",
            options=list(all_variables.keys()),
            default=[v for v in default_vars if v in all_variables]
        )
    )
    selected_variables = [all_variables[label] for label in selected_labels]

    # STEP 6 — OUTPUT FORMAT
    step6_num = 6 + step_offset if step_offset else 6
    step_header(step6_num, "Download Format")
    output_format = st.radio("Format", ["CSV", "Excel"])

    # ── FETCH BUTTON ──────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🚀 Fetch Weather Data", type="primary"):

        if not selected_variables:
            st.warning("⚠️ Please select at least one variable.")
            st.stop()

        date_error = validate_dates(start_date, end_date, data_type)
        if date_error:
            st.warning(f"⚠️ {date_error}")
            st.stop()

        with st.spinner("Fetching data from Open-Meteo..."):
            url    = API_URL_MAP[data_type]
            params = {
                "latitude": lat, "longitude": lon,
                "start_date": str(start_date), "end_date": str(end_date),
                "timezone": "auto"
            }

            if data_type == "air_quality":
                params["hourly"] = selected_variables
                freq_key = "hourly"
            elif data_type == "climate":
                params["daily"] = selected_variables
                freq_key = "daily"
            elif data_type == "marine":
                if frequency == "Hourly":
                    params["hourly"] = selected_variables
                    freq_key = "hourly"
                else:
                    params["daily"] = selected_variables
                    freq_key = "daily"
            elif frequency == "Daily":
                params["daily"] = selected_variables
                freq_key = "daily"
            else:
                params["hourly"] = selected_variables
                freq_key = "hourly"

            status_code, resp_data, error_msg = fetch_weather_data(url, params)

        if status_code != 200 or resp_data is None:
            st.error(f"❌ {error_msg}")
            st.stop()

        if freq_key not in resp_data:
            st.error(f"❌ Expected key '{freq_key}' not in API response.")
            with st.expander("Raw API response"):
                st.json(resp_data)
            st.stop()

        try:
            df = pd.DataFrame(resp_data[freq_key])
        except Exception as e:
            st.error(f"❌ Failed to parse response: {e}")
            st.stop()

        if df.empty:
            st.warning("⚠️ API returned no data — try a different date range or location.")
            st.stop()

        stat_row(len(df), len(df.columns), (end_date - start_date).days)

        st.dataframe(df, use_container_width=True)

        units_key = f"{freq_key}_units"
        if units_key in resp_data:
            with st.expander("📐 Column units"):
                st.dataframe(
                    pd.DataFrame(
                        list(resp_data[units_key].items()),
                        columns=["Column", "Unit"]
                    ),
                    use_container_width=True
                )

        file_name = build_download_filename(city, data_type_label, start_date, end_date)

        if output_format == "CSV":
            try:
                st.download_button(
                    "⬇️ Download CSV",
                    df.to_csv(index=False).encode("utf-8"),
                    f"{file_name}.csv",
                    "text/csv"
                )
            except Exception as e:
                st.error(f"❌ CSV generation failed: {e}")
        else:
            try:
                st.download_button(
                    "⬇️ Download Excel",
                    to_excel_bytes(df),
                    f"{file_name}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"❌ Excel generation failed: {e}")

        st.session_state.update({
            "wx_df":       df,
            "wx_city":     city,
            "wx_label":    data_type_label,
            "wx_vars":     selected_labels,
            "wx_start":    start_date,
            "wx_end":      end_date,
            "wx_insights": None,
            "wx_chat":     []
        })

    # ══════════════════════════════════════════════════════
    # AI INSIGHTS + CHAT
    # ══════════════════════════════════════════════════════
    if st.session_state.get("wx_df") is not None:
        groq_client = get_groq_client()

        if groq_client is None:
            st.divider()
            st.warning(
                "🔑 Add `GROQ_API_KEY` to your `.env` file (local) or Streamlit secrets (deployed) "
                "to enable AI insights and chat."
            )
        else:
            _df    = st.session_state["wx_df"]
            _city  = st.session_state["wx_city"]
            _label = st.session_state["wx_label"]
            _vars  = st.session_state["wx_vars"]
            _start = st.session_state["wx_start"]
            _end   = st.session_state["wx_end"]

            st.divider()

            st.markdown("""
            <div class="ai-header">
                <div class="ai-dot"></div>
                <div class="ai-title">AI Data Analyst</div>
            </div>
            """, unsafe_allow_html=True)

            # ── INSIGHTS ──────────────────────────────────
            sub_label("5 Key Insights")

            if st.session_state.get("wx_insights") is None:
                with st.spinner("Analyzing your data..."):
                    try:
                        st.session_state["wx_insights"] = generate_insights(
                            groq_client, _df, _label, _city, _start, _end, _vars
                        )
                        logger.info("Insights generated successfully")
                    except Exception as e:
                        st.error(f"Could not generate insights: {e}")
                        logger.error(f"Insights error: {e}")

            for insight in (st.session_state.get("wx_insights") or []):
                st.markdown(f'<div class="insight-card">{insight}</div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # ── CHAT ──────────────────────────────────────
            sub_label("Chat with your data")
            st.caption(f"Ask anything about your {_label} data for {_city}...")

            if "wx_chat" not in st.session_state:
                st.session_state["wx_chat"] = []

            # Render conversation history
            for msg in st.session_state["wx_chat"]:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])

            # ── Inline chat form (not a fixed footer) ─────
            with st.form("wx_chat_form", clear_on_submit=True):
                col_msg, col_send = st.columns([6, 1])
                with col_msg:
                    user_input = st.text_input(
                        "msg",
                        placeholder=f"Ask about {_city}'s {_label.lower()} data...",
                        label_visibility="collapsed"
                    )
                with col_send:
                    send_btn = st.form_submit_button("Send →", use_container_width=True)

            if send_btn and user_input and user_input.strip():
                trimmed = user_input.strip()
                st.session_state["wx_chat"].append({"role": "user", "content": trimmed})

                with st.spinner("Thinking..."):
                    try:
                        reply = get_chat_response(
                            groq_client,
                            trimmed,
                            st.session_state["wx_chat"][:-1],
                            _df, _label, _city, _start, _end, _vars
                        )
                    except Exception as e:
                        reply = f"Sorry, I ran into an error: {e}"
                        logger.error(f"Chat error: {e}")

                st.session_state["wx_chat"].append({"role": "assistant", "content": reply})
                st.rerun()

# ══════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════
st.divider()
st.markdown(
    '<div class="footer">'
    'Data provided by Open-Meteo &nbsp;·&nbsp; Free for non-commercial use &nbsp;·&nbsp; open-meteo.com'
    '</div>',
    unsafe_allow_html=True
)
