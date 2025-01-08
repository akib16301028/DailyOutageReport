import streamlit as st
import pandas as pd

# Set the title of the application
st.title("Tenant-Wise Data Processing Application")

# Sidebar for uploading files
st.sidebar.header("Upload Required Excel Files")

# Step 1: Upload Yesterday DCDB-01 Primary Disconnect History
yesterday_file = st.sidebar.file_uploader(
    "1. Yesterday DCDB-01 Primary Disconnect History", type=["xlsx", "xls"]
)

# Step 2: Upload RMS Site List
rms_site_file = st.sidebar.file_uploader(
    "2. RMS Site List", type=["xlsx", "xls"]
)

if yesterday_file and rms_site_file:
    st.success("Both files uploaded successfully!")

    try:
        # Load Yesterday DCDB-01 Primary Disconnect History file
        df_yesterday = pd.read_excel(yesterday_file, skiprows=2)  # Data starts from row 3
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

        # Extract tenant from Site Alias
        def extract_tenant(site_alias):
            if isinstance(site_alias, str) and "(" in site_alias and ")" in site_alias:
                return site_alias.split("(")[1].split(")")[0].strip()
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

            # VLOOKUP-like approach: Match Zone names with Yesterday DCDB-01 Primary Disconnect History and find affected sites
            zone_vlookup = df_yesterday[["Zone"]].drop_duplicates()
            zone_vlookup["Total Affected Site"] = zone_vlookup["Zone"].apply(
                lambda zone: df_rms_filtered[df_rms_filtered["Zone"] == zone].shape[0]
            )

            # Merge the zone VLOOKUP result into the grouped table
            grouped_df = pd.merge(grouped_df, zone_vlookup, on="Zone", how="left").fillna(0)

            # Sort by Cluster and Zone
            grouped_df = grouped_df.sort_values(by=["Cluster", "Zone"])

            # Display table for the specific Cluster and Zone
            st.subheader(f"Tenant: {tenant} - Cluster and Zone Site Counts")
            display_table = grouped_df[["Cluster", "Zone", "Total Site Count", "Total Affected Site"]]

            st.dataframe(display_table)

        # Display overall total (total site count for each zone)
        overall_total = df_rms_filtered.groupby("Zone").size().reset_index(name="Total Site Count")
        st.subheader("Overall Total Site Count by Zone")
        st.dataframe(overall_total)

    except Exception as e:
        st.error(f"Error processing RMS Site List or Yesterday DCDB-01 file: {e}")

# Final Message
if yesterday_file and rms_site_file:
    st.sidebar.success("Both files processed successfully!")
