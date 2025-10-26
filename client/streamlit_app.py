import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
import numpy as np
import os
import datetime

# configuration
load_dotenv()
"""
FLASK_HOST = "127.0.0.1"
FLASK_PORT = 5050
BASE_URL = f"http://{FLASK_HOST}:{FLASK_PORT}"
"""

#BASE_URL = os.getenv("FLASK_URL")
BASE_URL = "http://127.0.0.1:5050"

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
        color: white;
        background-color: #4DB4F0;
        border: none;
        border-radius: 9999px;
        padding: 0.6rem 1.2rem;
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
df1 = pd.read_csv("./database/2022-oct7.csv")
df2 = pd.read_csv("./database/2021-oct21.csv")
df3 = pd.read_csv("./database/2022-nov16.csv")
df4 = pd.read_csv("./database/2021-dec16.csv")
all_dfs = [df1, df2, df3, df4]

query_parameters = {
    "min_time": None, 
    "max_time": None, 
    "min_temp": None, 
    "max_temp": None, 
    "min_sal": None, 
    "max_sal": None, 
    "min_odo": None, 
    "max_odo": None, 
    "limit": None, 
}

##datasets for drop down
datasets = {
    "Oct 7, 2022": df1,
    "Oct 21, 2021": df2,
    "Nov 16, 2022": df3,
    "Dec 16, 2021": df4,
}

clean_datasets = {
    "Oct 7, 2022": None,
    "Oct 21, 2021": None,
    "Nov 16, 2022": None,
    "Dec 16, 2021": None,
}

def check_exceptions(filepath):
    try:
        df = pd.read_csv(filepath)
    except FileNotFoundError:
        df = pd.DataFrame()
    return df

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

def global_min_max_time(dfs):
    """Return (min, max) across dfs[col], skipping NaNs and missing columns."""
    mins = []
    maxs = []
    for d in dfs:
        if TIMESTAMP_COL in d.columns:
            mins.append(d[TIMESTAMP_COL].min())
            maxs.append(d[TIMESTAMP_COL].max())
    if not mins or not maxs:
        return None, None
    return min(mins), max(maxs)

def convert_to_time(string):
    return datetime.datetime.strptime(string, "%H:%M:%S").time()

def clean(df, filepath):
    # ZScore Formula
    # zscore = ((X - mean) / standard deviation))

    # Specifying columns with only numeric values
    new_df = df.select_dtypes(include='number')

    # Using Formula
    df_zscore = (new_df - new_df.mean()) / new_df.std(ddof=0)

    # Outliers that have |z| > 3
    outliers = (df_zscore.abs() > 3).any(axis=1)

    totalrows = len(df)  # number of rows in data
    removedrows = outliers.sum()  # number of rows removed
    remainingrows = totalrows - removedrows  # remaininggrows

    # Removing outliers
    cleaned_dataset = df[~outliers]

    # Moving "timestamp" column to be the first one
    moved_column = cleaned_dataset.pop("Time hh:mm:ss")
    cleaned_dataset.insert(0, "Time hh:mm:ss", moved_column)

    # Generating csv, printing report, and sending request to flask with json data, to upload to MongoDB
    cleaned_dataset.to_csv(filepath, index = False)
    report = f"{filepath}: Removed {totalrows - removedrows} outliers (from total of {totalrows} rows to remaining rows of {remainingrows})"
    print(report)

    response = requests.post(BASE_URL + "/api/upload", json=(cleaned_dataset.replace({np.nan: None})).to_dict(orient="records"))
    print(f"Status code of uploading to MongoDB: {response.status_code}")
    return cleaned_dataset

# Column aliases to handle inconsistent CSV headers
TEMP_ALIASES = ['Temperature (C)', 'Temperature (°C)', 'Temperature', 'Temp (C)', 'Temperature (c)']
ODO_ALIASES  = ['ODO (mg/L)', 'ODO mg/L', 'ODO', 'ODO_mg_L']
PH_ALIASES   = ['pH', 'PH']
TIMESTAMP_ALIASES = ['Time hh:mm:ss']

TEMP_COL = find_existing_col(all_dfs, TEMP_ALIASES)
ODO_COL  = find_existing_col(all_dfs, ODO_ALIASES)
SAL_COL  = find_existing_col(all_dfs, PH_ALIASES)
TIMESTAMP_COL = find_existing_col(all_dfs, TIMESTAMP_ALIASES)

# Warn clearly if any are missing everywhere
if TEMP_COL is None:
    st.error(f"Temperature column not found. Tried any of: {TEMP_ALIASES}.")
if ODO_COL is None:
    st.error(f"ODO column not found. Tried any of: {ODO_ALIASES}.")
if SAL_COL is None:
    st.error(f"pH/Salinity column not found. Tried any of: {PH_ALIASES}.")
if TIMESTAMP_COL is None:
        st.error(f"Time column not found. Tried any of: {TIMESTAMP_ALIASES}.")

# Control Panel (Sidebar)
st.sidebar.header("Control Panel")

##Dropdown of datasets
selected_dataset_name = st.sidebar.selectbox(
        "Select dataset (Only for first tab):",
        list(datasets.keys()),
        index=0,
)

selected_df = datasets[selected_dataset_name]

st.sidebar.header("Filters")
# Responsible for cleaning csv files if they're initially missing
i = 0
keysList = list(clean_datasets.keys())
for str in ["./database/cleaned_2022-oct7.csv", "./database/cleaned_2021-oct21.csv", "./database/cleaned_2022-nov16.csv", "./database/cleaned_2021-dec16.csv"]:
    df = check_exceptions(str)
    if df.empty:
        df = clean(datasets[keysList[i]], str)
    df[TIMESTAMP_COL] = df[TIMESTAMP_COL].map(convert_to_time)
    clean_datasets.update({keysList[i]: df})
    i += 1

selected_clean = clean_datasets[selected_dataset_name]
all_clean = list(clean_datasets.values())

# 1) Timestamp Slider
if TIMESTAMP_COL:
    time_min_val, time_max_val = global_min_max_time(all_clean)
    if time_min_val is not None:
        time_min, time_max = st.sidebar.slider(
            "Start/End Timestamps",
            time_min_val, time_max_val,
            (time_min_val, time_max_val)
        )
        query_parameters.update({"min_time": time_min})
        query_parameters.update({"max_time": time_max})
    else:
        st.sidebar.info(f"No numeric data found for {TIMESTAMP_COL}.")
        time_min = time_max = None
else:
    time_min = time_max = None

# 2) Temperature slider (only if column found and has data)
if TEMP_COL:
    temp_min_val, temp_max_val = global_min_max(all_clean, TEMP_COL)
    if temp_min_val is not None:
        temp_min, temp_max = st.sidebar.slider(
            f"{TEMP_COL}",
            temp_min_val, temp_max_val,
            (temp_min_val, temp_max_val)
        )
        query_parameters.update({"min_temp": temp_min})
        query_parameters.update({"max_temp": temp_max})
    else:
        st.sidebar.info(f"No numeric data found for {TEMP_COL}.")
        temp_min = temp_max = None
else:
    temp_min = temp_max = None

# 3) Salinity (pH) slider
if SAL_COL:
    sal_min_val, sal_max_val = global_min_max(all_clean, SAL_COL)
    if sal_min_val is not None:
        sal_min, sal_max = st.sidebar.slider(
            f"{SAL_COL}",
            sal_min_val, sal_max_val,
            (sal_min_val, sal_max_val)
        )
        query_parameters.update({"min_sal": sal_min})
        query_parameters.update({"max_sal": sal_max})
    else:
        st.sidebar.info(f"No numeric data found for {SAL_COL}.")
        sal_min = sal_max = None
else:
    sal_min = sal_max = None

# 4) ODO slider
if ODO_COL:
    odo_min_val, odo_max_val = global_min_max(all_clean, ODO_COL)
    if odo_min_val is not None:
        odo_min, odo_max = st.sidebar.slider(
            f"{ODO_COL}",
            odo_min_val, odo_max_val,
            (odo_min_val, odo_max_val)
        )
        query_parameters.update({"min_odo": odo_min})
        query_parameters.update({"max_odo": odo_max})
    else:
        st.sidebar.info(f"No numeric data found for {ODO_COL}.")
        odo_min = odo_max = None
else:
    odo_min = odo_max = None

# 5) Limit Slider
limit = st.sidebar.slider(
    "Limit",
    100,
    1000,
    100
)
query_parameters.update({"limit": limit})

# 6) Skip Text-Box (for pagination)
skip = st.sidebar.number_input("Skip", value = 0)
if skip > 500: st.sidebar.warning("A large skip value may exceed the maximum size of the collection.")

# Streamlit UI
st.markdown('<div class="header"><h1>Biscayne Bay Water Quality</h1><p>2021 - 2022</p></div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Datasets",
    "Filtered Dataset",
    "Plotly Charts",
    "Statistics",
    "Outliers",
    "Code",
    "Contributors"
])

with tab1:
    st.markdown(
        f'<h2 style="color: black;">Clean Dataset for {selected_dataset_name}</h2>',
        unsafe_allow_html=True)
    st.write(selected_clean)
    st.markdown(
        f'<h2 style="color: black;">Original Dataset for {selected_dataset_name}</h2>',
        unsafe_allow_html=True)
    st.write(selected_df)

with tab2:
    st.markdown(
        f'<h2 style="color: black;">Dataset w/ query parameters</h2>',
        unsafe_allow_html=True)
    if st.button("Load", key="filters_button"):
        try:
            url = f"{BASE_URL}/api/observations?"
            for key, value in query_parameters.items():
                if value is not None:
                    url += f"{key}={value}&"
            new_url = url[:-1]

            r = requests.get(new_url, timeout=3)
            r.raise_for_status()
            filters = r.json()
            if (len(filters) != 0):
                count = filters["count"]
                documents = filters["items"]
                st.markdown(
                f'<p style="color: black;">{count} documents found.</p>',
                unsafe_allow_html=True)
                st.dataframe(pd.DataFrame(documents), use_container_width=True)
            else:
                st.error("No documents were found in the collection.")
        except requests.exceptions.RequestException as e:
            st.error(f"Could not reach stats API at {BASE_URL}/api/observations\n{e}")

with tab3:
    st.markdown(f'<h3 style="color:#000000;">{selected_dataset_name} Plotly Charts</h3>', unsafe_allow_html=True)

    df = selected_clean.copy()

    chart_type = st.session_state.get("chart_type", "Map")
    st.markdown(f"<p style='color:black; font-size:0.9rem;'>Active chart: <strong>{chart_type}</strong></p>", unsafe_allow_html=True)
    
    # Common helpers
    all_cols = df.columns.tolist()
    num_cols = df.select_dtypes(include="number").columns.tolist()

    if "chart_type" not in st.session_state:
        st.session_state["chart_type"] = "Map"
        
    bcols = st.columns(3)
    if bcols[0].button("Scatter"):
        st.session_state["chart_type"] = "Scatter"
    if bcols[1].button("Line"):
        st.session_state["chart_type"] = "Line"
    if bcols[2].button("Map"):
        st.session_state["chart_type"] = "Map"

    # Color
    st.markdown("<p style='color:black; font-weight:600; margin-bottom:0;'>Color (optional)</p>", unsafe_allow_html=True)
    color_opt = st.selectbox(
        label="Color (optional)",
        options=["(none)"] + all_cols,
        index=0,
        label_visibility="collapsed"
    )

    # Size
    st.markdown("<p style='color:black; font-weight:600; margin-bottom:0;'>Size (optional)</p>", unsafe_allow_html=True)
    size_opt = st.selectbox(
        label="Size (optional)",
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

    # Scatter or Line plot
    if chart_type != "Map":
        st.markdown("<p style='color:black; font-weight:600; margin-bottom:0;'>X-axis</p>", unsafe_allow_html=True)
        x_col = st.selectbox(
            label="X-axis",
            options=all_cols,
            index=0,
            label_visibility="collapsed"
        )
        st.markdown("<p style='color:black; font-weight:600; margin-bottom:0;'>Y-axis</p>", unsafe_allow_html=True)
        y_col = st.selectbox(
            label="Y-axis",
            options=all_cols,
            index=1 if len(all_cols) > 1 else 0,
            label_visibility="collapsed"
        )

        if chart_type == "Scatter":
            fig = px.scatter(df, x=x_col, y=y_col, **_opt_kwargs())
        elif chart_type == "Line":
            fig = px.line(df, x=x_col, y=y_col, **_opt_kwargs())

        st.plotly_chart(fig, use_container_width=True)

    # Map plot
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

            fig = px.scatter_map(
                df,
                lat=lat_col,
                lon=lon_col,
                hover_data=hover_cols,
                **_opt_kwargs(),
                zoom=zoom
            )
            fig.update_layout(
                map_style="open-street-map",
                margin=dict(l=0, r=0, t=0, b=0)
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
    st.markdown("<p style='color:black; font-size:20px; font-weight:600; margin-bottom:0;'>Column</p>", unsafe_allow_html=True)

    df = selected_clean.copy()
    num_cols = df.select_dtypes(include="number").columns.tolist()
    num_cols.insert(0, "All Columns")
    if not num_cols:
        st.warning("No numeric columns found in the selected dataset.")
    else:
        metric = st.selectbox(
            label="Column",
            options=num_cols,
            index=0,
            key="outliers_column_select", 
            label_visibility="collapsed"
        )

        st.markdown("<p style='color:black; font-size:20px; font-weight:600; margin-bottom:0;'>Method</p>", unsafe_allow_html=True)
        method = st.selectbox(
            label="Method",
            options=["IQR", "Z-score"],
            index=0,
            key="outliers_method_select", 
            label_visibility="collapsed"
        )

        if method == "IQR":
            st.markdown(
            "<p style='color:black; font-size:15px; font-weight:600; margin-bottom:0;'>IQR multiplier</p>",
            unsafe_allow_html=True
            )
            k = st.number_input(
            label="IQR multiplier",
            min_value=0.1, max_value=10.0, value=1.5, step=0.1,
            key="outliers_k_iqr",
            label_visibility="collapsed"  
        )
        else:
            st.markdown(
            "<p style='color:black; font-size:15px; font-weight:600; margin-bottom:0;'>Z-score threshold</p>",
            unsafe_allow_html=True
            )
            k = st.number_input(
            label="Z-score threshold",
            min_value=0.5, max_value=10.0, value=3.0, step=0.1,
            key="outliers_k_zscore",
            label_visibility="collapsed"
            )

    if st.button("Confirm", key="outliers_button"):
            try:
                params = {
                    "field": metric,
                    "method": method.lower(),
                    "k": k,
                }
                url = f"{BASE_URL}/api/outliers?"
                for key, value in params.items():
                    if value is not None:
                        url += f"{key}={value}&"
                new_url = url[:-1]

                r = requests.get(new_url, timeout=3)
                r.raise_for_status()
                outliers = r.json()
                count = outliers["count"]
                if (count != 0):
                    documents = outliers["items"]
                    df = pd.DataFrame(documents)
                    st.markdown(
                    f'<p style="color: black;">{count} outliers found.</p>',
                    unsafe_allow_html=True)
                    if metric != "All Columns":
                        df = df[metric]
                    st.dataframe(df, use_container_width=True)
                else:
                    st.error("No outliers were found in the collection.")
            except requests.exceptions.RequestException as e:
                st.error(f"Could not reach stats API at {BASE_URL}/api/outliers\n{e}")
            
with tab6:
    st.markdown('<h3 style="color:black;">Project Files (Google Drive)</h3>',unsafe_allow_html=True)
    FOLDER_ID = "1_FbQvwhNMpDJTELHY7jhln7kWLelL8MN"
    src = f"https://drive.google.com/embeddedfolderview?id={FOLDER_ID}#list"
    st.components.v1.html(
        f'<iframe src="{src}" style="width:100%; height:600px; border:0;"></iframe>',
        height=620,
        scrolling=True,
    )

with tab7:
    st.markdown("""<a href="https://github.com/gdelcsan/" target="_blank" style="text-decoration: none;"><p style="color:#000000; font-size:20px; font-weight:600;">☆ Gabriela del Cristo</p></a>""",unsafe_allow_html=True)
    st.markdown("""<a href="https://github.com/JasonP1-code/" target="_blank" style="text-decoration: none;"><p style="color:#000000; font-size:20px; font-weight:600;">☆ Jason Pena</p></a>""",unsafe_allow_html=True)
    st.markdown("""<a href="https://github.com/McArthurMilk/" target="_blank" style="text-decoration: none;"><p style="color:#000000; font-size:20px; font-weight:600;">☆ Luis Gutierrez</p></a>""",unsafe_allow_html=True)
    st.markdown("""<a href="#" target="_blank" style="text-decoration: none;"><p style="color:#000000; font-size:20px; font-weight:600;">☆ Lauren Stone</p></a>""",unsafe_allow_html=True)
