import streamlit as st
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

# Set the title of the application
st.title("Tenant-Wise Data Processing Application")

# Sidebar for uploading files
st.sidebar.header("Upload Required Excel Files")

# Step 1: Upload RMS Site List
rms_site_file = st.sidebar.file_uploader(
    "1. RMS Site List", type=["xlsx", "xls"]
)
if rms_site_file:
    st.success("RMS Site List uploaded successfully!")

    try:
        # Read RMS Site List starting from row 3
        df_rms_site = pd.read_excel(rms_site_file, skiprows=2)

        # Define a mapping for tenant name standardization
        tenant_mapping = {
            "BANJO": "Banjo",
            "BL": "Banglalink",
            "GP": "Grameenphone",
            "ROBI": "Robi",
        }

        # Function to standardize tenant names
        def standardize_tenant(tenant_name):
            return tenant_mapping.get(tenant_name, tenant_name)

        # Filter out sites starting with 'L'
        df_rms_filtered = df_rms_site[~df_rms_site["Site"].str.startswith("L", na=False)]

        # Extract tenant from Site Alias (updated to find tenant from any bracketed name)
        def extract_tenant(site_alias):
            if isinstance(site_alias, str):
                # Find all text inside parentheses
                brackets = site_alias.split("(")
                tenants = [part.split(")")[0].strip() for part in brackets if ")" in part]

                # Check if BANJO exists in any of the extracted tenant names
                for tenant in tenants:
                    if "BANJO" in tenant:
                        return "Banjo"
                return tenants[0] if tenants else "Unknown"  # Return the first tenant found if no 'BANJO'
            return "Unknown"

        # Add Tenant column
        df_rms_filtered["Tenant"] = df_rms_filtered["Site Alias"].apply(extract_tenant)

        # Standardize tenant names in RMS Site List
        df_rms_filtered["Tenant"] = df_rms_filtered["Tenant"].apply(standardize_tenant)

        # Get unique tenants
        tenant_names = df_rms_filtered["Tenant"].unique()

        # Store tenant-wise data for aggregation later
        tenant_zone_rms = {}

        for tenant in tenant_names:
            tenant_df = df_rms_filtered[df_rms_filtered["Tenant"] == tenant]

            # Group data by Cluster and Zone
            grouped_df = tenant_df.groupby(["Cluster", "Zone"]).size().reset_index(name="Total Site Count")

            # Sort by Cluster and Zone
            grouped_df = grouped_df.sort_values(by=["Cluster", "Zone"])

            tenant_zone_rms[tenant] = grouped_df

        # Step 2: Upload Yesterday Alarm History File
        alarm_history_file = st.sidebar.file_uploader(
            "2. Yesterday Alarm History", type=["xlsx", "xls"]
        )
        if alarm_history_file:
            st.success("Yesterday Alarm History uploaded successfully!")

            try:
                # Read Yesterday Alarm History file, skip first 3 rows
                df_alarm_history = pd.read_excel(alarm_history_file, skiprows=2)

                # Filter out sites starting with 'L' in the Site column of Yesterday Alarm History
                df_alarm_history = df_alarm_history[~df_alarm_history["Site"].str.startswith("L", na=False)]

                # Standardize tenant names in Yesterday Alarm History file
                df_alarm_history["Tenant"] = df_alarm_history["Tenant"].apply(standardize_tenant)

                # Get unique tenants from Yesterday Alarm History
                tenant_names_history = df_alarm_history["Tenant"].unique()

                # Store merged data for all tenants
                merged_all_tenants = pd.DataFrame()

                # Display tenant-wise tables
                for tenant in tenant_names_history:
                    # Get RMS Site List data for the tenant
                    rms_data = tenant_zone_rms.get(tenant, pd.DataFrame())

                    # Get Alarm History data for the tenant
                    alarm_data = df_alarm_history[df_alarm_history["Tenant"] == tenant]

                    # Group Alarm History data by Cluster and Zone
                    grouped_alarm_data = alarm_data.groupby(["Cluster", "Zone"]).size().reset_index(name="Total Affected Site")

                    # Sum Elapsed Time (in seconds) for each Cluster and Zone
                    alarm_data["Elapsed Time"] = pd.to_timedelta(alarm_data["Elapsed Time"], errors="coerce")
                    elapsed_time_sum = alarm_data.groupby(["Cluster", "Zone"])["Elapsed Time"].sum().reset_index()

                    # Convert Elapsed Time sum into 24-hour format (HH:MM:SS) to decimal hours
                    def convert_to_decimal_hours(elapsed_time):
                        if pd.notnull(elapsed_time):
                            # Convert to seconds and then to decimal hours
                            total_seconds = elapsed_time.total_seconds()
                            decimal_hours = total_seconds / 3600  # Convert seconds to hours
                            # Round to 2 decimal places using ROUND_HALF_UP for standard rounding behavior
                            return Decimal(decimal_hours).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
                        return Decimal(0.0)

                    elapsed_time_sum["Elapsed Time (Decimal)"] = elapsed_time_sum["Elapsed Time"].apply(convert_to_decimal_hours)

                    # Merge RMS data with Alarm History data
                    merged_data = pd.merge(rms_data, grouped_alarm_data, on=["Cluster", "Zone"], how="left")
                    merged_data = pd.merge(merged_data, elapsed_time_sum[["Cluster", "Zone", "Elapsed Time (Decimal)"]], on=["Cluster", "Zone"], how="left")

                    # If there is no matching data in Alarm History, set the count to 0
                    merged_data["Total Affected Site"] = merged_data["Total Affected Site"].fillna(0)
                    merged_data["Elapsed Time (Decimal)"] = merged_data["Elapsed Time (Decimal)"].fillna(Decimal(0.0))

                    # Display tenant-wise merged table
                    st.subheader(f"Tenant: {tenant} - Cluster and Zone Site Counts with Affected Sites and Elapsed Time")
                    st.dataframe(merged_data[["Cluster", "Zone", "Total Site Count", "Total Affected Site", "Elapsed Time (Decimal)"]])

                    # Append the merged data to the overall data
                    merged_all_tenants = pd.concat([merged_all_tenants, merged_data])

                # Group by Cluster and Zone for all tenants together
                overall_merged_data = merged_all_tenants.groupby(["Cluster", "Zone"]).agg({
                    "Total Site Count": "sum",
                    "Total Affected Site": "sum",
                    "Elapsed Time (Decimal)": "sum"
                }).reset_index()

                # Display merged table for all tenants
                st.subheader("Overall Merged Cluster and Zone Site Counts (with Affected Sites and Elapsed Time) for All Tenants")
                st.dataframe(overall_merged_data[["Cluster", "Zone", "Total Site Count", "Total Affected Site", "Elapsed Time (Decimal)"]])

            except Exception as e:
                st.error(f"Error processing Yesterday Alarm History: {e}")

        # Step 3: Upload Grid Data (with 3 sheets)
        grid_data_file = st.sidebar.file_uploader("3. Upload Grid Data", type=["xlsx", "xls"])

        if grid_data_file:
            st.success("Grid Data uploaded successfully!")

            try:
                # Read the 'Site Wise Summary' sheet from the Grid Data
                df_grid_data = pd.read_excel(grid_data_file, sheet_name="Site Wise Summary", skiprows=2)

                # Display the column names of Grid Data to verify
                st.write("Grid Data columns:", df_grid_data.columns)

                # Clean column names by stripping spaces
                df_grid_data.columns = df_grid_data.columns.str.strip()

                # Filter out sites starting with 'L' in the Site column
                df_grid_data = df_grid_data[~df_grid_data["Site"].str.startswith("L", na=False)]

                # Handle the tenant-wise grouping
                tenant_names_grid = df_grid_data["Tenant Name"].unique()

                # Store data for aggregation
                tenant_zone_grid = {}

                # For each tenant, group by Cluster and Zone
                for tenant in tenant_names_grid:
                    tenant_df = df_grid_data[df_grid_data["Tenant Name"] == tenant]

                    # Group by Cluster and Zone
                    grouped_df = tenant_df.groupby(["Cluster", "Zone"]).agg({
                        "Site Alias": "count",  # Count the number of Site Alias in each Cluster-Zone
                        "AC Availability (%)": "mean",  # Average of AC Availability
                    }).reset_index()

                    tenant_zone_grid[tenant] = grouped_df

                    # Display tenant-wise table
                    st.subheader(f"Tenant: {tenant} - AC Availability by Cluster and Zone")
                    st.dataframe(grouped_df[["Cluster", "Zone", "Site Alias", "AC Availability (%)"]])

                # Create the combined table for all tenants
                combined_grid_data = df_grid_data.groupby(["Cluster", "Zone"]).agg({
                    "Site Alias": "count",  # Count all Site Alias
                    "AC Availability (%)": "mean",  # Average AC Availability
                }).reset_index()

                # Merge overall merged data with the combined grid data
                merged_final_data = pd.merge(
                    overall_merged_data,
                    combined_grid_data[["Cluster", "Zone", "AC Availability (%)"]],
                    on=["Cluster", "Zone"],
                    how="left"
                )

                # Add a new column for Grid Availability
                merged_final_data["Grid Availability"] = merged_final_data["AC Availability (%)"]

                # Display the final merged data
                st.subheader("Final Merged Table (with Grid Availability)")
                st.dataframe(merged_final_data[["Cluster", "Zone", "Total Site Count", "Total Affected Site", "Elapsed Time (Decimal)", "Grid Availability"]])

            except Exception as e:
                st.error(f"Error processing Grid Data: {e}")

# Final Message
if rms_site_file and alarm_history_file and grid_data_file:
    st.sidebar.success("All files processed successfully!")
