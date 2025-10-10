import streamlit as st
import requests
import pandas as pd

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
st.markdown('<div class="header"><h1>Biscayne Bay Water Quality</h1><p>Oct 2022</p></div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "Dataset",
    "Clean Dataset",
    "Plotly Charts",
    "Contributors"
])

with tab1:
    if st.button("Load Dataset"):
        st.write(df)

with tab2:
    if st.button("Load Clean Dataset"):
        response = requests.get(base_url + '/cleandataset/load')
        data = response.json()
        df_cleaned = pd.DataFrame(data)
        ##csv = df_cleaned.to_csv(index=False).encode('utf-8')
        ##st.download_button("Download Cleaned CSV", data=csv, file_name="cleaned_data.csv", mime="text/csv")
        st.write(df_cleaned)

with tab3:
    if st.button("Load Plotly Chart 1"):
        response = requests.get(base_url + '/waterQuality/load').json()
        st.json(response)
    if st.button("Load Plotly Chart 2"):
        response = requests.get(base_url + '/waterQuality/load').json()
        st.json(response)
    if st.button("Load Plotly Chart 3"):
        response = requests.get(base_url + '/waterQuality/load').json()
        st.json(response)

with tab4:
    st.write("Gabriela del Cristo")
    st.write("Jason Pena")
    st.write("Luis Gutierrez")
    st.write("Lauren Stone")





