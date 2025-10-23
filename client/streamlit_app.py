import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from numpy.random import default_rng as rng
from datetime import datetime

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

##Control Panel
st.sidebar.header("Control Panel")

# 1. Temperature Range Slider
TEMP_COL = 'Temperature (C)'
temp_min_val, temp_max_val = float(df[TEMP_COL].min()), float(df[TEMP_COL].max())

temp_min, temp_max = st.sidebar.slider(
    "Temperature range (°C)",
    temp_min_val,
    temp_max_val,
    (temp_min_val, temp_max_val) # Default to full range
)

# 2. Salinity Range Slider
SAL_COL = 'pH'
sal_min_val, sal_max_val = float(df[SAL_COL].min()), float(df[SAL_COL].max())

sal_min, sal_max = st.sidebar.slider(
    "Salinity range",
    sal_min_val,
    sal_max_val,
    (sal_min_val, sal_max_val) # Default to full range
)

# 3. ODO Range Slider
ODO_COL = 'ODO (mg/L)'
odo_min_val, odo_max_val = float(df[ODO_COL].min()), float(df[ODO_COL].max())

odo_min, odo_max = st.sidebar.slider(
    "ODO range (mg/L)",
    odo_min_val,
    odo_max_val,
    (odo_min_val, odo_max_val) # Default to full range
)

# 4. Pagination Inputs
limit = st.sidebar.number_input("Rows per page (Limit)", 10, 100, value=25)
page = st.sidebar.number_input("Page number", 1, value=1)


#OG Filter
filtered_data = df[
    (df[TEMP_COL] >= temp_min) &
    (df[TEMP_COL] <= temp_max) &
    (df[SAL_COL] >= sal_min) &
    (df[SAL_COL] <= sal_max) &
    (df[ODO_COL] >= odo_min) &
    (df[ODO_COL] <= odo_max)
].copy()

#Cleaned filter
clean_filtered_data = clean_df[
    (clean_df[TEMP_COL] >= temp_min) &
    (clean_df[TEMP_COL] <= temp_max) &
    (clean_df[SAL_COL] >= sal_min) &
    (clean_df[SAL_COL] <= sal_max) &
    (clean_df[ODO_COL] >= odo_min) &
    (clean_df[ODO_COL] <= odo_max)
].copy()

#Pagination
total_rows = len(filtered_data)
total_clean_rows = len(clean_filtered_data)

#starting index for the current page
start_idx = (page - 1) * limit
clean_start_idx = (page - 1) * limit

#ending index
end_idx = start_idx + limit
clean_end_idx = clean_start_idx + limit

# bounds for OG
if start_idx >= total_rows and total_rows > 0:
    st.sidebar.warning(f"Page {page} is empty for Original Dataset. Resetting to Page 1.")
    start_idx = 0
    page = 1
elif total_rows == 0:
    st.sidebar.info("The applied filters returned no data in Original Dataset.")
    start_idx = 0

#bounds for Cleaned
if clean_start_idx >= total_clean_rows and total_clean_rows > 0:
    clean_start_idx = (total_clean_rows // limit) * limit
elif total_clean_rows == 0:
    st.sidebar.info("The applied filters returned no data in Clean Dataset.")
    clean_start_idx = 0

#Filtered OG data and Filtered Cleaned data ## USE THESE AND NOT THE UPLOADED ON TOP TO
#USE FILTER
og_filtered_page = filtered_data.iloc[start_idx:end_idx]
cleaned_filtered_page = clean_filtered_data.iloc[clean_start_idx:clean_end_idx]

tab1, tab2, tab3, tab4, tab5= st.tabs([
    "Dataset",
    "Clean Dataset",
    "Plotly Charts",
    "Statistics",
    "Contributors"
])

with tab1:
        st.subheader("Original Dataset")
        st.write(og_filtered_page)

with tab2:
    st.subheader("Cleaned Dataset")
    st.write(cleaned_filtered_page)

with tab3:
    if st.button("Load Plotly Chart 1"):
        st.subheader("pH Correlation with Temperature (C)")
        fig = px.scatter(
        cleaned_filtered_page,
        x="Temperature (C)", 
        y="pH"
        )
        st.plotly_chart(fig, theme="streamlit", use_container_width=True)

    if st.button("Load Plotly Chart 2"):
        st.subheader("Total Meters in Depth on Map")
        fig = px.scatter(
        cleaned_filtered_page, x="latitude", y="longitude", color="Total Water Column (m)", size="ODO (mg/L)", hover_data=["pH"])
        event = st.plotly_chart(fig, key="iris", on_select="rerun")

    if st.button("Load Plotly Chart 3"):
        st.subheader("IDK")
        st.bar_chart(cleaned_filtered_page, x="pH", y="ODO (mg/L)", color="Temperature (C)", stack=False)
   
with tab4:
        st.dataframe(cleaned_filtered_page.describe())

with tab5:
    st.write("Gabriela del Cristo")
    st.write("Jason Pena")
    st.write("Luis Gutierrez")
    st.write("Lauren Stone")

