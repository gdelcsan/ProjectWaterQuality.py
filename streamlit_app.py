import streamlit as st
import requests
import pandas as pd

st.markdown("""
    <style>
    /* Set background color for the whole app */
    .stApp {
        background-color: #FBF7F2;
    }

    /* Optionally adjust sidebar background */
    [data-testid="stSidebar"] {
        background-color: #F2ECE4;
    }

    /* Optional: make widgets pop */
    .stButton>button {
        border-radius: 10px;
        font-weight: 600;
    }
    /* --- Global button styling --- */
    .stButton > button {
    color: white;
    background-color: #FACF32;       /* primary color */
    border: none;
    border-radius: 9999px;           /* pill shape */
    padding: 0.6rem 1.2rem;
    font-weight: 600;
    transition: all 0.2s ease-in-out;
    }

    /* --- Hover effect --- */
    .stButton > button:hover {
    background-color: #FAC141;
    transform: scale(1.02);
    }

    /* --- Secondary-style button (use a CSS class marker in Markdown) --- */
    button[data-baseweb="button"]:has(span:contains("Secondary")) {
    background-color: #A2B7DE;       
    }

    /* --- Tertiary-style button --- */
    .header {
    color: #1C349E;
    text-align: center;
    padding: 2.5rem 1rem;
    }
    /* Styling for the selected tab label */
    .stTabs [aria-selected="true"] {
        color: #FAC141;
    }
    .stTabs [aria-selected="false"] {
    color: #000000
    }
    </style>
""", unsafe_allow_html=True)

base_url = 'http://127.0.0.1:8000'

df = pd.read_csv("./database/biscayne_bay_dataset_oct_2022.csv")
st.markdown('<div class="header"><h1>Biscayne Bay Water Quality</h1></div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "Dataset",
    "Idk",
    "Tab",
    "Another Tab"
])

with tab1:
    if st.button("Load Dataset"):
        st.write(df)

with tab2:
    if st.button("Load"):
        response = requests.get(base_url + '/waterQuality/load').json()
        st.json(response)

