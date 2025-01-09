import streamlit as st
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

# Set the title of the application
st.title("Tenant-Wise Data Processing Application")

# Sidebar for uploading files
st.sidebar.header("Upload Required Excel Files")

# Step 1: Upload RMS Site List
rms_site_file = st.sidebar.file_uploader("1. RMS Site List", type=["xlsx", "xls"])
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
                        return "Banjo"  # Return 'Banjo' if it is found
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
        alarm_history_file = st.sidebar.file_uploader("2. Yesterday Alarm History", type=["xlsx", "xls"])
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

        # Step 3: Upload Grid Data File
        grid_data_file = st.sidebar.file_uploader("3. Grid Data", type=["xlsx", "xls"])
        if grid_data_file:
            st.success("Grid Data uploaded successfully!")

            try:
                # Read Grid Data (assuming sheet name is 'Site Wise Summary')
                df_grid = pd.read_excel(grid_data_file, sheet_name="Site Wise Summary", skiprows=2)

                # Filter out sites starting with 'L' in the Site column of Grid Data
                df_grid = df_grid[~df_grid["Site"].str.startswith("L", na=False)]

                # Select necessary columns
                columns_to_select = [
                    "Rms Station", "Site", "Site Alias", "Zone", "Cluster", "Tenant Name", "AC Availability (%)", "DC Availability (%)"
                ]

                df_grid = df_grid[columns_to_select]

                # Standardize tenant names in Grid Data
                df_grid["Tenant Name"] = df_grid["Tenant Name"].apply(standardize_tenant)

                # Get unique tenants from Grid Data
                tenant_names_grid = df_grid["Tenant Name"].unique()

                # Store tenant-wise Grid Data for aggregation later
                tenant_zone_grid = {}

                for tenant in tenant_names_grid:
                    tenant_df = df_grid[df_grid["Tenant Name"] == tenant]

                    # Group data by Cluster and Zone, calculating average AC Availability (%)
                    grouped_grid_data = tenant_df.groupby(["Cluster", "Zone"]).agg({
                        "AC Availability (%)": "mean"
                    }).reset_index()

                    grouped_grid_data.rename(columns={"AC Availability (%)": "Grid Availability"}, inplace=True)

                    tenant_zone_grid[tenant] = grouped_grid_data

                    # Display tenant-wise grid data table
                    st.subheader(f"Tenant: {tenant} - AC Availability by Cluster and Zone")
                    st.dataframe(grouped_grid_data)

                # Group Grid Data for all tenants together
                overall_grid_data = df_grid.groupby(["Cluster", "Zone"]).agg({
                    "AC Availability (%)": "mean"
                }).reset_index()

                overall_grid_data.rename(columns={"AC Availability (%)": "Grid Availability"}, inplace=True)

                # Display overall grid data table
                st.subheader("Overall AC Availability by Cluster and Zone for All Tenants")
                st.dataframe(overall_grid_data)

            except Exception as e:
                st.error(f"Error processing Grid Data: {e}")

        # Step 4: Merge Tables
        if rms_site_file and alarm_history_file and grid_data_file:
            try:
                # Merge tenant-specific tables with Grid Data
                for tenant in tenant_names_history:
                    if tenant in tenant_zone_grid:
                        tenant_alarm_data = merged_all_tenants[merged_all_tenants["Tenant"] == tenant]
                        tenant_grid_data = tenant_zone_grid[tenant]

                        # Merge tenant-specific tables
                        merged_tenant_data = pd.merge(tenant_alarm_data, tenant_grid_data, on=["Cluster", "Zone"], how="left")

                        # Display merged tenant-specific data
                        st.subheader(f"Tenant: {tenant} - Merged Data with Grid Availability")
                        st.dataframe(merged_tenant_data)

                # Merge overall table with overall Grid Data
                overall_merged_with_grid = pd.merge(overall_merged_data, overall_grid_data, on=["Cluster", "Zone"], how="left")

                # Display overall merged table
                st.subheader("Overall Merged Data with Grid Availability for All Tenants")
                st.dataframe(overall_merged_with_grid)

            except Exception as e:
                st.error(f"Error merging tables: {e}")

        # Step 5: Upload Total Elapse Till Date File
        elapse_file = st.sidebar.file_uploader("4. Total Elapse Till Date", type=["xlsx", "xls"])
        if elapse_file:
            st.success("Total Elapse Till Date uploaded successfully!")

            try:
                # Read Total Elapse Till Date file
                df_elapse = pd.read_excel(elapse_file)

                # Filter out sites starting with 'L'
                df_elapse = df_elapse[~df_elapse["Site"].str.startswith("L", na=False)]

                # Select necessary columns
                columns_to_select = [
                    "Rms Station", "Site", "Site Alias", "Zone", "Cluster", "Node", "Tag", "Tenant", "Elapsed Time"
                ]

                df_elapse = df_elapse[columns_to_select]

                # Standardize tenant names in Elapse Data
                df_elapse["Tenant"] = df_elapse["Tenant"].apply(standardize_tenant)

                # Get unique tenants from Elapse Data
                tenant_names_elapse = df_elapse["Tenant"].unique()

                # Store tenant-wise Elapse Data for aggregation later
                tenant_zone_elapse = {}

                for tenant in tenant_names_elapse:
                    tenant_df = df_elapse[df_elapse["Tenant"] == tenant]

                    # Group data by Cluster and Zone, summing Elapsed Time
                    tenant_df["Elapsed Time"] = pd.to_timedelta(tenant_df["Elapsed Time"], errors="coerce")
                    grouped_elapse_data = tenant_df.groupby(["Cluster", "Zone"]).agg({
                        "Elapsed Time": "sum"
                    }).reset_index()

                    # Convert Elapsed Time to total seconds
                    grouped_elapse_data["Elapsed Time (Seconds)"] = grouped_elapse_data["Elapsed Time"].dt.total_seconds()

                    tenant_zone_elapse[tenant] = grouped_elapse_data

                    # Display tenant-wise elapse data table
                    st.subheader(f"Tenant: {tenant} - Elapsed Time by Cluster and Zone")
                    st.dataframe(grouped_elapse_data[["Cluster", "Zone", "Elapsed Time (Seconds)"]])

                # Group Elapse Data for all tenants together
                overall_elapse_data = df_elapse.groupby(["Cluster", "Zone"]).agg({
                    "Elapsed Time": "sum"
                }).reset_index()

                # Convert Elapsed Time to total seconds
                overall_elapse_data["Elapsed Time (Seconds)"] = overall_elapse_data["Elapsed Time"].dt.total_seconds()

                # Display overall elapse data table
                st.subheader("Overall Elapsed Time by Cluster and Zone for All Tenants")
                st.dataframe(overall_elapse_data[["Cluster", "Zone", "Elapsed Time (Seconds)"]])

            except Exception as e:
                st.error(f"Error processing Total Elapse Till Date: {e}")

    except Exception as e:
        st.error(f"Error processing RMS Site List: {e}")

# Final Message
if rms_site_file and alarm_history_file and grid_data_file and elapse_file:
    st.sidebar.success("All files processed successfully!")
