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

# Final Message
if rms_site_file:
    st.sidebar.success("RMS Site List processed successfully!")
