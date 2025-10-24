import os
import threading
import time
from contextlib import suppress
from datetime import datetime

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from numpy.random import default_rng as rng
import numpy as np

from flask import Flask, jsonify
from pymongo import MongoClient

# Configuration
FLASK_HOST = "127.0.0.1"
FLASK_PORT = 5050
BASE_URL = f"http://{FLASK_HOST}:{FLASK_PORT}"

MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGO_DB = os.getenv("MONGO_DB", "biscaynebay")
MONGO_COLL = os.getenv("MONGO_COLL", "readings")

st.set_page_config(page_title="Biscayne Bay Water Datasets", page_icon="🌊", layout="wide")

# Style
st.markdown("""
    <style>
    /* Sidebar container */
    section[data-testid="stSidebar"] {
        color: #ffffff;
        text-align: center;
        background-color: #B8E3FC;
        background-image: linear-gradient(120deg, #4158C4, #4DB4F0);
        border-right: 1px solid rgba(27,31,35,0.1);  
    }
    section[data-testid="stSidebar"] label { color: white; }

    .stApp { background-color: #FBF7F2; }

    /* Buttons */
    .stButton > button {
    background-color: #4DB4F0;
    color: white;
    border: none;
    border-radius: 9999px;
    padding: 0.35rem 0.8rem;
    font-weight: 600;
    transition: all 0.2s ease-in-out;
    }

    .stButton > button:hover {
    background-color: #1C349E;
    background-image: linear-gradient(90deg, #1C349E, #4DB4F0);
    transform: scale(1.02);
    }

    /* Title gradient */
    .header {
        text-align: center;
        padding: 2.5rem 1rem;
        font-size: 2.5rem;             
        font-weight: 800;
        background: linear-gradient(90deg, #1C349E, #4DB4F0); 
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    /* Tabs */
    .stTabs [aria-selected="false"] { color: #000000; 
    }

    /* Make dropdown background white */
    div[data-baseweb="select"] > div {
        background-color: white !important;
        color: black !important;
        border-radius: 8px !important;
        border: 1px solid #ccc !important;
    }
    
    </style>
""", unsafe_allow_html=True)

# Load data
df2 = pd.read_csv("./database/2021-oct21.csv")
df4 = pd.read_csv("./database/2021-dec16.csv")
df1 = pd.read_csv("./database/2022-oct7.csv")
df3 = pd.read_csv("./database/2022-nov16.csv")

#clean_df = pd.read_csv("./database/cleaned_data.csv")

df2clean = pd.read_csv("./database/cleaned_2021-oct21.csv")
df4clean = pd.read_csv("./database/cleaned_2021-dec16.csv")
df1clean = pd.read_csv("./database/cleaned_2022-oct7.csv")
df3clean = pd.read_csv("./database/cleaned_2022-nov16.csv")

all_dfs = [df1, df2, df3, df4]

##datasets for drop down
datasets = {
    "Original: Oct 21, 2021": df2,
    "Original: Dec 16, 2021": df4,
    "Original: Oct 7, 2022": df1,
    "Original: Nov 16, 2022": df3,
    "Cleaned: Oct 21, 2021": df2clean,
    "Cleaned: Dec 16, 2021": df4clean,
    "Cleaned: Oct 7, 2022": df1clean,
    "Cleaned: Nov 16, 2022": df3clean,
}

# Helpers: resolve column names & numeric ranges safely
def find_existing_col(dfs, aliases):
    """Return the first alias that exists in ANY dataframe; else None."""
    for name in aliases:
        for d in dfs:
            if name in d.columns:
                return name
    return None

def numeric_series(df, col):
    """Return numeric series (coerced) for df[col], or empty Series if not present."""
    if col not in df.columns:
        return pd.Series(dtype="float64")
    return pd.to_numeric(df[col], errors="coerce")

def global_min_max(dfs, col):
    """Return (min, max) across dfs[col], skipping NaNs and missing columns."""
    vals = []
    for d in dfs:
        if col in d.columns:
            s = numeric_series(d, col).dropna()
            if not s.empty:
                vals.extend(s.tolist())
    if not vals:
        return None, None
    return float(pd.Series(vals).min()), float(pd.Series(vals).max())

# Column aliases to handle inconsistent CSV headers
TEMP_ALIASES = ['Temperature (C)', 'Temperature (°C)', 'Temperature', 'Temp (C)', 'Temperature (c)']
ODO_ALIASES  = ['ODO (mg/L)', 'ODO mg/L', 'ODO', 'ODO_mg_L']
PH_ALIASES   = ['pH', 'PH']

TEMP_COL = find_existing_col(all_dfs, TEMP_ALIASES)
ODO_COL  = find_existing_col(all_dfs, ODO_ALIASES)
SAL_COL  = find_existing_col(all_dfs, PH_ALIASES)

# Warn clearly if any are missing everywhere
if TEMP_COL is None:
    st.error(f"Temperature column not found. Tried any of: {TEMP_ALIASES}.")
if ODO_COL is None:
    st.error(f"ODO column not found. Tried any of: {ODO_ALIASES}.")
if SAL_COL is None:
    st.error(f"pH/Salinity column not found. Tried any of: {PH_ALIASES}.")

# Control Panel (Sidebar)
st.sidebar.header("Control Panel")

##Dropdown of datasets
selected_dataset_name = st.sidebar.selectbox(
        "Select dataset:",
        list(datasets.keys()),
        index=0
    )
selected_df = datasets[selected_dataset_name]

# 1) Temperature slider (only if column found and has data)
if TEMP_COL:
    temp_min_val, temp_max_val = global_min_max(all_dfs, TEMP_COL)
    if temp_min_val is not None:
        temp_min, temp_max = st.sidebar.slider(
            f"{TEMP_COL}",
            temp_min_val, temp_max_val,
            (temp_min_val, temp_max_val)
        )
    else:
        st.sidebar.info(f"No numeric data found for {TEMP_COL}.")
        temp_min = temp_max = None
else:
    temp_min = temp_max = None

# 2) Salinity (pH) slider
if SAL_COL:
    sal_min_val, sal_max_val = global_min_max(all_dfs, SAL_COL)
    if sal_min_val is not None:
        sal_min, sal_max = st.sidebar.slider(
            f"{SAL_COL}",
            sal_min_val, sal_max_val,
            (sal_min_val, sal_max_val)
        )
    else:
        st.sidebar.info(f"No numeric data found for {SAL_COL}.")
        sal_min = sal_max = None
else:
    sal_min = sal_max = None

# 3) ODO slider
if ODO_COL:
    odo_min_val, odo_max_val = global_min_max(all_dfs, ODO_COL)
    if odo_min_val is not None:
        odo_min, odo_max = st.sidebar.slider(
            f"{ODO_COL}",
            odo_min_val, odo_max_val,
            (odo_min_val, odo_max_val)
        )
    else:
        st.sidebar.info(f"No numeric data found for {ODO_COL}.")
        odo_min = odo_max = None
else:
    odo_min = odo_max = None

# 4) Pagination Inputs
#limit = st.sidebar.number_input("Rows per page (Limit)", 10, 100, value=25)
#page = st.sidebar.number_input("Page number", 1, value=1)

# Flask API (background)
flask_app = Flask(__name__)

try:
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=500)
    _ = mongo_client.server_info()  # quick ping
    mongo_db = mongo_client[MONGO_DB]
    mongo_coll = mongo_db[MONGO_COLL]
    MONGO_OK = True
except Exception:
    mongo_client = None
    mongo_db = None
    mongo_coll = None
    MONGO_OK = False

@flask_app.get("/health")
def health():
    status = {"status": "ok", "mongo": "up" if MONGO_OK else "down"}
    return jsonify(status), 200

@flask_app.get("/api/stats")
def api_stats():
    """Basic numeric stats from cleaned dataset (auto-select numeric cols)."""
    df = clean_df.copy()
    num_df = df.select_dtypes(include="number")
    summary = (
        num_df.agg(["count", "mean", "std", "min", "max"])
        .transpose()
        .reset_index()
        .rename(columns={"index": "metric"})
    )
    for col in ["mean", "std", "min", "max"]:
        if col in summary.columns:
            summary[col] = summary[col].round(3)
    return jsonify(summary.to_dict(orient="records")), 200

def _run_flask():
    flask_app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False, use_reloader=False)

def _ensure_flask_running():
    if "flask_started" not in st.session_state:
        st.session_state.flask_started = False
    if not st.session_state.flask_started:
        t = threading.Thread(target=_run_flask, daemon=True)
        t.start()
        health_url = f"{BASE_URL}/health"
        for _ in range(60):  # ~6s max
            with suppress(Exception):
                r = requests.get(health_url, timeout=0.25)
                if r.ok:
                    st.session_state.flask_started = True
                    break
            time.sleep(0.1)

# UI
st.markdown('<div class="header"><h1>Biscayne Bay Water Datasets</h1><p>2021 - 2022</p></div>', unsafe_allow_html=True)

tab1, tab3, tab4, tab5 = st.tabs([
    "Datasets",
    "Plotly Charts",
    "Statistics",
    "Contributors"
])

with tab1:

    st.markdown(
        f'<h2 style="color: black;">Dataset for {selected_dataset_name}</h2>',
        unsafe_allow_html=True)
    st.write(selected_df)

    #st.subheader("October 21, 2021")
    #st.write(df2)
    #st.subheader("December 16, 2021")
    #st.write(df1)
    #st.subheader("October 7, 2022")
    #st.write(df4)
    #st.subheader("November 16, 2022")
    #st.write(df3)

#with tab2:
    #if st.button("2021 Clean Datasets"):
        #st.markdown('<h3 style="color:#000000;">Clean Dataset</h3>', unsafe_allow_html=True)
        #st.write(clean_df)


    #st.markdown(
       # f'<h2 style="color: black;">Cleaned Dataset for {selected_dataset_name}</h2>',
        #unsafe_allow_html=True)
    #st.write(selected_df )


with tab3:
    st.markdown(f'<h3 style="color:#000000;">{selected_dataset_name}</h3>', unsafe_allow_html=True)

    df = selected_df.copy()
    
    # Common helpers
    all_cols = df.columns.tolist()
    num_cols = df.select_dtypes(include="number").columns.tolist()

    if "chart_type" not in st.session_state:
        st.session_state["chart_type"] = "Map"  # default

    if st.button("Scatter", key="btn_scatter"):
        st.session_state["chart_type"] = "Scatter"
        
    if st.button("Line", key="btn_line"):
        st.session_state["chart_type"] = "Line"
        
    if st.button("Bar", key="btn_bar"):
        st.session_state["chart_type"] = "Bar"

    if st.button("Map", key="btn_map"):
        st.session_state["chart_type"] = "Map"

    chart_type = st.session_state["chart_type"]
    st.markdown(f"<p style='color:black; font-size:0.9rem;'>Active chart: <strong>{chart_type}</strong></p>",unsafe_allow_html=True)

    st.markdown("<p style='color:black; font-weight:600; margin-bottom:0;'>Color (optional)</p>", unsafe_allow_html=True)
    color_opt = st.selectbox(
    label="Color (optional)",
    options=["(none)"] + all_cols,
    index=0,
    label_visibility="collapsed" 
    )

    st.markdown("<p style='color:black; font-weight:600; margin-bottom:0;'>Size (optional/numeric)</p>", unsafe_allow_html=True)
    size_opt = st.selectbox(
    label="Size (optional/numeric)",
    options=["(none)"] + num_cols,
    index=0,
    label_visibility="collapsed" 
    )

    def _opt_kwargs():
        kwargs = {}
        if color_opt != "(none)":
            kwargs["color"] = color_opt
        if size_opt != "(none)":
            kwargs["size"] = size_opt
        return kwargs

    if chart_type != "Map":
        x_col = st.selectbox("X-axis", all_cols, index=0)
        y_col = st.selectbox("Y-axis", all_cols, index=1 if len(all_cols) > 1 else 0)

        if chart_type == "Scatter":
            fig = px.scatter(df, x=x_col, y=y_col, **_opt_kwargs())
        elif chart_type == "Line":
            fig = px.line(df, x=x_col, y=y_col, **_opt_kwargs())
        else:  # "Bar"
            fig = px.bar(df, x=x_col, y=y_col, **_opt_kwargs())

        st.plotly_chart(fig, use_container_width=True)

    else:
        LAT_ALIASES = ["Latitude", "Lat", "latitude", "lat"]
        LON_ALIASES = ["Longitude", "Lon", "Lng", "longitude", "lon", "lng"]

        lat_col = find_existing_col([df], LAT_ALIASES)
        lon_col = find_existing_col([df], LON_ALIASES)

        if not lat_col or not lon_col:
            st.warning(
                "To plot a map, your dataset must have latitude/longitude columns. "
                f"Tried latitude aliases: {LAT_ALIASES}; longitude aliases: {LON_ALIASES}."
            )
        else:
            st.markdown("<p style='color:black; font-weight:600; margin-bottom:0;'>Hover data (optional)</p>", unsafe_allow_html=True)
            hover_cols = st.multiselect(
            label="Hover data (optional)",
            options=["(none)"] + [c for c in all_cols if c not in {lat_col, lon_col}],
            default=[],
            label_visibility="collapsed" 
            )

            st.markdown("<p style='color:black; font-weight:600; margin-bottom:0;'>Map zoom</p>", unsafe_allow_html=True)
            zoom = st.slider(
            label="Map zoom",
            min_value=1,
            max_value=18,
            value=17,
            label_visibility="collapsed" 
            )

            fig = px.scatter_mapbox(
                df,
                lat=lat_col,
                lon=lon_col,
                hover_data=hover_cols,
                **_opt_kwargs(),
                zoom=zoom
            )
            fig.update_layout(mapbox_style="open-street-map", margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, use_container_width=True)

with tab4:
    # Start Flask (if not already) and call the API safely
    _ensure_flask_running()
    try:
        r = requests.get(f"{BASE_URL}/api/stats", timeout=3)
        r.raise_for_status()
        stats = r.json()
        st.dataframe(pd.DataFrame(stats), use_container_width=True)
    except requests.exceptions.RequestException as e:
        st.error(f"Could not reach stats API at {BASE_URL}/api/stats\n{e}")
        
with tab5:
    st.markdown("""<a href="https://github.com/gdelcsan/" target="_blank" style="text-decoration: none;"><p style="color:#000000; font-size:20px; font-weight:600;">☆ Gabriela del Cristo</p></a>""",unsafe_allow_html=True)
    st.markdown("""<a href="https://github.com/JasonP1-code/" target="_blank" style="text-decoration: none;"><p style="color:#000000; font-size:20px; font-weight:600;">☆ Jason Pena</p></a>""",unsafe_allow_html=True)
    st.markdown("""<a href="https://github.com/McArthurMilk/" target="_blank" style="text-decoration: none;"><p style="color:#000000; font-size:20px; font-weight:600;">☆ Luis Gutierrez</p></a>""",unsafe_allow_html=True)
    st.markdown("""<a href="#" target="_blank" style="text-decoration: none;"><p style="color:#000000; font-size:20px; font-weight:600;">☆ Lauren Stone</p></a>""",unsafe_allow_html=True)
