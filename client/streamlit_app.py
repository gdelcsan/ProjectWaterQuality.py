
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
import os

# configuration
load_dotenv()
HOST = os.getenv('FLASK_HOST')
PORT = os.getenv('FLASK_PORT')
BASE_URL = f"http://{HOST}:{PORT}"

st.set_page_config(layout="wide")
st.markdown("""
    <style>
    /* Set background color for the whole app */
    h2, h3
    p, span, div, label,
    .stMarkdown, [data-testid="stMarkdownContainer"] {
        color: #1C349E !important;
    }
    [data-testid="stSidebar"] {
        background-color: #B8E3FC;         
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
    background-color: #B8E3FC;       /* primary color */
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
    /* Styling for tabs */
    .stTabs [aria-selected="true"] {
        color: #FAC141;
    }
    .stTabs [aria-selected="false"] {
    color: #000000
    }
    </style>
""", unsafe_allow_html=True) 

df1 = pd.read_csv("./database/2021-dec16.csv")
df2 = pd.read_csv("./database/2021-oct21.csv")
df3 = pd.read_csv("./database/2022-nov16.csv")
df4 = pd.read_csv("./database/2022-oct7.csv")
clean_df = pd.read_csv("./database/cleaned_data.csv")

##Control Panel
st.sidebar.header("Control Panel")

# 1. Temperature Range Slider
TEMP_COL = 'Temperature (c)'
temp_min_val, temp_max_val = float(df1[TEMP_COL].min()), float(df1[TEMP_COL].max())

temp_min, temp_max = st.sidebar.slider(
    "Temperature range (°C)",
    temp_min_val,
    temp_max_val,
    (temp_min_val, temp_max_val) # Default to full range
)

# 2. Salinity Range Slider
SAL_COL = 'pH'
sal_min_val, sal_max_val = float(df1[SAL_COL].min()), float(df1[SAL_COL].max())

sal_min, sal_max = st.sidebar.slider(
    "Salinity range",
    sal_min_val,
    sal_max_val,
    (sal_min_val, sal_max_val) # Default to full range
)

# 3. ODO Range Slider
ODO_COL = 'ODO mg/L'
odo_min_val, odo_max_val = float(df1[ODO_COL].min()), float(df1[ODO_COL].max())

odo_min, odo_max = st.sidebar.slider(
    "ODO range (mg/L)",
    odo_min_val,
    odo_max_val,
    (odo_min_val, odo_max_val) # Default to full range
)

# 4. Pagination Inputs
limit = st.sidebar.number_input("Rows per page (Limit)", 10, 100, value=25)
page = st.sidebar.number_input("Page number", 1, value=1)

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
