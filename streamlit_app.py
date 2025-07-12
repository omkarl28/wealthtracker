import streamlit as st
import pandas as pd
import sqlite3
import folium
from streamlit_folium import st_folium
from datetime import datetime
import os
import shutil

# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(page_title="📍 Photo Map Viewer", layout="wide")
st.title("📸 Google Photo + Manual Places Map")

DB_SRC = "photo_locations.db"
DB_PATH = "/tmp/photo_locations.db"

# Copy DB to writable /tmp for Streamlit Cloud
if not os.path.exists(DB_PATH):
    if os.path.exists(DB_SRC):
        shutil.copy(DB_SRC, DB_PATH)
    else:
        st.error("Database not found.")
        st.stop()

# ---------------------------
# LOAD DATA
# ---------------------------
@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT title, latitude, longitude, datetime, filepath FROM photos", conn, parse_dates=['datetime'])
    conn.close()
    return df

df = load_data()

if df.empty:
    st.warning("No data found in the database.")
    st.stop()

# Ensure datetime is valid
df = df.dropna(subset=["datetime"])

if df.empty:
    st.warning("No valid datetime entries found.")
    st.stop()

# ---------------------------
# DATE FILTER
# ---------------------------
min_date = df['datetime'].min().date()
max_date = df['datetime'].max().date()

start_date, end_date = st.date_input(
    "📅 Filter by Date",
    (min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

mask = (df["datetime"].dt.date >= start_date) & (df["datetime"].dt.date <= end_date)
filtered = df[mask]

if filtered.empty:
    st.info("No data found for selected date range.")
    st.stop()

# ---------------------------
# GROUP DATA
# ---------------------------
df_grouped = filtered.groupby(['latitude', 'longitude', 'title']).agg(
    photo_count=('datetime', 'count'),
    last_seen=('datetime', 'max')
).reset_index()

# ---------------------------
# CREATE FOLIUM MAP
# ---------------------------
center_lat = filtered["latitude"].mean()
center_lon = filtered["longitude"].mean()

m = folium.Map(location=[center_lat, center_lon], zoom_start=6, tiles="OpenStreetMap")

for _, row in df_grouped.iterrows():
    folium.CircleMarker(
        location=[row['latitude'], row['longitude']],
        radius=min(max(row['photo_count'] * 1.5, 4), 15),  # scale radius
        popup=folium.Popup(f"""
            <b>{row['title']}</b><br>
            {row['photo_count']} photo(s)<br>
            Last visited: {row['last_seen'].strftime('%Y-%m-%d')}
        """, max_width=250),
        color="crimson",
        fill=True,
        fill_color="crimson",
        fill_opacity=0.75
    ).add_to(m)

# ---------------------------
# DISPLAY MAP
# ---------------------------
st.markdown("### 🗺️ Map View")
st_data = st_folium(m, width=1200, height=700)
