import streamlit as st
import pandas as pd

# Set the title of the application
st.title("Data Upload Application")

st.header("Upload Required Excel Files")

# Step 1: Upload Yesterday DCDB-01 Primary Disconnect History
st.subheader("1. Yesterday DCDB-01 Primary Disconnect History")
yesterday_file = st.file_uploader("Upload the Excel file for 'Yesterday DCDB-01 Primary Disconnect History'", type=["xlsx", "xls"])
if yesterday_file:
    st.success("File uploaded successfully!")
    df_yesterday = pd.read_excel(yesterday_file)
    st.dataframe(df_yesterday)

# Step 2: Upload Total DCDB-01 Primary Disconnect History Till Date
st.subheader("2. Total DCDB-01 Primary Disconnect History Till Date")
total_history_file = st.file_uploader("Upload the Excel file for 'Total DCDB-01 Primary Disconnect History Till Date'", type=["xlsx", "xls"])
if total_history_file:
    st.success("File uploaded successfully!")
    df_total_history = pd.read_excel(total_history_file)
    st.dataframe(df_total_history)

# Step 3: Upload RMS Site List
st.subheader("3. RMS Site List")
rms_site_file = st.file_uploader("Upload the Excel file for 'RMS Site List'", type=["xlsx", "xls"])
if rms_site_file:
    st.success("File uploaded successfully!")
    df_rms_site = pd.read_excel(rms_site_file)
    st.dataframe(df_rms_site)

# Step 4: Upload Grid Data
st.subheader("4. Grid Data")
grid_data_file = st.file_uploader("Upload the Excel file for 'Grid Data'", type=["xlsx", "xls"])
if grid_data_file:
    st.success("File uploaded successfully!")
    df_grid_data = pd.read_excel(grid_data_file)
    st.dataframe(df_grid_data)

# Final Message
if yesterday_file and total_history_file and rms_site_file and grid_data_file:
    st.success("All files have been uploaded successfully!")
