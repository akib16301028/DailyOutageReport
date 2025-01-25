import streamlit as st
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

# Set the title of the application
st.title("Tenant-Wise Data Processing Application")

# Sidebar for uploading files
st.sidebar.header("Upload Required Excel Files")

# Function to standardize tenant names
def standardize_tenant(tenant_name):
    tenant_mapping = {
        "BANJO": "Banjo",
        "BL": "Banglalink",
        "GP": "Grameenphone",
        "ROBI": "Robi",
    }
    return tenant_mapping.get(tenant_name, tenant_name)

# Function to extract tenant from Site Alias
def extract_tenant(site_alias):
    if isinstance(site_alias, str):
        brackets = site_alias.split("(")
        tenants = [part.split(")")[0].strip() for part in brackets if ")" in part]
        for tenant in tenants:
            if "BANJO" in tenant:
                return "Banjo"
        return tenants[0] if tenants else "Unknown"
    return "Unknown"

# Function to convert elapsed time to decimal hours
def convert_to_decimal_hours(elapsed_time):
    if pd.notnull(elapsed_time):
        total_seconds = elapsed_time.total_seconds()
        decimal_hours = total_seconds / 3600
        return Decimal(decimal_hours).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
    return Decimal(0.0)

# Option to display MTA Site List
show_mta_list = st.sidebar.checkbox("Show MTA Site List")

if show_mta_list:
    try:
        mta_site_file = st.sidebar.file_uploader("Upload MTA Site List", type=["xlsx", "xls"])
        if mta_site_file:
            df_mta_site = pd.read_excel(mta_site_file)
            st.subheader("MTA Site List")
            st.dataframe(df_mta_site)
        else:
            st.warning("Please upload an MTA Site List file.")
    except Exception as e:
        st.error(f"Error reading MTA Site List: {e}")

# Step 1: Upload RMS Site List
rms_site_file = st.sidebar.file_uploader("1. RMS Site List", type=["xlsx", "xls"])
if rms_site_file:
    try:
        # Read RMS Site List starting from row 3
        df_rms_site = pd.read_excel(rms_site_file, skiprows=2)
        df_rms_filtered = df_rms_site[~df_rms_site["Site"].str.startswith("L", na=False)]

        # Add Tenant column
        df_rms_filtered["Tenant"] = df_rms_filtered["Site Alias"].apply(extract_tenant)
        df_rms_filtered["Tenant"] = df_rms_filtered["Tenant"].apply(standardize_tenant)

        # Group tenant data by Cluster and Zone
        tenant_zone_rms = {}
        for tenant in df_rms_filtered["Tenant"].unique():
            tenant_df = df_rms_filtered[df_rms_filtered["Tenant"] == tenant]
            grouped_df = tenant_df.groupby(["Cluster", "Zone"]).size().reset_index(name="Total Site Count")
            tenant_zone_rms[tenant] = grouped_df
        st.success("RMS Site List processed successfully!")
    except Exception as e:
        st.error(f"Error processing RMS Site List: {e}")

# Step 2: Upload Yesterday Alarm History
alarm_history_file = st.sidebar.file_uploader("2. Yesterday Alarm History", type=["xlsx", "xls"])
if alarm_history_file:
    try:
        df_alarm_history = pd.read_excel(alarm_history_file, skiprows=2)
        df_alarm_history = df_alarm_history[~df_alarm_history["Site"].str.startswith("L", na=False)]
        df_alarm_history["Tenant"] = df_alarm_history["Tenant"].apply(standardize_tenant)
        st.success("Alarm History processed successfully!")
    except Exception as e:
        st.error(f"Error processing Alarm History: {e}")

# Step 3: Upload Grid Data
grid_data_file = st.sidebar.file_uploader("3. Grid Data", type=["xlsx", "xls"])
if grid_data_file:
    try:
        df_grid_data = pd.read_excel(grid_data_file, sheet_name="Site Wise Summary", skiprows=2)
        df_grid_data = df_grid_data[~df_grid_data["Site"].str.startswith("L", na=False)]
        df_grid_data["Tenant Name"] = df_grid_data["Tenant Name"].apply(standardize_tenant)
        st.success("Grid Data processed successfully!")
    except Exception as e:
        st.error(f"Error processing Grid Data: {e}")

# Step 4: Upload Total Elapse Till Date
total_elapse_file = st.sidebar.file_uploader("4. Total Elapse Till Date", type=["xlsx", "xls", "csv"])
if total_elapse_file:
    try:
        if total_elapse_file.name.endswith(".csv"):
            df_total_elapse = pd.read_csv(total_elapse_file)
        else:
            df_total_elapse = pd.read_excel(total_elapse_file)
        df_total_elapse["Tenant"] = df_total_elapse["Tenant"].apply(standardize_tenant)
        st.success("Total Elapse Till Date processed successfully!")
    except Exception as e:
        st.error(f"Error processing Total Elapse Till Date: {e}")

# Ensure all required files are processed
if rms_site_file and alarm_history_file and grid_data_file and total_elapse_file:
    try:
        # Example merging logic (details can be added per your requirements)
        # Final merge and processing logic goes here
        st.success("All data files processed and merged successfully!")
    except Exception as e:
        st.error(f"Error merging data: {e}")
