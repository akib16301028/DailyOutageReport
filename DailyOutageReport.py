import os
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

# Path to the MTA Site List in the deployed directory (using __file__ to get the current script's directory)
MTA_SITE_LIST_PATH = os.path.join(os.path.dirname(__file__), "MTA_Site_List.xlsx")

# Function to load MTA Site List from the local repository
def load_mta_site_list():
    if os.path.exists(MTA_SITE_LIST_PATH):
        return pd.read_excel(MTA_SITE_LIST_PATH, skiprows=2)
    else:
        st.error("MTA Site List file is missing in the deployment folder.")
        return pd.DataFrame()

# Step 1: Upload RMS Site List
rms_site_file = st.sidebar.file_uploader("1. RMS Site List", type=["xlsx", "xls"])
if rms_site_file:
    st.success("RMS Site List uploaded successfully!")

    try:
        # Read RMS Site List starting from row 3
        df_rms_site = pd.read_excel(rms_site_file, skiprows=2)

        # Filter out sites starting with 'L'
        df_rms_filtered = df_rms_site[~df_rms_site["Site"].str.startswith("L", na=False)]

        # Add Tenant column
        df_rms_filtered["Tenant"] = df_rms_filtered["Site Alias"].apply(extract_tenant)

        # Standardize tenant names
        df_rms_filtered["Tenant"] = df_rms_filtered["Tenant"].apply(standardize_tenant)

        # Group tenant data by Cluster and Zone
        tenant_zone_rms = {}
        for tenant in df_rms_filtered["Tenant"].unique():
            tenant_df = df_rms_filtered[df_rms_filtered["Tenant"] == tenant]
            grouped_df = tenant_df.groupby(["Cluster", "Zone"]).size().reset_index(name="Total Site Count")
            grouped_df = grouped_df.sort_values(by=["Cluster", "Zone"])
            tenant_zone_rms[tenant] = grouped_df

    except Exception as e:
        st.error(f"Error processing RMS Site List: {e}")

# Step 2: Upload Yesterday Alarm History
alarm_history_file = st.sidebar.file_uploader("2. Yesterday Alarm History", type=["xlsx", "xls"])
if alarm_history_file:
    st.success("Yesterday Alarm History uploaded successfully!")

    try:
        df_alarm_history = pd.read_excel(alarm_history_file, skiprows=2)
        df_alarm_history = df_alarm_history[~df_alarm_history["Site"].str.startswith("L", na=False)]
        df_alarm_history["Tenant"] = df_alarm_history["Tenant"].apply(standardize_tenant)

        tenant_merged_data = {}
        merged_all_tenants = pd.DataFrame()

        for tenant in df_alarm_history["Tenant"].unique():
            rms_data = tenant_zone_rms.get(tenant, pd.DataFrame())
            alarm_data = df_alarm_history[df_alarm_history["Tenant"] == tenant]

            grouped_alarm_data = alarm_data.groupby(["Cluster", "Zone"]).size().reset_index(name="Total Affected Site")
            alarm_data["Elapsed Time"] = pd.to_timedelta(alarm_data["Elapsed Time"], errors="coerce")
            elapsed_time_sum = alarm_data.groupby(["Cluster", "Zone"])["Elapsed Time"].sum().reset_index()
            elapsed_time_sum["Elapsed Time (Decimal)"] = elapsed_time_sum["Elapsed Time"].apply(convert_to_decimal_hours)

            merged_data = pd.merge(rms_data, grouped_alarm_data, on=["Cluster", "Zone"], how="left")
            merged_data = pd.merge(merged_data, elapsed_time_sum[["Cluster", "Zone", "Elapsed Time (Decimal)"]], on=["Cluster", "Zone"], how="left")

            merged_data["Total Affected Site"] = merged_data["Total Affected Site"].fillna(0)
            merged_data["Elapsed Time (Decimal)"] = merged_data["Elapsed Time (Decimal)"].fillna(Decimal(0.0))

            tenant_merged_data[tenant] = merged_data
            merged_all_tenants = pd.concat([merged_all_tenants, merged_data])

    except Exception as e:
        st.error(f"Error processing Yesterday Alarm History: {e}")

# Step 3: Upload Grid Data
grid_data_file = st.sidebar.file_uploader("3. Grid Data", type=["xlsx", "xls"])
if grid_data_file:
    st.success("Grid Data uploaded successfully!")

    try:
        df_grid_data = pd.read_excel(grid_data_file, sheet_name="Site Wise Summary", skiprows=2)
        df_grid_data = df_grid_data[~df_grid_data["Site"].str.startswith("L", na=False)]

        df_grid_data = df_grid_data[["Cluster", "Zone", "Tenant Name", "AC Availability (%)"]]
        df_grid_data["Tenant Name"] = df_grid_data["Tenant Name"].apply(standardize_tenant)

        tenant_zone_grid = {}
        for tenant in df_grid_data["Tenant Name"].unique():
            tenant_df = df_grid_data[df_grid_data["Tenant Name"] == tenant]
            grouped_grid = tenant_df.groupby(["Cluster", "Zone"])["AC Availability (%)"].mean().reset_index()
            tenant_zone_grid[tenant] = grouped_grid

    except Exception as e:
        st.error(f"Error processing Grid Data: {e}")

# Step 4: Upload Total Elapse Till Date
total_elapse_file = st.sidebar.file_uploader("4. Total Elapse Till Date", type=["xlsx", "xls", "csv"])
if total_elapse_file:
    st.success("Total Elapse Till Date uploaded successfully!")

    try:
        if total_elapse_file.name.endswith(".csv"):
            df_total_elapse = pd.read_csv(total_elapse_file)
        else:
            df_total_elapse = pd.read_excel(total_elapse_file, skiprows=0)

        df_total_elapse = df_total_elapse[~df_total_elapse["Site"].str.startswith("L", na=False)]
        df_total_elapse["Tenant"] = df_total_elapse["Tenant"].apply(standardize_tenant)
        df_total_elapse["Elapsed Time"] = pd.to_timedelta(df_total_elapse["Elapsed Time"], errors="coerce")

        tenant_total_elapsed = {}
        for tenant in df_total_elapse["Tenant"].unique():
            tenant_df = df_total_elapse[df_total_elapse["Tenant"] == tenant]
            grouped_elapsed = tenant_df.groupby(["Cluster", "Zone"])["Elapsed Time"].sum().reset_index()
            grouped_elapsed["Total Reedemed Hour"] = grouped_elapsed["Elapsed Time"].apply(convert_to_decimal_hours)

            tenant_total_elapsed[tenant] = grouped_elapsed

    except Exception as e:
        st.error(f"Error processing Total Elapse Till Date: {e}")

# Load MTA Site List
df_mta_site_list = load_mta_site_list()

if not df_mta_site_list.empty:
    try:
        # Group MTA Site List by Cluster and Zone
        mta_zone_data = df_mta_site_list.groupby(["Cluster", "Zone"]).size().reset_index(name="Total Site Count")

        # Merging with Yesterday Alarm History (matching Site Alias)
        mta_alarm_data = df_alarm_history[df_alarm_history["Site Alias"].isin(df_mta_site_list["Site Alias"])]
        mta_alarm_data_grouped = mta_alarm_data.groupby(["Cluster", "Zone"]).size().reset_index(name="Total Affected Site")
        mta_alarm_data["Elapsed Time"] = pd.to_timedelta(mta_alarm_data["Elapsed Time"], errors="coerce")
        mta_elapsed_time_sum = mta_alarm_data.groupby(["Cluster", "Zone"])["Elapsed Time"].sum().reset_index()
        mta_elapsed_time_sum["Elapsed Time (Decimal)"] = mta_elapsed_time_sum["Elapsed Time"].apply(convert_to_decimal_hours)

        # Merging with Grid Data (matching Site Alias)
        mta_grid_data = df_grid_data[df_grid_data["Site Alias"].isin(df_mta_site_list["Site Alias"])]
        mta_grid_data_grouped = mta_grid_data.groupby(["Cluster", "Zone"])["AC Availability (%)"].mean().reset_index()

        # Merging with Total Elapse Till Date (matching Site Alias)
        mta_total_elapse_data = df_total_elapse[df_total_elapse["Site Alias"].isin(df_mta_site_list["Site Alias"])]
        mta_total_elapsed_grouped = mta_total_elapse_data.groupby(["Cluster", "Zone"])["Elapsed Time"].sum().reset_index()
        mta_total_elapsed_grouped["Total Reedemed Hour"] = mta_total_elapsed_grouped["Elapsed Time"].apply(convert_to_decimal_hours)

        # Final MTA Data merge
        mta_final_merged = pd.merge(
            mta_zone_data,
            mta_alarm_data_grouped[["Cluster", "Zone", "Total Affected Site"]],
            on=["Cluster", "Zone"],
            how="left"
        )
        mta_final_merged = pd.merge(
            mta_final_merged,
            mta_elapsed_time_sum[["Cluster", "Zone", "Elapsed Time (Decimal)"]],
            on=["Cluster", "Zone"],
            how="left"
        )
        mta_final_merged = pd.merge(
            mta_final_merged,
            mta_grid_data_grouped[["Cluster", "Zone", "AC Availability (%)"]],
            on=["Cluster", "Zone"],
            how="left"
        )
        mta_final_merged = pd.merge(
            mta_final_merged,
            mta_total_elapsed_grouped[["Cluster", "Zone", "Total Reedemed Hour"]],
            on=["Cluster", "Zone"],
            how="left"
        )

        mta_final_merged["Grid Availability"] = mta_final_merged["AC Availability (%)"]
        mta_final_merged["Total Allowable Limit (Hr)"] = mta_final_merged["Total Site Count"] * 24 * 30 * (1 - 0.9985)
        mta_final_merged["Remaining Hour"] = mta_final_merged["Total Allowable Limit (Hr)"] - mta_final_merged["Total Reedemed Hour"]

        st.subheader("MTA Sites Final Merged Table")
        st.dataframe(
            mta_final_merged[
                [
                    "Cluster",
                    "Zone",
                    "Total Site Count",
                    "Total Affected Site",
                    "Elapsed Time (Decimal)",
                    "Grid Availability",
                    "Total Reedemed Hour",
                    "Total Allowable Limit (Hr)",
                    "Remaining Hour"
                ]
            ]
        )

    except Exception as e:
        st.error(f"Error processing MTA Sites: {e}")
