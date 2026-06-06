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

# ──────────────────────────────────────────
# LOGGING
# ──────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────
st.set_page_config(
    page_title="Weather Data Collector",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ──────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────
DATASET_URL = "https://raw.githubusercontent.com/dr5hn/countries-states-cities-database/master/json/countries+states+cities.json"
DATASET_TIMEOUT = 30       # seconds
API_TIMEOUT     = 20       # seconds
MAX_RETRIES     = 3
RETRY_DELAY     = 2        # seconds between retries

API_URL_MAP = {
    "historical":  "https://archive-api.open-meteo.com/v1/archive",
    "forecast":    "https://api.open-meteo.com/v1/forecast",
    "air_quality": "https://air-quality-api.open-meteo.com/v1/air-quality",
    "marine":      "https://marine-api.open-meteo.com/v1/marine",
    "climate":     "https://climate-api.open-meteo.com/v1/climate"
}

DATA_TYPE_OPTIONS = {
    "🕰️ Historical Weather":        "historical",
    "🔮 Weather Forecast":          "forecast",
    "💨 Air Quality":               "air_quality",
    "🌊 Marine / Ocean":            "marine",
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
        "Wave Height (m)":              "wave_height",
        "Wave Direction (°)":          "wave_direction",
        "Wave Period (s)":             "wave_period",
        "Wind Wave Height (m)":        "wind_wave_height",
        "Wind Wave Direction (°)":     "wind_wave_direction",
        "Wind Wave Period (s)":        "wind_wave_period",
        "Wind Wave Peak Period (s)":   "wind_wave_peak_period",
        "Swell Wave Height (m)":       "swell_wave_height",
        "Swell Wave Direction (°)":    "swell_wave_direction",
        "Swell Wave Period (s)":       "swell_wave_period",
        "Swell Wave Peak Period (s)":  "swell_wave_peak_period",
        "Ocean Current Velocity (m/s)":"ocean_current_velocity",
        "Ocean Current Direction (°)": "ocean_current_direction"
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

# ──────────────────────────────────────────
# HELPER FUNCTIONS
# ──────────────────────────────────────────

@st.cache_data(show_spinner=False)
def load_world_data() -> list | None:
    """Load country/state/city dataset with error handling."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Loading world dataset — attempt {attempt}")
            with urllib.request.urlopen(DATASET_URL, timeout=DATASET_TIMEOUT) as r:
                data = json.loads(r.read())
            logger.info(f"World dataset loaded — {len(data)} countries")
            return data
        except urllib.error.URLError as e:
            logger.error(f"Network error loading dataset: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error loading dataset: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading dataset: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
    return None


def fetch_weather_data(url: str, params: dict) -> tuple[int, dict | None, str]:
    """
    Fetch weather data with retry logic.
    Returns (status_code, data_or_None, error_message).
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"API call to {url} — attempt {attempt} — params: { {k:v for k,v in params.items() if k != 'hourly' and k != 'daily'} }")
            response = requests.get(url, params=params, timeout=API_TIMEOUT)
            logger.info(f"API response status: {response.status_code}")

            if response.status_code == 200:
                return 200, response.json(), ""

            elif response.status_code == 429:
                logger.warning("Rate limited — waiting before retry")
                if attempt < MAX_RETRIES:
                    time.sleep(30)
                    continue
                return 429, None, "Rate limit exceeded. Please wait a moment and try again."

            elif response.status_code == 400:
                return 400, None, f"Bad request — check your parameters. Details: {response.text}"

            else:
                return response.status_code, None, f"API error {response.status_code}: {response.text}"

        except requests.exceptions.Timeout:
            logger.error(f"Request timed out — attempt {attempt}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error — attempt {attempt}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return 0, None, f"Network error: {str(e)}"

    return 0, None, "Failed after multiple retries. Check your internet connection."


def get_variable_key(data_type: str, frequency: str) -> str:
    """Get the correct variable dictionary key."""
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
    """Validate date range. Returns error message or None if valid."""
    if start >= end:
        return "Start date must be before end date."
    if data_type == "historical" and (end - start).days > 365 * 10:
        return "Date range too large — maximum 10 years per request recommended."
    return None


def build_download_filename(city: str, data_type_label: str, start: date, end: date) -> str:
    """Build clean filename for download."""
    clean_label = (
        data_type_label
        .replace("🕰️ ", "").replace("🔮 ", "")
        .replace("💨 ", "").replace("🌊 ", "")
        .replace("🌍 ", "").replace(" ", "_")
        .replace("/", "_")
    )
    clean_city = city.replace(" ", "_").replace(",", "")
    return f"{clean_city}_{clean_label}_{start}_{end}"


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Convert DataFrame to Excel bytes."""
    buffer = BytesIO()
    df.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)
    return buffer.getvalue()


# ──────────────────────────────────────────
# APP HEADER
# ──────────────────────────────────────────
st.title("🌤️ Weather Data Collector")
st.write("Collect any type of weather data for any city in the world — powered by Open-Meteo")

# ──────────────────────────────────────────
# LOAD DATASET
# ──────────────────────────────────────────
with st.spinner("Loading city database... (first load only, cached after)"):
    world_data = load_world_data()

if world_data is None:
    st.error(
        "❌ Failed to load city database after multiple attempts. "
        "Please check your internet connection and refresh the page."
    )
    st.stop()

# ──────────────────────────────────────────
# STEP 1 — LOCATION SELECTION
# ──────────────────────────────────────────
st.header("Step 1 — Select Location")

country_names = [c["name"] for c in world_data]
selected_country = st.selectbox("Select Country", country_names, index=country_names.index("India") if "India" in country_names else 0)

country_data = next((c for c in world_data if c["name"] == selected_country), None)

lat, lon, city = None, None, None

if country_data is None:
    st.error("Country data not found. Please select another country.")
    st.stop()

state_names = [s["name"] for s in country_data.get("states", [])]

if not state_names:
    st.warning(f"No states/provinces found for {selected_country}. This country may not be supported.")
else:
    selected_state = st.selectbox("Select State / Province", state_names)
    state_data = next((s for s in country_data["states"] if s["name"] == selected_state), None)

    if state_data is None:
        st.error("State data not found. Please select another state.")
    else:
        city_names = [c["name"] for c in state_data.get("cities", [])]

        if not city_names:
            st.warning(f"No cities found for {selected_state}. Try a neighbouring state.")
        else:
            selected_city = st.selectbox("Select City", city_names)
            city_data = next((c for c in state_data["cities"] if c["name"] == selected_city), None)

            if city_data is None:
                st.error("City data not found.")
            else:
                try:
                    lat = float(city_data["latitude"])
                    lon = float(city_data["longitude"])
                    city = selected_city
                    st.success(f"✅ {selected_city}, {selected_state}, {selected_country} | Lat: {lat} | Lon: {lon}")
                except (ValueError, KeyError) as e:
                    logger.error(f"Invalid coordinates for {selected_city}: {e}")
                    st.error(f"Invalid coordinates for {selected_city}. Please select another city.")

# ──────────────────────────────────────────
# MAIN FLOW — only if valid location selected
# ──────────────────────────────────────────
if lat and lon and city:

    # ── STEP 2 — DATA TYPE ──
    st.header("Step 2 — Select Data Type")
    data_type_label = st.selectbox("What type of data do you need?", list(DATA_TYPE_OPTIONS.keys()))
    data_type = DATA_TYPE_OPTIONS[data_type_label]
    st.info(DATA_TYPE_DESCRIPTIONS[data_type])

    # ── STEP 3 — DATE RANGE ──
    st.header("Step 3 — Select Date Range")
    today = date.today()

    date_configs = {
        "historical": dict(
            start_val=date(2025, 1, 1), end_val=date(2025, 12, 31),
            min_val=date(1940, 1, 1),   max_val=today - timedelta(days=5)
        ),
        "forecast": dict(
            start_val=today,            end_val=today + timedelta(days=7),
            min_val=today,              max_val=today + timedelta(days=16)
        ),
        "climate": dict(
            start_val=date(2024, 1, 1), end_val=date(2030, 12, 31),
            min_val=date(1950, 1, 1),   max_val=date(2050, 12, 31)
        ),
        "air_quality": dict(
            start_val=date(2025, 1, 1), end_val=today,
            min_val=None,               max_val=None
        ),
        "marine": dict(
            start_val=date(2025, 1, 1), end_val=today,
            min_val=None,               max_val=None
        )
    }

    cfg = date_configs[data_type]
    col1, col2 = st.columns(2)

    with col1:
        date_kwargs = {"value": cfg["start_val"]}
        if cfg["min_val"]: date_kwargs["min_value"] = cfg["min_val"]
        if cfg["max_val"]: date_kwargs["max_value"] = cfg["max_val"]
        start_date = st.date_input("Start date", **date_kwargs)

    with col2:
        date_kwargs = {"value": cfg["end_val"]}
        if cfg["min_val"]: date_kwargs["min_value"] = cfg["min_val"]
        if cfg["max_val"]: date_kwargs["max_value"] = cfg["max_val"]
        end_date = st.date_input("End date", **date_kwargs)

    # ── STEP 4 — FREQUENCY ──
    frequency = None
    step_offset = 0

    if data_type in ["historical", "forecast", "marine"]:
        st.header("Step 4 — Select Frequency")
        frequency = st.radio("What frequency do you need?", ["Daily", "Hourly"])
    elif data_type == "air_quality":
        frequency = "Hourly"
        step_offset = -1
    elif data_type == "climate":
        frequency = "Daily"
        step_offset = -1

    # ── STEP 5 — VARIABLES ──
    step5_num = 5 + step_offset if step_offset else 5
    st.header(f"Step {step5_num} — Select Variables")

    var_key = get_variable_key(data_type, frequency or "Daily")
    # forecast uses same variables as historical
    if data_type == "forecast":
        var_key = f"historical_{(frequency or 'Daily').lower()}"

    all_variables = VARIABLES.get(var_key, {})
    default_var_key = var_key if var_key in DEFAULT_VARS else "historical_daily"
    default_vars = DEFAULT_VARS.get(default_var_key, [])

    if not all_variables:
        st.error("No variables available for this selection.")
        st.stop()

    select_all = st.checkbox("Select All Variables")
    if select_all:
        selected_labels = list(all_variables.keys())
    else:
        valid_defaults = [v for v in default_vars if v in all_variables]
        selected_labels = st.multiselect(
            "Choose variables",
            options=list(all_variables.keys()),
            default=valid_defaults
        )

    selected_variables = [all_variables[label] for label in selected_labels]

    # ── STEP 6 — OUTPUT FORMAT ──
    step6_num = 6 + step_offset if step_offset else 6
    st.header(f"Step {step6_num} — Select Output Format")
    output_format = st.radio("Download as", ["CSV", "Excel"])

    # ── FETCH BUTTON ──
    if st.button("🚀 Fetch Weather Data", type="primary"):

        # validation
        if not selected_variables:
            st.warning("⚠️ Please select at least one variable.")
            st.stop()

        date_error = validate_dates(start_date, end_date, data_type)
        if date_error:
            st.warning(f"⚠️ {date_error}")
            st.stop()

        with st.spinner("Fetching data from Open-Meteo..."):

            url = API_URL_MAP[data_type]

            params = {
                "latitude":   lat,
                "longitude":  lon,
                "start_date": str(start_date),
                "end_date":   str(end_date),
                "timezone":   "auto"
            }

            # set frequency key in params
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
                logger.error(f"Fetch failed — status: {status_code} — error: {error_msg}")
                st.stop()

            if freq_key not in resp_data:
                st.error(f"❌ Expected key '{freq_key}' not found in response. The API may not support this combination.")
                logger.error(f"Missing key '{freq_key}' in response. Keys present: {list(resp_data.keys())}")
                with st.expander("View raw API response"):
                    st.json(resp_data)
                st.stop()

            try:
                df = pd.DataFrame(resp_data[freq_key])
            except Exception as e:
                st.error(f"❌ Failed to parse response into table: {e}")
                logger.error(f"DataFrame creation failed: {e}")
                st.stop()

            if df.empty:
                st.warning("⚠️ API returned no data for this selection. Try a different date range or location.")
                st.stop()

            # success
            st.success(f"✅ Data fetched — {len(df):,} records | {len(df.columns)} columns")
            st.dataframe(df, use_container_width=True)

            # units expander
            units_key = f"{freq_key}_units"
            if units_key in resp_data:
                with st.expander("📐 View column units"):
                    units_df = pd.DataFrame(
                        list(resp_data[units_key].items()),
                        columns=["Column", "Unit"]
                    )
                    st.dataframe(units_df, use_container_width=True)

            # download
            file_name = build_download_filename(city, data_type_label, start_date, end_date)

            if output_format == "CSV":
                try:
                    csv_bytes = df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="⬇️ Download CSV",
                        data=csv_bytes,
                        file_name=f"{file_name}.csv",
                        mime="text/csv"
                    )
                except Exception as e:
                    st.error(f"❌ Failed to generate CSV: {e}")
                    logger.error(f"CSV generation failed: {e}")
            else:
                try:
                    excel_bytes = to_excel_bytes(df)
                    st.download_button(
                        label="⬇️ Download Excel",
                        data=excel_bytes,
                        file_name=f"{file_name}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                except Exception as e:
                    st.error(f"❌ Failed to generate Excel file: {e}")
                    logger.error(f"Excel generation failed: {e}")

# ──────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────
st.divider()
st.caption("Data provided by Open-Meteo | Free for non-commercial use | open-meteo.com")