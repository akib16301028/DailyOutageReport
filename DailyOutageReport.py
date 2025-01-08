import streamlit as st
import pandas as pd

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
                        return "Banjo"  # Return 'Banjo' if it is found
                return tenants[0] if tenants else "Unknown"  # Return the first tenant found if no 'BANJO'
            return "Unknown"
        
        # Add Tenant column
        df_rms_filtered["Tenant"] = df_rms_filtered["Site Alias"].apply(extract_tenant)

        # Standardize tenant names in RMS Site List
        df_rms_filtered["Tenant"] = df_rms_filtered["Tenant"].apply(standardize_tenant)

        # Get unique tenants
        tenant_names = df_rms_filtered["Tenant"].unique()

        # Display tables for each tenant and group by Cluster and Zone
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

                # Standardize tenant names in Yesterday Alarm History file
                df_alarm_history["Tenant"] = df_alarm_history["Tenant"].apply(standardize_tenant)

                # Get unique tenants from Yesterday Alarm History
                tenant_names_history = df_alarm_history["Tenant"].unique()

                # Display merged tables for each tenant and group by Cluster and Zone
                tenant_zone_merged = {}

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

                    # Convert Elapsed Time sum into 24-hour format (HH:MM:SS)
                    elapsed_time_sum["Elapsed Time"] = elapsed_time_sum["Elapsed Time"].apply(lambda x: str(x).split()[2] if pd.notnull(x) else "00:00:00")

                    # Merge RMS data with Alarm History data
                    merged_data = pd.merge(rms_data, grouped_alarm_data, on=["Cluster", "Zone"], how="left")
                    merged_data = pd.merge(merged_data, elapsed_time_sum, on=["Cluster", "Zone"], how="left")

                    # If there is no matching data in Alarm History, set the count to 0
                    merged_data["Total Affected Site"] = merged_data["Total Affected Site"].fillna(0)
                    merged_data["Elapsed Time"] = merged_data["Elapsed Time"].fillna("00:00:00")

                    # Add merged data to the dictionary
                    tenant_zone_merged[tenant] = merged_data

                # Display merged table for each tenant
                for tenant, merged_df in tenant_zone_merged.items():
                    st.subheader(f"Tenant: {tenant} - Merged Cluster and Zone Site Counts (with Affected Sites and Elapsed Time)")
                    st.dataframe(merged_df[["Cluster", "Zone", "Total Site Count", "Total Affected Site", "Elapsed Time"]])

            except Exception as e:
                st.error(f"Error processing Yesterday Alarm History: {e}")

    except Exception as e:
        st.error(f"Error processing RMS Site List: {e}")

# Final Message
if rms_site_file and alarm_history_file:
    st.sidebar.success("All files processed successfully!")
