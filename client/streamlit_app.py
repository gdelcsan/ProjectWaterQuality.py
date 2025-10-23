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

# Config
FLASK_HOST = "127.0.0.1"
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("MONGO_DB", "mydatabase")
COLL_NAME = os.getenv("MONGO_COLL", "users")

# Create Flask app and Mongo client
flask_app = Flask(__name__)
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
collection = db[COLL_NAME]

@flask_app.get("/health")
def health():
    return {"status": "ok"}, 200

@flask_app.get("/data")
def get_data():
    # Return all docs without _id
    docs = list(collection.find({}, {"_id": 0}))
    return jsonify(docs), 200

def run_flask():
    # Use Flask’s built-in server for dev. (For prod, run Flask separately.)
    flask_app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False, use_reloader=False)

def ensure_flask_running():
    """Start Flask once per Streamlit session and wait until it’s responsive."""
    if "flask_started" not in st.session_state:
        st.session_state.flask_started = False

    if not st.session_state.flask_started:
        t = threading.Thread(target=run_flask, daemon=True)
        t.start()
        # Wait for the /health endpoint to come up
        health_url = f"http://{FLASK_HOST}:{FLASK_PORT}/health"
        for _ in range(50):  # ~5s max
            with suppress(Exception):
                r = requests.get(health_url, timeout=0.2)
                if r.ok:
                    st.session_state.flask_started = True
                    break
            time.sleep(0.1)
            
st.set_page_config(layout="wide")

st.markdown("""
    <style>
    /* Set background color for the whole app */
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
    background-color: #FACF32;       /* primary color */
    border: none;
    border-radius: 9999px;           /* pill shape */
    padding: 0.6rem 1.2rem;
    font-weight: 600;
    transition: all 0.2s ease-in-out;
    }

    /* Hover effect */
    .stButton > button:hover {
    background-color: #FAC141;
    transform: scale(1.02);
    }

    /* Secondary-style button */
    button[data-baseweb="button"]:has(span:contains("Secondary")) {
    background-color: #A2B7DE;       
    }

    /* Title style */
    .header {
    color: #1C349E;
    text-align: center;
    padding: 2.5rem 1rem;
    }
            
    /* Styling for tabs */
    .stTabs [aria-selected="true"] {
        color: #FAC141;
    }
    .stTabs [aria-selected="false"] {
    color: #000000
    }
    </style>
""", unsafe_allow_html=True)

base_url = 'http://127.0.0.1:5050'

df1 = pd.read_csv("./database/2021-dec16.csv")
df2 = pd.read_csv("./database/2021-oct21.csv")
df3 = pd.read_csv("./database/2022-nov16.csv")
df4 = pd.read_csv("./database/2022-oct7.csv")
clean_df = pd.read_csv("./database/cleaned_data.csv")
st.markdown('<div class="header"><h1>Biscayne Bay Water Quality</h1><p>2021 - 2022</p></div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5= st.tabs([
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
        fig = px.scatter(
        clean_df, 
        x="Total Water Column (m)", 
        y="pH"
        )
        st.plotly_chart(fig, theme="streamlit", use_container_width=True)

    if st.button("Load Plotly Chart 2"):
        st.subheader("Temperature in Celsius on Map")
        fig = px.scatter(
        clean_df, x="latitude", y="longitude", color="Temperature (C)", size="ODO (mg/L)", hover_data=["pH"])
        event = st.plotly_chart(fig, key="iris", on_select="rerun")

    if st.button("Load Plotly Chart 3"):
        st.subheader("Broad Data Display")
        st.bar_chart(clean_df, x="pH", y="ODO (mg/L)", color="Temperature (C)", stack=False)

    if st.button("Load Plotly Chart 4"):
        st.subheader("Oxygen Levels on Detailed Map")
        fig = px.scatter_mapbox(clean_df,
                            lat="latitude",
                            lon="longitude",
                            hover_name="Total Water Column (m)",
                            hover_data=["ODO (mg/L)"],
                            color="ODO (mg/L)", 
                            size="ODO (mg/L)", 
                            mapbox_style="open-street-map",
                            zoom=17) 
        st.plotly_chart(fig, use_container_width=True)
   
with tab4:
    response = requests.get(base_url + "/api/stats").json()
    st.dataframe(pd.DataFrame(response))

with tab5:
    st.write("Gabriela del Cristo")
    st.write("Jason Pena")
    st.write("Luis Gutierrez")
    st.write("Lauren Stone")
