import streamlit as st
import pandas as pd
import sqlite3
import pydeck as pdk
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

st.set_page_config(page_title="📍 Google Photo + Places Map", layout="wide")
st.title("📸 Map of Photo Locations and Places")

DB_PATH = "photo_locations.db"

# --- DB Utilities ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            datetime TEXT,
            latitude REAL,
            longitude REAL,
            filepath TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_place(place_name, lat, lon, dt="2024-01-01 00:00:00", source="manual_entry"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO photos (title, datetime, latitude, longitude, filepath)
        VALUES (?, ?, ?, ?, ?)
    """, (place_name, dt, lat, lon, source))
    conn.commit()
    conn.close()

@st.cache_data
def load_photo_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT latitude, longitude, datetime, title, filepath FROM photos", conn, parse_dates=["datetime"])
    conn.close()
    return df

# --- Initialize DB ---
init_db()

# --- Add new place ---
st.sidebar.header("📍 Add a New Place")
place_input = st.sidebar.text_input("Enter place name (e.g., Munnar)")
submit = st.sidebar.button("Add Place")

if submit and place_input.strip():
    geolocator = Nominatim(user_agent="streamlit-place-adder", timeout=10)
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
    location = geocode(f"{place_input}, India")

    if location:
        lat, lon = location.latitude, location.longitude
        insert_place(place_input.title(), lat, lon)
        st.sidebar.success(f"✅ Added: {place_input.title()} ({lat:.3f}, {lon:.3f})")
        st.experimental_rerun()
    else:
        st.sidebar.error(f"Could not geocode location: {place_input}")

# --- Load data and filter ---
df = load_photo_data()

if df.empty:
    st.warning("No data found.")
    st.stop()

# Date filter
min_date = df["datetime"].min().date()
max_date = df["datetime"].max().date()

start_date, end_date = st.date_input(
    "📅 Filter by Date",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

mask = (df["datetime"].dt.date >= start_date) & (df["datetime"].dt.date <= end_date)
filtered = df[mask]

if filtered.empty:
    st.info("No photo locations found in this date range.")
    st.stop()

# Group data
df_grouped = filtered.groupby(['latitude', 'longitude', 'title']).agg(
    photo_count=('datetime', 'count'),
    last_seen=('datetime', 'max')
).reset_index()

df_grouped["tooltip"] = df_grouped.apply(
    lambda row: f"<b>{row['title']}</b><br/>{row['photo_count']} photos<br/>{row['last_seen'].strftime('%Y-%m-%d')}",
    axis=1
)

# Zoom-aware map
view_state = pdk.ViewState(
    latitude=filtered["latitude"].mean(),
    longitude=filtered["longitude"].mean(),
    zoom=5,
    pitch=0
)

scatter_layer = pdk.Layer(
    "ScatterplotLayer",
    data=df_grouped,
    get_position='[longitude, latitude]',
    get_radius="photo_count",
    radius_scale=3000,
    radius_min_pixels=3,
    radius_max_pixels=40,
    get_fill_color="[255, 80, 80, 160]",
    pickable=True,
    auto_highlight=True,
)

st.pydeck_chart(pdk.Deck(
    map_style="mapbox://styles/mapbox/streets-v11",
    initial_view_state=view_state,
    layers=[scatter_layer],
    tooltip={"html": "{tooltip}", "style": {"backgroundColor": "white", "color": "black"}}
))
