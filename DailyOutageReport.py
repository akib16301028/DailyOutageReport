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
        # Detect file type and load accordingly
        if total_elapse_file.name.endswith(".csv"):
            df_total_elapse = pd.read_csv(total_elapse_file)
        else:
            df_total_elapse = pd.read_excel(total_elapse_file, skiprows=0)  # Header starts from row 1

        # Filter out rows where Site column starts with 'L'
        df_total_elapse = df_total_elapse[~df_total_elapse["Site"].str.startswith("L", na=False)]

        # Standardize tenant names
        df_total_elapse["Tenant"] = df_total_elapse["Tenant"].apply(standardize_tenant)

        # Convert Elapsed Time to timedelta for summation
        df_total_elapse["Elapsed Time"] = pd.to_timedelta(df_total_elapse["Elapsed Time"], errors="coerce")

        # Tenant-wise table grouped by Cluster and Zone with summed Elapsed Time
        tenant_total_elapsed = {}
        for tenant in df_total_elapse["Tenant"].unique():
            tenant_df = df_total_elapse[df_total_elapse["Tenant"] == tenant]
            grouped_elapsed = (
                tenant_df.groupby(["Cluster", "Zone"])["Elapsed Time"]
                .sum()
                .reset_index()
            )
            # Convert total elapsed time to decimal hours
            grouped_elapsed["Total Reedemed Hour"] = grouped_elapsed["Elapsed Time"].apply(convert_to_decimal_hours)

            tenant_total_elapsed[tenant] = grouped_elapsed

    except Exception as e:
        st.error(f"Error processing Total Elapse Till Date: {e}")

# Merge Overall and Tenant-Specific Data
if rms_site_file and alarm_history_file and grid_data_file and total_elapse_file:
    try:
        for tenant, tenant_merged in tenant_merged_data.items():
            grid_data = tenant_zone_grid.get(tenant, pd.DataFrame())
            
            # Merge tenant-specific data with Grid Data
            merged_tenant_final = pd.merge(
                tenant_merged,
                grid_data[["Cluster", "Zone", "AC Availability (%)"]],
                on=["Cluster", "Zone"],
                how="left"
            )

            merged_tenant_final["Grid Availability"] = merged_tenant_final["AC Availability (%)"]
            
            # Merge with Total Reedemed Hour for each tenant
            total_elapsed_data = tenant_total_elapsed.get(tenant, pd.DataFrame())
            merged_tenant_final = pd.merge(
                merged_tenant_final,
                total_elapsed_data[["Cluster", "Zone", "Total Reedemed Hour"]],
                on=["Cluster", "Zone"],
                how="left"
            )

            st.subheader(f"Tenant: {tenant} - Final Merged Table")
            st.dataframe(merged_tenant_final[["Cluster", "Zone", "Total Site Count", "Total Affected Site", "Elapsed Time (Decimal)", "Grid Availability", "Total Reedemed Hour"]])

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

        # Merge with Total Reedemed Hour for overall data
        overall_elapsed = (
            df_total_elapse.groupby(["Cluster", "Zone"])["Elapsed Time"]
            .sum()
            .reset_index()
        )
        overall_elapsed["Total Reedemed Hour"] = overall_elapsed["Elapsed Time"].apply(convert_to_decimal_hours)

        overall_final_merged = pd.merge(
            overall_final_merged,
            overall_elapsed[["Cluster", "Zone", "Total Reedemed Hour"]],
            on=["Cluster", "Zone"],
            how="left"
        )

        st.subheader("Overall Merged Table")
        st.dataframe(overall_final_merged[["Cluster", "Zone", "Total Site Count", "Total Affected Site", "Elapsed Time (Decimal)", "Grid Availability", "Total Reedemed Hour"]])

    except Exception as e:
        st.error(f"Error during merging: {e}")

# After the tenant-specific and overall merged data have been created, process and add the new columns
try:
    for tenant, tenant_merged in tenant_merged_data.items():
        # Display the initial table for debugging
        st.write(f"Initial table for Tenant: {tenant}")
        st.dataframe(tenant_merged)

        # Replace None/NaN with 0 and convert all numeric columns to float
        st.write("Step 1: Replacing None/NaN with 0 and converting to float")
        numeric_columns = ["Total Site Count", "Total Affected Site", "Elapsed Time (Decimal)", "Total Reedemed Hour"]
        tenant_merged[numeric_columns] = tenant_merged[numeric_columns].fillna(0).astype(float)
        st.dataframe(tenant_merged)

        # Step-by-step calculation of Total Allowable Limit (Hr)
        st.write("Step 2: Calculating Total Allowable Limit (Hr)")
        tenant_merged["Total Allowable Limit (Hr)"] = tenant_merged["Total Site Count"] * 24 * 30 * (1 - 0.9985)
        st.write("Calculated 'Total Allowable Limit (Hr)':")
        st.dataframe(tenant_merged[["Cluster", "Zone", "Total Allowable Limit (Hr)"]])

        # Step-by-step calculation of Remaining Hour
        st.write("Step 3: Calculating Remaining Hour")
        tenant_merged["Remaining Hour"] = tenant_merged["Total Allowable Limit (Hr)"] - tenant_merged["Elapsed Time (Decimal)"]
        st.write("Calculated 'Remaining Hour':")
        st.dataframe(tenant_merged[["Cluster", "Zone", "Remaining Hour"]])

        # Display the tenant-specific table with the new columns
        st.subheader(f"Tenant: {tenant} - Final Merged Table")
        st.dataframe(
            tenant_merged[
                [
                    "Cluster",
                    "Zone",
                    "Total Site Count",
                    "Total Affected Site",
                    "Elapsed Time (Decimal)",
                    "Grid Availability",
                    "Total Reedemed Hour",
                    "Total Allowable Limit (Hr)",
                    "Remaining Hour",
                ]
            ]
        )

    # Debugging for the overall table
    st.write("Processing the overall merged table")
    st.write("Step 1: Replacing None/NaN with 0 and converting to float")
    numeric_columns = ["Total Site Count", "Total Affected Site", "Elapsed Time (Decimal)", "Total Reedemed Hour"]
    overall_final_merged[numeric_columns] = overall_final_merged[numeric_columns].fillna(0).astype(float)
    st.dataframe(overall_final_merged)

    # Step-by-step calculation of Total Allowable Limit (Hr) for overall table
    st.write("Step 2: Calculating Total Allowable Limit (Hr) for overall table")
    overall_final_merged["Total Allowable Limit (Hr)"] = overall_final_merged["Total Site Count"] * 24 * 30 * (1 - 0.9985)
    st.write("Calculated 'Total Allowable Limit (Hr)':")
    st.dataframe(overall_final_merged[["Cluster", "Zone", "Total Allowable Limit (Hr)"]])

    # Step-by-step calculation of Remaining Hour for overall table
    st.write("Step 3: Calculating Remaining Hour for overall table")
    overall_final_merged["Remaining Hour"] = overall_final_merged["Total Allowable Limit (Hr)"] - overall_final_merged["Elapsed Time (Decimal)"]
    st.write("Calculated 'Remaining Hour':")
    st.dataframe(overall_final_merged[["Cluster", "Zone", "Remaining Hour"]])

    # Display the overall table with the new columns
    st.subheader("Overall Merged Table")
    st.dataframe(
        overall_final_merged[
            [
                "Cluster",
                "Zone",
                "Total Site Count",
                "Total Affected Site",
                "Elapsed Time (Decimal)",
                "Grid Availability",
                "Total Reedemed Hour",
                "Total Allowable Limit (Hr)",
                "Remaining Hour",
            ]
        ]
    )
except Exception as e:
    st.error(f"Error during processing: {e}")




# Final Message
if rms_site_file and alarm_history_file and grid_data_file and total_elapse_file:
    st.sidebar.success("All files processed and merged successfully!")
