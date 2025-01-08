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
if yesterday_file:
    st.success("Yesterday's disconnect history uploaded successfully!")
    df_yesterday = pd.read_excel(yesterday_file, skiprows=2)  # Data starts from row 3
    tenant_names = df_yesterday["Tenant"].unique()

# Step 2: Upload RMS Site List
rms_site_file = st.sidebar.file_uploader(
    "2. RMS Site List", type=["xlsx", "xls"]
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
        
        # Extract tenant from Site Alias
        def extract_tenant(site_alias):
            if isinstance(site_alias, str) and "(" in site_alias and ")" in site_alias:
                return site_alias.split("(")[1].split(")")[0].strip()
            return "Unknown"
        
        # Add Tenant column
        df_rms_filtered["Tenant"] = df_rms_filtered["Site Alias"].apply(extract_tenant)

        # Standardize tenant names in RMS Site List
        df_rms_filtered["Tenant"] = df_rms_filtered["Tenant"].apply(standardize_tenant)

        # Display the tenant-wise zone and site count table
        st.subheader("Tenant-wise Zone Site Count")
        tenant_zone_count = (
            df_rms_filtered.groupby(["Tenant", "Zone"])
            .size()
            .reset_index(name="Site Count")
        )
        st.dataframe(tenant_zone_count)

        # Display the complete RMS site list table with Tenant, Site, Zone, Cluster for debugging
        st.subheader("Complete RMS Site List")
        debug_table = df_rms_filtered[["Site", "Site Alias", "Zone", "Cluster", "Tenant"]]
        st.dataframe(debug_table)

    except Exception as e:
        st.error(f"Error processing RMS Site List: {e}")

# Final Message
if yesterday_file and rms_site_file:
    st.sidebar.success("All files have been uploaded and processed successfully!")
