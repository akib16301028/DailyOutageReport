import streamlit as st
import pandas as pd

# Set the title of the application
st.title("Data Upload Application")

# Sidebar for uploading files
st.sidebar.header("Upload Required Excel Files")

# Step 1: Upload Yesterday DCDB-01 Primary Disconnect History
yesterday_file = st.sidebar.file_uploader(
    "1. Yesterday DCDB-01 Primary Disconnect History", type=["xlsx", "xls"]
)
if yesterday_file:
    st.success("Yesterday's disconnect history uploaded successfully!")
    df_yesterday = pd.read_excel(yesterday_file)
    st.subheader("Yesterday DCDB-01 Primary Disconnect History")
    st.dataframe(df_yesterday)

# Step 2: Upload Total DCDB-01 Primary Disconnect History Till Date
total_history_file = st.sidebar.file_uploader(
    "2. Total DCDB-01 Primary Disconnect History Till Date", type=["xlsx", "xls"]
)
if total_history_file:
    st.success("Total disconnect history till date uploaded successfully!")
    df_total_history = pd.read_excel(total_history_file)
    st.subheader("Total DCDB-01 Primary Disconnect History Till Date")
    st.dataframe(df_total_history)

# Step 3: Upload RMS Site List
rms_site_file = st.sidebar.file_uploader(
    "3. RMS Site List", type=["xlsx", "xls"]
)
if rms_site_file:
    st.success("RMS site list uploaded successfully!")
    df_rms_site = pd.read_excel(rms_site_file)
    st.subheader("RMS Site List")
    st.dataframe(df_rms_site)

# Step 4: Upload Grid Data
grid_data_file = st.sidebar.file_uploader(
    "4. Grid Data", type=["xlsx", "xls"]
)
if grid_data_file:
    st.success("Grid data uploaded successfully!")
    df_grid_data = pd.read_excel(grid_data_file)
    st.subheader("Grid Data")
    st.dataframe(df_grid_data)

# Checkbox to view MTA Site List
show_mta_site_list = st.sidebar.checkbox("Show MTA Site List")

if show_mta_site_list:
    try:
        # Read the MTA Site List Excel file
        mta_file_path = "MTA Site List.xlsx"  # Ensure this file is in the same directory as the script
        df_mta = pd.read_excel(mta_file_path)
        # Select specific columns to display
        columns_to_show = [
            "Rms Station", "Site", "Site Alias", "Zone", "Cluster",
            "District", "Site Attributes", "Alarm Status", "Installation Date"
        ]
        df_filtered_mta = df_mta[columns_to_show]
        
        # Display the filtered MTA Site List
        st.subheader("MTA Site List")
        st.dataframe(df_filtered_mta)

    except Exception as e:
        st.error(f"Could not load MTA Site List. Error: {e}")

# Final Message
if yesterday_file and total_history_file and rms_site_file and grid_data_file:
    st.sidebar.success("All files have been uploaded successfully!")
