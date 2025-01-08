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
        for tenant in tenant_names:
            tenant_df = df_rms_filtered[df_rms_filtered["Tenant"] == tenant]

            # Group data by Cluster and Zone
            grouped_df = tenant_df.groupby(["Cluster", "Zone"]).size().reset_index(name="Total Site Count")

            # Sort by Cluster and Zone
            grouped_df = grouped_df.sort_values(by=["Cluster", "Zone"])

            # Display table for the specific Cluster and Zone
            st.subheader(f"Tenant: {tenant} - Cluster and Zone Site Counts")
            display_table = grouped_df[["Cluster", "Zone", "Total Site Count"]]

            st.dataframe(display_table)

        # Display overall total (total site count for each zone)
        overall_total = df_rms_filtered.groupby("Zone").size().reset_index(name="Total Site Count")
        st.subheader("Overall Total Site Count by Zone")
        st.dataframe(overall_total)

    except Exception as e:
        st.error(f"Error processing RMS Site List: {e}")

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

        # Display tables for each tenant and group by Cluster and Zone
        for tenant in tenant_names_history:
            tenant_df_history = df_alarm_history[df_alarm_history["Tenant"] == tenant]

            # Group data by Cluster and Zone
            grouped_df_history = tenant_df_history.groupby(["Cluster", "Zone"]).size().reset_index(name="Total Site Count")

            # Sort by Cluster and Zone
            grouped_df_history = grouped_df_history.sort_values(by=["Cluster", "Zone"])

            # Display table for the specific Cluster and Zone
            st.subheader(f"Tenant: {tenant} - Yesterday Alarm History Cluster and Zone Site Counts")
            display_table_history = grouped_df_history[["Cluster", "Zone", "Total Site Count"]]

            st.dataframe(display_table_history)

        # Display overall total (total site count for each zone)
        overall_total_history = df_alarm_history.groupby("Zone").size().reset_index(name="Total Site Count")
        st.subheader("Overall Total Site Count by Zone from Yesterday Alarm History")
        st.dataframe(overall_total_history)

    except Exception as e:
        st.error(f"Error processing Yesterday Alarm History: {e}")

# Final Message
if rms_site_file and alarm_history_file:
    st.sidebar.success("All files processed successfully!")
