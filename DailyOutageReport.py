import streamlit as st
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP
import os  # For file path operations

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

# Function to trim spaces at the end of column header names
def trim_column_names(df):
    """
    Trims trailing spaces from column header names in a DataFrame.
    Example: "Site Alias " -> "Site Alias"
    """
    df.columns = df.columns.str.rstrip()  # Remove trailing spaces
    return df

# Step 1: Upload RMS Site List
rms_site_file = st.sidebar.file_uploader("1. RMS Site List", type=["xlsx", "xls"])
if rms_site_file:
    st.success("RMS Site List uploaded successfully!")

    try:
        # Read RMS Site List starting from row 3
        df_rms_site = pd.read_excel(rms_site_file, skiprows=2)

        # Trim column names
        df_rms_site = trim_column_names(df_rms_site)

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

        # Trim column names
        df_alarm_history = trim_column_names(df_alarm_history)

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

        # Trim column names
        df_grid_data = trim_column_names(df_grid_data)

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

        # Trim column names
        df_total_elapse = trim_column_names(df_total_elapse)

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

# Step 5: Read MTA Site List from the repository
mta_site_list_path = os.path.join(os.path.dirname(__file__), "MTA Site List.xlsx")
if os.path.exists(mta_site_list_path):
    st.success("MTA Site List loaded successfully!")

    try:
        # Read MTA Site List
        df_mta_site_list = pd.read_excel(mta_site_list_path)

        # Debug: Print column names
        st.write("Columns in MTA Site List:", df_mta_site_list.columns.tolist())

        # Trim column names to remove trailing spaces
        df_mta_site_list = trim_column_names(df_mta_site_list)

        # Debug: Print column names after trimming
        st.write("Columns after trimming:", df_mta_site_list.columns.tolist())

        # Check if 'Site' column exists
        if "Site" not in df_mta_site_list.columns:
            st.error("Column 'Site' not found in MTA Site List.")
        else:
            # Debug: Print unique values in 'Site' column
            st.write("Unique values in 'Site':", df_mta_site_list["Site"].unique())

            # Convert 'Site' column to string (if not already)
            df_mta_site_list["Site"] = df_mta_site_list["Site"].astype(str)

            # Debug: Check for missing values in 'Site' column
            st.write("Missing values in 'Site':", df_mta_site_list["Site"].isna().sum())

            # Filter out sites starting with 'L'
            df_mta_site_list = df_mta_site_list[~df_mta_site_list["Site"].str.startswith("L", na=False)]

            # Debug: Print filtered data
            st.write("Filtered MTA Site List (sites starting with 'L' removed):")
            st.write(df_mta_site_list.head())

            # Group by Cluster and Zone
            mta_grouped = df_mta_site_list.groupby(["Cluster", "Zone"]).size().reset_index(name="Total Site Count")

            # Debug: Print grouped data
            st.write("Grouped MTA Site List by Cluster and Zone:")
            st.write(mta_grouped.head())

            # Merge with Yesterday Alarm History
            if alarm_history_file:
                df_alarm_history = pd.read_excel(alarm_history_file, skiprows=2)
                df_alarm_history = trim_column_names(df_alarm_history)

                # Filter out sites starting with 'L'
                df_alarm_history = df_alarm_history[~df_alarm_history["Site"].str.startswith("L", na=False)]

                # Standardize tenant names
                df_alarm_history["Tenant"] = df_alarm_history["Tenant"].apply(standardize_tenant)

                # Filter alarm history for sites present in MTA Site List
                df_alarm_history_mta = df_alarm_history[df_alarm_history["Site"].isin(df_mta_site_list["Site"])]

                # Group alarm data by Cluster and Zone
                grouped_alarm_data_mta = df_alarm_history_mta.groupby(["Cluster", "Zone"]).size().reset_index(name="Total Affected Site")

                # Convert Elapsed Time to decimal hours
                df_alarm_history_mta["Elapsed Time"] = pd.to_timedelta(df_alarm_history_mta["Elapsed Time"], errors="coerce")
                elapsed_time_sum_mta = df_alarm_history_mta.groupby(["Cluster", "Zone"])["Elapsed Time"].sum().reset_index()
                elapsed_time_sum_mta["Elapsed Time (Decimal)"] = elapsed_time_sum_mta["Elapsed Time"].apply(convert_to_decimal_hours)

                # Merge MTA grouped data with alarm data
                merged_data_mta = pd.merge(mta_grouped, grouped_alarm_data_mta, on=["Cluster", "Zone"], how="left")
                merged_data_mta = pd.merge(merged_data_mta, elapsed_time_sum_mta[["Cluster", "Zone", "Elapsed Time (Decimal)"]], on=["Cluster", "Zone"], how="left")

                # Fill NaN values
                merged_data_mta["Total Affected Site"] = merged_data_mta["Total Affected Site"].fillna(0)
                merged_data_mta["Elapsed Time (Decimal)"] = merged_data_mta["Elapsed Time (Decimal)"].fillna(Decimal(0.0))

                # Merge with Grid Data
                if grid_data_file:
                    df_grid_data = pd.read_excel(grid_data_file, sheet_name="Site Wise Summary", skiprows=2)
                    df_grid_data = trim_column_names(df_grid_data)

                    # Filter out sites starting with 'L'
                    df_grid_data = df_grid_data[~df_grid_data["Site"].str.startswith("L", na=False)]

                    # Select relevant columns
                    df_grid_data = df_grid_data[["Cluster", "Zone", "Tenant Name", "AC Availability (%)"]]
                    df_grid_data["Tenant Name"] = df_grid_data["Tenant Name"].apply(standardize_tenant)

                    # Filter grid data for sites present in MTA Site List
                    df_grid_data_mta = df_grid_data[df_grid_data["Site"].isin(df_mta_site_list["Site"])]

                    # Group grid data by Cluster and Zone
                    grouped_grid_mta = df_grid_data_mta.groupby(["Cluster", "Zone"])["AC Availability (%)"].mean().reset_index()

                    # Merge with existing data
                    merged_data_mta = pd.merge(merged_data_mta, grouped_grid_mta, on=["Cluster", "Zone"], how="left")
                    merged_data_mta["Grid Availability"] = merged_data_mta["AC Availability (%)"]

                # Merge with Total Elapse Till Date
                if total_elapse_file:
                    if total_elapse_file.name.endswith(".csv"):
                        df_total_elapse = pd.read_csv(total_elapse_file)
                    else:
                        df_total_elapse = pd.read_excel(total_elapse_file, skiprows=0)

                    df_total_elapse = trim_column_names(df_total_elapse)

                    # Filter out sites starting with 'L'
                    df_total_elapse = df_total_elapse[~df_total_elapse["Site"].str.startswith("L", na=False)]

                    # Standardize tenant names
                    df_total_elapse["Tenant"] = df_total_elapse["Tenant"].apply(standardize_tenant)

                    # Convert Elapsed Time to timedelta
                    df_total_elapse["Elapsed Time"] = pd.to_timedelta(df_total_elapse["Elapsed Time"], errors="coerce")

                    # Filter total elapse for sites present in MTA Site List
                    df_total_elapse_mta = df_total_elapse[df_total_elapse["Site"].isin(df_mta_site_list["Site"])]

                    # Group total elapse by Cluster and Zone
                    grouped_elapsed_mta = df_total_elapse_mta.groupby(["Cluster", "Zone"])["Elapsed Time"].sum().reset_index()
                    grouped_elapsed_mta["Total Reedemed Hour"] = grouped_elapsed_mta["Elapsed Time"].apply(convert_to_decimal_hours)

                    # Merge with existing data
                    merged_data_mta = pd.merge(merged_data_mta, grouped_elapsed_mta[["Cluster", "Zone", "Total Reedemed Hour"]], on=["Cluster", "Zone"], how="left")

                # Calculate Total Allowable Limit (Hr) and Remaining Hour
                merged_data_mta["Total Allowable Limit (Hr)"] = merged_data_mta["Total Site Count"] * 24 * 30 * (1 - 0.9985)
                merged_data_mta["Remaining Hour"] = merged_data_mta["Total Allowable Limit (Hr)"] - merged_data_mta["Total Reedemed Hour"].astype(float)

                # Display Final Merged Table
                st.subheader("MTA Sites - Final Merged Table")
                st.dataframe(
                    merged_data_mta[
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
        st.error(f"Error processing MTA Site List: {e}")
else:
    st.error("MTA Site List file not found in the repository.")
