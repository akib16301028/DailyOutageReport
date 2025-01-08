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
    try:
        st.success("Yesterday's disconnect history uploaded successfully!")
        # Read the Excel file starting from row 3
        df_yesterday = pd.read_excel(yesterday_file, skiprows=2)
        
        st.subheader("Yesterday DCDB-01 Primary Disconnect History (Raw Data)")
        st.dataframe(df_yesterday)

        # Extract tenant names dynamically
        tenant_column = "Tenant"  # Replace with actual column name
        cluster_column = "Cluster"  # Replace with actual column name
        zone_column = "Zone"  # Replace with actual column name

        # Check required columns
        required_columns = [tenant_column, cluster_column, zone_column]
        if all(col in df_yesterday.columns for col in required_columns):
            tenants = df_yesterday[tenant_column].unique()
            st.sidebar.subheader("Tenant-Wise Tables")

            for tenant in tenants:
                # Filter data for each tenant
                tenant_data = df_yesterday[df_yesterday[tenant_column] == tenant]
                
                # Group by Cluster (RIO) and Zone
                grouped_data = (
                    tenant_data.groupby([cluster_column, zone_column])
                    .size()
                    .reset_index(name="Count")
                )
                
                # Rename columns for clarity
                grouped_data.rename(columns={cluster_column: "RIO", zone_column: "Zone"}, inplace=True)
                
                # Display tenant-specific table
                st.subheader(f"Tenant: {tenant}")
                st.dataframe(grouped_data)

        else:
            missing_cols = [col for col in required_columns if col not in df_yesterday.columns]
            st.error(f"Missing columns in the uploaded file: {', '.join(missing_cols)}")

    except Exception as e:
        st.error(f"An error occurred while processing the file: {e}")

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
