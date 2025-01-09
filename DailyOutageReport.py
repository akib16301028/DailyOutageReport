import streamlit as st
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

# Set the title of the application
st.title("Tenant-Wise Data Processing Application")

# Sidebar for uploading files
st.sidebar.header("Upload Required Excel Files")

# Function to safely read Excel files
def safe_read_excel(file, skiprows=0, sheet_name=0):
    try:
        return pd.read_excel(file, skiprows=skiprows, sheet_name=sheet_name)
    except Exception as e:
        st.error(f"Error reading Excel file: {e}")
        return pd.DataFrame()

# Function to standardize tenant names
def standardize_tenant(tenant_name):
    tenant_mapping = {
        "BANJO": "Banjo",
        "BL": "Banglalink",
        "GP": "Grameenphone",
        "ROBI": "Robi",
    }
    return tenant_mapping.get(tenant_name, tenant_name)

# Function to convert elapsed time to decimal hours
def convert_to_decimal_hours(elapsed_time):
    if pd.notnull(elapsed_time):
        total_seconds = elapsed_time.total_seconds()
        decimal_hours = total_seconds / 3600
        return Decimal(decimal_hours).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
    return Decimal(0.0)

# Step 1: Upload RMS Site List
rms_site_file = st.sidebar.file_uploader("1. RMS Site List", type=["xlsx", "xls"])
if rms_site_file:
    st.success("RMS Site List uploaded successfully!")
    df_rms_site = safe_read_excel(rms_site_file, skiprows=2)

    if not df_rms_site.empty:
        # Filter out sites starting with 'L'
        df_rms_filtered = df_rms_site[~df_rms_site["Site"].str.startswith("L", na=False)]

        # Extract and standardize tenant names
        def extract_tenant(site_alias):
            if isinstance(site_alias, str):
                tenants = [part.split(")")[0].strip() for part in site_alias.split("(") if ")" in part]
                return tenants[0] if tenants else "Unknown"
            return "Unknown"

        df_rms_filtered["Tenant"] = df_rms_filtered["Site Alias"].apply(extract_tenant)
        df_rms_filtered["Tenant"] = df_rms_filtered["Tenant"].apply(standardize_tenant)

        # Group data by Cluster and Zone for tenants
        tenant_zone_rms = {}
        for tenant, tenant_df in df_rms_filtered.groupby("Tenant"):
            grouped_df = tenant_df.groupby(["Cluster", "Zone"]).size().reset_index(name="Total Site Count")
            tenant_zone_rms[tenant] = grouped_df

# Step 2: Upload Yesterday Alarm History File
alarm_history_file = st.sidebar.file_uploader("2. Yesterday Alarm History", type=["xlsx", "xls"])
if alarm_history_file:
    st.success("Yesterday Alarm History uploaded successfully!")
    df_alarm_history = safe_read_excel(alarm_history_file, skiprows=2)

    if not df_alarm_history.empty:
        df_alarm_history = df_alarm_history[~df_alarm_history["Site"].str.startswith("L", na=False)]
        df_alarm_history["Tenant"] = df_alarm_history["Tenant"].apply(standardize_tenant)

        merged_all_tenants = pd.DataFrame()
        for tenant, alarm_df in df_alarm_history.groupby("Tenant"):
            rms_data = tenant_zone_rms.get(tenant, pd.DataFrame())
            grouped_alarm_data = alarm_df.groupby(["Cluster", "Zone"]).size().reset_index(name="Total Affected Site")

            alarm_df["Elapsed Time"] = pd.to_timedelta(alarm_df["Elapsed Time"], errors="coerce")
            elapsed_time_sum = alarm_df.groupby(["Cluster", "Zone"])["Elapsed Time"].sum().reset_index()
            elapsed_time_sum["Elapsed Time (Decimal)"] = elapsed_time_sum["Elapsed Time"].apply(convert_to_decimal_hours)

            merged_data = pd.merge(rms_data, grouped_alarm_data, on=["Cluster", "Zone"], how="left")
            merged_data = pd.merge(merged_data, elapsed_time_sum[["Cluster", "Zone", "Elapsed Time (Decimal)"]], on=["Cluster", "Zone"], how="left")
            merged_data.fillna({"Total Affected Site": 0, "Elapsed Time (Decimal)": Decimal(0.0)}, inplace=True)

            st.subheader(f"Tenant: {tenant} - Cluster and Zone Data")
            st.dataframe(merged_data)
            merged_all_tenants = pd.concat([merged_all_tenants, merged_data])

        overall_merged_data = merged_all_tenants.groupby(["Cluster", "Zone"]).agg({
            "Total Site Count": "sum",
            "Total Affected Site": "sum",
            "Elapsed Time (Decimal)": "sum",
        }).reset_index()

        st.subheader("Overall Cluster and Zone Data for All Tenants")
        st.dataframe(overall_merged_data)

# Step 3: Upload Grid Data File
grid_data_file = st.sidebar.file_uploader("3. Grid Data", type=["xlsx", "xls"])
if grid_data_file:
    st.success("Grid Data uploaded successfully!")
    df_grid = safe_read_excel(grid_data_file, skiprows=2, sheet_name="Site Wise Summary")

    if not df_grid.empty:
        df_grid = df_grid[~df_grid["Site"].str.startswith("L", na=False)]
        df_grid["Tenant Name"] = df_grid["Tenant Name"].apply(standardize_tenant)

        overall_grid_data = df_grid.groupby(["Cluster", "Zone"]).agg({
            "AC Availability (%)": "mean"
        }).reset_index()
        overall_grid_data.rename(columns={"AC Availability (%)": "Grid Availability"}, inplace=True)

        st.subheader("Overall Grid Availability by Cluster and Zone")
        st.dataframe(overall_grid_data)

# Merge all data
if rms_site_file and alarm_history_file and grid_data_file:
    try:
        overall_merged_with_grid = pd.merge(overall_merged_data, overall_grid_data, on=["Cluster", "Zone"], how="left")
        st.subheader("Final Merged Data")
        st.dataframe(overall_merged_with_grid)
    except Exception as e:
        st.error(f"Error merging final tables: {e}")
