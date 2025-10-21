import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from numpy.random import default_rng as rng

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

df = pd.read_csv("./database/biscayne_bay_dataset_oct_2022.csv")
clean_df = pd.read_csv("./database/cleaned_data.csv")
st.markdown('<div class="header"><h1>Biscayne Bay Water Quality</h1><p>Oct 2022</p></div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5= st.tabs([
    "Dataset",
    "Clean Dataset",
    "Plotly Charts",
    "Statistics",
    "Contributors"
])

with tab1:
    st.subheader("Original Dataset")
    st.write(df)

with tab2:
    st.subheader("Cleaned Dataset")
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
        st.subheader("Total Celsius on Map")
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
