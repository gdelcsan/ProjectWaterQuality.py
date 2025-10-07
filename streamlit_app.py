import streamlit as st
import requests
import pandas as pd

base_url = 'http://127.0.0.1:8000'

st.title("Biscayne Bay Water Quality")

tab1, tab2, tab3, tab4 = st.tabs([
    "Dataset",
    "Idk",
    "Tab",
    "Another Tab"
])

with tab1:
    if st.button("Load Dataset"):
        response = requests.get(base_url + '/cars').json()
        st.json(pd.DataFrame(response))

with tab2:
    if st.button("Load Makes"):
        response = requests.get(base_url + '/cars/makes').json()
        st.json(response)

