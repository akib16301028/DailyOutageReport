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

# Function to calculate Total Allowable Limit
def calculate_total_allowable_limit(total_site_count):
    return (total_site_count * 24 * 30) - ((total_site_count * 24 * 30) * 0.9985)

# Function to calculate Remaining Hour
def calculate_remaining_hour(total_allowable_limit, total_reedemed_hour):
    return total_allowable_limit - total_reedemed_hour

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

# Merge Overall and Tenant-Specific Data
if rms_site_file and alarm_history_file and grid_data_file:
    try:
        for tenant, tenant_merged in tenant_merged_data.items():
            grid_data = tenant_zone_grid.get(tenant, pd.DataFrame())
            
            merged_tenant_final = pd.merge(
                tenant_merged,
                grid_data[["Cluster", "Zone", "AC Availability (%)"]],
                on=["Cluster", "Zone"],
                how="left"
            )

            merged_tenant_final["Grid Availability"] = merged_tenant_final["AC Availability (%)"]
            
            # Calculate Total Allowable Limit and Remaining Hour
            merged_tenant_final["Total Allowable Limit (Hr)"] = merged_tenant_final["Total Site Count"].apply(calculate_total_allowable_limit)
            merged_tenant_final["Remaining Hour"] = merged_tenant_final.apply(
                lambda row: calculate_remaining_hour(row["Total Allowable Limit (Hr)"], row["Total Reedemed Hour"]), axis=1)

            st.subheader(f"Tenant: {tenant} - Final Merged Table")
            st.dataframe(merged_tenant_final[["Cluster", "Zone", "Total Site Count", "Total Affected Site", 
                                             "Elapsed Time (Decimal)", "Grid Availability", "Total Reedemed Hour", 
                                             "Total Allowable Limit (Hr)", "Remaining Hour"]])

        # Combine all tenants for the overall table
        combined_grid_data = df_grid_data.groupby(["Cluster", "Zone"]).agg({
            "AC Availability (%)": "mean",
        }).reset_index()

        overall_final_merged = pd.merge(
            merged_all_tenants.groupby(["Cluster", "Zone"]).sum().reset_index(),
            combined_grid_data,
            on=["Cluster", "Zone"],
            how="left"
        )

        overall_final_merged["Grid Availability"] = overall_final_merged["AC Availability (%)"]
        
        # Calculate Total Allowable Limit and Remaining Hour for overall
        overall_final_merged["Total Allowable Limit (Hr)"] = overall_final_merged["Total Site Count"].apply(calculate_total_allowable_limit)
        overall_final_merged["Remaining Hour"] = overall_final_merged.apply(
            lambda row: calculate_remaining_hour(row["Total Allowable Limit (Hr)"], row["Total Reedemed Hour"]), axis=1)

        st.subheader("Overall Merged Table")
        st.dataframe(overall_final_merged[["Cluster", "Zone", "Total Site Count", "Total Affected Site", 
                                          "Elapsed Time (Decimal)", "Grid Availability", "Total Reedemed Hour", 
                                          "Total Allowable Limit (Hr)", "Remaining Hour"]])

    except Exception as e:
        st.error(f"Error during merging: {e}")

# Final Message
if rms_site_file and alarm_history_file and grid_data_file:
    st.sidebar.success("All files processed and merged successfully!")
