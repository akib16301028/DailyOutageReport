import streamlit as st
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP
import os

# Set the title of the application
st.title("MTA Site List Processing")

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

# Function to trim spaces at the end of column header names
def trim_column_names(df):
    df.columns = df.columns.str.rstrip()  # Remove trailing spaces
    return df

# Step 1: Load MTA Site List from the repository
mta_site_list_path = os.path.join(os.path.dirname(__file__), "MTA Site List.xlsx")
if os.path.exists(mta_site_list_path):
    st.success("MTA Site List loaded successfully!")

    try:
        # Read MTA Site List
        df_mta_site_list = pd.read_excel(mta_site_list_path)
        df_mta_site_list = trim_column_names(df_mta_site_list)

        # Filter out sites starting with 'L'
        df_mta_site_list = df_mta_site_list[~df_mta_site_list["Site"].str.startswith("L", na=False)].copy()

        # Group by Cluster and Zone
        mta_grouped = df_mta_site_list.groupby(["Cluster", "Zone"]).size().reset_index(name="Total Site Count")

        # Step 2: Load Yesterday Alarm History
        alarm_history_path = os.path.join(os.path.dirname(__file__), "Yesterday Alarm History.xlsx")
        if os.path.exists(alarm_history_path):
            df_alarm_history = pd.read_excel(alarm_history_path, skiprows=2)
            df_alarm_history = trim_column_names(df_alarm_history)

            # Filter out sites starting with 'L'
            df_alarm_history = df_alarm_history[~df_alarm_history["Site"].str.startswith("L", na=False)].copy()

            # Standardize tenant names
            df_alarm_history.loc[:, "Tenant"] = df_alarm_history["Tenant"].apply(standardize_tenant)

            # Filter alarm history for sites present in MTA Site List
            df_alarm_history_mta = df_alarm_history[df_alarm_history["Site"].isin(df_mta_site_list["Site"])].copy()

            # Group alarm data by Cluster and Zone
            grouped_alarm_data_mta = df_alarm_history_mta.groupby(["Cluster", "Zone"]).size().reset_index(name="Total Affected Site")

            # Convert Elapsed Time to decimal hours
            df_alarm_history_mta.loc[:, "Elapsed Time"] = pd.to_timedelta(df_alarm_history_mta["Elapsed Time"], errors="coerce")
            elapsed_time_sum_mta = df_alarm_history_mta.groupby(["Cluster", "Zone"])["Elapsed Time"].sum().reset_index()
            elapsed_time_sum_mta.loc[:, "Elapsed Time (Decimal)"] = elapsed_time_sum_mta["Elapsed Time"].apply(convert_to_decimal_hours)

            # Merge MTA grouped data with alarm data
            merged_data_mta = pd.merge(mta_grouped, grouped_alarm_data_mta, on=["Cluster", "Zone"], how="left")
            merged_data_mta = pd.merge(merged_data_mta, elapsed_time_sum_mta[["Cluster", "Zone", "Elapsed Time (Decimal)"]], on=["Cluster", "Zone"], how="left")

            # Fill NaN values
            merged_data_mta.loc[:, "Total Affected Site"] = merged_data_mta["Total Affected Site"].fillna(0)
            merged_data_mta.loc[:, "Elapsed Time (Decimal)"] = merged_data_mta["Elapsed Time (Decimal)"].fillna(Decimal(0.0))

        # Step 3: Load Grid Data
        grid_data_path = os.path.join(os.path.dirname(__file__), "Grid Data.xlsx")
        if os.path.exists(grid_data_path):
            df_grid_data = pd.read_excel(grid_data_path, sheet_name="Site Wise Summary", skiprows=2)
            df_grid_data = trim_column_names(df_grid_data)

            # Filter out sites starting with 'L'
            df_grid_data = df_grid_data[~df_grid_data["Site"].str.startswith("L", na=False)].copy()

            # Select relevant columns
            df_grid_data = df_grid_data[["Cluster", "Zone", "Tenant Name", "AC Availability (%)"]]
            df_grid_data.loc[:, "Tenant Name"] = df_grid_data["Tenant Name"].apply(standardize_tenant)

            # Filter grid data for sites present in MTA Site List
            df_grid_data_mta = df_grid_data[df_grid_data["Site"].isin(df_mta_site_list["Site"])].copy()

            # Group grid data by Cluster and Zone
            grouped_grid_mta = df_grid_data_mta.groupby(["Cluster", "Zone"])["AC Availability (%)"].mean().reset_index()

            # Merge with existing data
            merged_data_mta = pd.merge(merged_data_mta, grouped_grid_mta, on=["Cluster", "Zone"], how="left")
            merged_data_mta.loc[:, "Grid Availability"] = merged_data_mta["AC Availability (%)"]

        # Step 4: Load Total Elapse Till Date
        total_elapse_path = os.path.join(os.path.dirname(__file__), "Total Elapse Till Date.xlsx")
        if os.path.exists(total_elapse_path):
            df_total_elapse = pd.read_excel(total_elapse_path, skiprows=0)
            df_total_elapse = trim_column_names(df_total_elapse)

            # Filter out sites starting with 'L'
            df_total_elapse = df_total_elapse[~df_total_elapse["Site"].str.startswith("L", na=False)].copy()

            # Standardize tenant names
            df_total_elapse.loc[:, "Tenant"] = df_total_elapse["Tenant"].apply(standardize_tenant)

            # Convert Elapsed Time to timedelta
            df_total_elapse.loc[:, "Elapsed Time"] = pd.to_timedelta(df_total_elapse["Elapsed Time"], errors="coerce")

            # Filter total elapse for sites present in MTA Site List
            df_total_elapse_mta = df_total_elapse[df_total_elapse["Site"].isin(df_mta_site_list["Site"])].copy()

            # Group total elapse by Cluster and Zone
            grouped_elapsed_mta = df_total_elapse_mta.groupby(["Cluster", "Zone"])["Elapsed Time"].sum().reset_index()
            grouped_elapsed_mta.loc[:, "Total Reedemed Hour"] = grouped_elapsed_mta["Elapsed Time"].apply(convert_to_decimal_hours)

            # Merge with existing data
            merged_data_mta = pd.merge(merged_data_mta, grouped_elapsed_mta[["Cluster", "Zone", "Total Reedemed Hour"]], on=["Cluster", "Zone"], how="left")

            # Calculate Total Allowable Limit (Hr) and Remaining Hour
            merged_data_mta.loc[:, "Total Allowable Limit (Hr)"] = merged_data_mta["Total Site Count"] * 24 * 30 * (1 - 0.9985)
            merged_data_mta.loc[:, "Remaining Hour"] = merged_data_mta["Total Allowable Limit (Hr)"] - merged_data_mta["Total Reedemed Hour"].astype(float)

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
