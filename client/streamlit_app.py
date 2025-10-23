import os
import threading
import time
from contextlib import suppress

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from numpy.random import default_rng as rng

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
    /* Base light mode */
    .stApp {
        background-color: #FBF7F2;
    }
    .stButton>button {
        border-radius: 10px;
        font-weight: 600;
    }
    .stButton > button {
        color: white;
        background-color: #FACF32;
        border: none;
        border-radius: 9999px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
    }
    .stButton > button:hover {
        background-color: #FAC141;
        transform: scale(1.02);
    }
    button[data-baseweb="button"]:has(span:contains("Secondary")) {
        background-color: #A2B7DE;       
    }
    .header {
        color: #1C349E;
        text-align: center;
        padding: 2.5rem 1rem;
    }
    .stTabs [aria-selected="true"] {
        color: #FAC141;
    }
    .stTabs [aria-selected="false"] {
        color: #000000;
    }

    /* ===== Dark mode overrides ===== */
    @media (prefers-color-scheme: dark) {
        .stApp {
            background-color: #1E1E1E;
        }
        .header {
            color: #FACF32;   /* brighter for contrast */
        }
        .stButton > button {
            background-color: #FACF32;
            color: black;     /* better contrast on yellow background */
        }
        .stButton > button:hover {
            background-color: #FAC141;
        }
        .stTabs [aria-selected="true"] {
            color: #FAC141;
        }
        .stTabs [aria-selected="false"] {
            color: #FFFFFF;
        }
    }
    </style>
""", unsafe_allow_html=True)

base_url = 'http://127.0.0.1:5050'

df1 = pd.read_csv("./database/2021-dec16.csv")
df2 = pd.read_csv("./database/2021-oct21.csv")
df3 = pd.read_csv("./database/2022-nov16.csv")
df4 = pd.read_csv("./database/2022-oct7.csv")
clean_df = pd.read_csv("./database/cleaned_data.csv")

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
st.markdown('<div class="header"><h1>Biscayne Bay Water Quality</h1><p>2021 - 2022</p></div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Datasets",
    "Clean Datasets",
    "Plotly Charts",
    "Statistics",
    "Contributors"
])

with tab1:
    st.subheader("October 21, 2021")
    st.write(df2)
    st.subheader("December 16, 2021")
    st.write(df1)
    st.subheader("October 7, 2022")
    st.write(df4)
    st.subheader("November 16, 2022")
    st.write(df3)

with tab2:
    st.subheader("Clean Dataset")
    st.write(clean_df)

with tab3:
    if st.button("Load Plotly Chart 1"):
        st.subheader("pH Correlation with Depth")
        fig = px.scatter(clean_df, x="Total Water Column (m)", y="pH")
        st.plotly_chart(fig, theme="streamlit", use_container_width=True)

    if st.button("Load Plotly Chart 2"):
        st.subheader("Temperature in Celsius on Map")
        fig = px.scatter(
            clean_df, x="latitude", y="longitude",
            color="Temperature (C)", size="ODO (mg/L)",
            hover_data=["pH"]
        )
        st.plotly_chart(fig, use_container_width=True)

    if st.button("Load Plotly Chart 3"):
        st.subheader("Broad Data Display")
        st.bar_chart(clean_df, x="pH", y="ODO (mg/L)", color="Temperature (C)", stack=False)

    if st.button("Load Plotly Chart 4"):
        st.subheader("Oxygen Levels on Detailed Map")
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
    st.write("Gabriela del Cristo")
    st.write("Jason Pena")
    st.write("Luis Gutierrez")
    st.write("Lauren Stone")
