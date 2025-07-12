import streamlit as st
import pandas as pd
import sqlite3
import folium
from streamlit_folium import st_folium
from datetime import datetime

# --------------------
# CONFIG
# --------------------
st.set_page_config(page_title="📍 Photo Location Map", layout="wide")
st.title("📸 Google Photos + Manual Places Map (No Token Needed)")

DB_PATH = "/tmp/photo_locations.db"
LOCAL_DB = "photo_locations.db"

# Copy database to /tmp if not there (for Streamlit Cloud)
import os, shutil
if not os.path.exists(DB_PATH):
    shutil.copy(LOCAL_DB, DB_PATH)

# --------------------
# LOAD DATA
# --------------------
@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT title, latitude, longitude, datetime, filepath FROM photos", conn, parse_dates=['datetime'])
    conn.close()
    return df

df = load_data()

if df.empty:
    st.warning("No data found.")
    st.stop()

# --------------------
# DATE FILTER
# --------------------
min_date = df['datetime'].min().date()
max_date = df['datetime'].max().date()

start_date, end_date = st.date_input(
    "📅 Select date range",
    (min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

mask
