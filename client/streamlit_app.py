import os
import threading
import time
from contextlib import suppress

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from numpy.random import default_rng as rng
from datetime import datetime

from flask import Flask, jsonify
from pymongo import MongoClient

# configuration
FLASK_HOST = "127.0.0.1"
FLASK_PORT = 5050
BASE_URL = f"http://{FLASK_HOST}:{FLASK_PORT}"

MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGO_DB = os.getenv("MONGO_DB", "biscaynebay")
MONGO_COLL = os.getenv("MONGO_COLL", "readings")

st.set_page_config(layout="wide")

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
    section[data-testid="stSidebar"] label {
    color: white;
    }
    .stApp {
        background-color: #FBF7F2;
    }   
    /* Make widgets pop */
    .stButton>button {
        border-radius: 10px;
        font-weight: 600;
    }       
    /* Button styling */
    .stButton > button {
    color: white;
    background-color: #4DB4F0;       /* primary color */
    border: none;
    border-radius: 9999px;           /* pill shape */
    padding: 0.6rem 1.2rem;
    font-weight: 600;
    transition: all 0.2s ease-in-out;
    }
    /* Hover effect */
    .stButton > button:hover {
    background-color: #1C349E;
    background-image: linear-gradient(90deg, #1C349E, #4DB4F0);
    transform: scale(1.02);
    }
    /* Title style */
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
    .stTabs [aria-selected="true"] {
    color: 4DB4F0;
    }
    .stTabs [aria-selected="false"] {
    color: #000000;
    }
    </style>
""", unsafe_allow_html=True) 

st.set_page_config(page_title="Biscayne Bay Water Datasets", page_icon="🌊")

df1 = pd.read_csv("./database/2021-dec16.csv")
df2 = pd.read_csv("./database/2021-oct21.csv")
df3 = pd.read_csv("./database/2022-nov16.csv")
df4 = pd.read_csv("./database/2022-oct7.csv")
clean_df = pd.read_csv("./database/cleaned_data.csv")

##Control Panel
st.sidebar.header("Control Panel")

# 1. Temperature Range Slider
TEMP_COL = 'Temperature (°C)'
temp_min_val = min(
    float(df1[TEMP_COL].min()),
    float(df2[TEMP_COL].min()),
    float(df3[TEMP_COL].min()),
    float(df4[TEMP_COL].min()),
    float(clean_df[TEMP_COL].min())
)

temp_max_val = max(
    float(df1[TEMP_COL].max()),
    float(df2[TEMP_COL].max()),
    float(df3[TEMP_COL].max()),
    float(df4[TEMP_COL].max()),
    float(clean_df[TEMP_COL].max())
)

temp_min, temp_max = st.sidebar.slider(
    "Temperature range (°C)",
    temp_min_val,
    temp_max_val,
    (temp_min_val, temp_max_val) # Default to full range
)

# 2. Salinity Range Slider
SAL_COL = 'pH'
sal_min_val = min(
    float(df1[SAL_COL].min()),
    float(df2[SAL_COL].min()),
    float(df3[SAL_COL].min()),
    float(df4[SAL_COL].min()),
    float(clean_df[SAL_COL].min())
)

sal_max_val = max(
    float(df1[SAL_COL].max()),
    float(df2[SAL_COL].max()),
    float(df3[SAL_COL].max()),
    float(df4[SAL_COL].max()),
    float(clean_df[SAL_COL].max())
)

sal_min, sal_max = st.sidebar.slider(
    "Salinity range",
    sal_min_val,
    sal_max_val,
    (sal_min_val, sal_max_val) # Default to full range
)

# 3. ODO Range Slider
ODO_COL = 'ODO mg/L'
odo_min_val = min(
    float(df1[ODO_COL].min()),
    float(df2[ODO_COL].min()),
    float(df3[ODO_COL].min()),
    float(df4[ODO_COL].min()),
    float(clean_df[ODO_COL].min())
)

odo_max_val = max(
    float(df1[ODO_COL].max()),
    float(df2[ODO_COL].max()),
    float(df3[ODO_COL].max()),
    float(df4[ODO_COL].max()),
    float(clean_df[ODO_COL].max())
)

odo_min, odo_max = st.sidebar.slider(
    "ODO range (mg/L)",
    odo_min_val,
    odo_max_val,
    (odo_min_val, odo_max_val) # Default to full range
)

# 4. Pagination Inputs
limit = st.sidebar.number_input("Rows per page (Limit)", 10, 100, value=25)
page = st.sidebar.number_input("Page number", 1, value=1)

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
    """
    Returns basic numeric stats from the cleaned dataset.
    You can customize which columns to summarize below.
    """
    df = clean_df.copy()

    # Pick numeric columns automatically
    num_df = df.select_dtypes(include="number")

    # If you want specific columns only, uncomment and adjust:
    # num_df = df[["pH", "Temperature (C)", "ODO (mg/L)", "Total Water Column (m)"]].apply(pd.to_numeric, errors="coerce")

    summary = (
        num_df.agg(["count", "mean", "std", "min", "max"])
        .transpose()
        .reset_index()
        .rename(columns={"index": "metric"})
    )
    # Round for readability
    for col in ["mean", "std", "min", "max"]:
        if col in summary.columns:
            summary[col] = summary[col].round(3)

    return jsonify(summary.to_dict(orient="records")), 200

def _run_flask():
    # dev server; for production run Flask separately (gunicorn/uvicorn), not threaded in Streamlit
    flask_app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False, use_reloader=False)

def _ensure_flask_running():
    """Start Flask once per Streamlit session and wait until it responds."""
    if "flask_started" not in st.session_state:
        st.session_state.flask_started = False

    if not st.session_state.flask_started:
        t = threading.Thread(target=_run_flask, daemon=True)
        t.start()
        # wait for /health to be available
        health_url = f"{BASE_URL}/health"
        for _ in range(60):  # ~6s max
            with suppress(Exception):
                r = requests.get(health_url, timeout=0.25)
                if r.ok:
                    st.session_state.flask_started = True
                    break
            time.sleep(0.1)

# Streamlit UI
st.markdown('<div class="header"><h1>Biscayne Bay Water Datasets</h1><p>2021 - 2022</p></div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Datasets",
    "Clean Datasets",
    "Plotly Charts",
    "Statistics",
    "Contributors"
])

with tab1:
    if st.button("2021 Datasets"):
        st.markdown('<h3 style="color:#000000;">October 21, 2021</h3>', unsafe_allow_html=True)
        st.write(df2)
        st.markdown('<h3 style="color:#000000;">December 16, 2021</h3>', unsafe_allow_html=True)
        st.write(df1)
    
    if st.button("2022 Datasets"):
        st.markdown('<h3 style="color:#000000;">October 7, 2022</h3>', unsafe_allow_html=True)
        st.write(df4)
        st.markdown('<h3 style="color:#000000;">November 16, 2022</h3>', unsafe_allow_html=True)
        st.write(df3)

with tab2:
    if st.button("2021 Clean Datasets"):
        st.markdown('<h3 style="color:#000000;">Clean Dataset</h3>', unsafe_allow_html=True)
        st.write(clean_df)

with tab3:
    st.markdown('<h3 style="color:#000000;">October 21, 2021</h3>', unsafe_allow_html=True)
    
    if st.button("Load Plotly Chart 1"):
        st.markdown('<h3 style="color:#000000;">pH Correlation with Depth</h3>', unsafe_allow_html=True)
        fig = px.scatter(clean_df, x="Total Water Column (m)", y="pH")
        st.plotly_chart(fig, theme="streamlit", use_container_width=True)

    if st.button("Load Plotly Chart 2"):
        st.markdown('<h3 style="color:#000000;">Temperature in Celsius on Map</h3>', unsafe_allow_html=True)
        fig = px.scatter(
            clean_df, x="latitude", y="longitude",
            color="Temperature (C)", size="ODO (mg/L)",
            hover_data=["pH"]
        )
        st.plotly_chart(fig, use_container_width=True)

    if st.button("Load Plotly Chart 3"):
        st.markdown('<h3 style="color:#000000;">Broad Data Display</h3>', unsafe_allow_html=True)
        st.bar_chart(clean_df, x="pH", y="ODO (mg/L)", color="Temperature (C)", stack=False)

    if st.button("Load Plotly Chart 4"):
        st.markdown('<h3 style="color:#000000;">Oxygen Levels on Detailed Map</h3>', unsafe_allow_html=True)
        fig = px.scatter_mapbox(
            clean_df,
            lat="latitude", lon="longitude",
            hover_name="Total Water Column (m)",
            hover_data=["ODO (mg/L)"],
            color="ODO (mg/L)", size="ODO (mg/L)",
            mapbox_style="open-street-map",
            zoom=17
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<h3 style="color:#000000;">December 16, 2021</h3>', unsafe_allow_html=True)

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
