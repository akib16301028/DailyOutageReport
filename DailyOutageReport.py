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

        # Standardize tenant names in Yesterday DCDB-01 Primary Disconnect History
        df_yesterday["Tenant"] = df_yesterday["Tenant"].apply(standardize_tenant)

        # Display the RMS Site List table for debugging
        debug_columns = ["Site", "Site Alias", "Zone", "Cluster", "Tenant"]
        st.subheader("Filtered RMS Site List with Extracted Tenant")
        st.dataframe(df_rms_filtered[debug_columns])

        # Create a set of all unique Cluster-Zone combinations
        all_cluster_zone = df_yesterday[["Cluster", "Zone"]].drop_duplicates()

        # Count sites per zone and tenant
        site_count_per_zone = (
            df_rms_filtered.groupby(["Tenant", "Zone"])
            .size()
            .reset_index(name="Total Site Count")
        )
        
        # Merge site count into the main tenant table
        tenant_tables = []
        for tenant in tenant_names:
            tenant_df = df_yesterday[df_yesterday["Tenant"] == tenant]
            
            # Group data by Cluster and Zone
            grouped_df = tenant_df.groupby(["Cluster", "Zone"]).size().reset_index(name="Count")
            
            # Merge with site counts from RMS Site List
            grouped_df = grouped_df.merge(
                site_count_per_zone[site_count_per_zone["Tenant"] == tenant],
                on="Zone",
                how="left",
            ).fillna(0)
            
            # Merge with all possible Cluster-Zone combinations to ensure all zones are shown
            grouped_df = pd.merge(
                all_cluster_zone, 
                grouped_df, 
                on=["Cluster", "Zone"], 
                how="left"
            ).fillna(0)
            
            # Add Total Site Count column
            grouped_df["Total Site Count"] = grouped_df["Total Site Count"].astype(int)
            
            # Add to tenant table list
            tenant_tables.append(grouped_df)
            
            # Display table for the specific tenant
            st.subheader(f"Table for Tenant: {tenant}")
            st.dataframe(grouped_df)

        # Display overall total
        overall_total = site_count_per_zone.groupby("Zone")["Total Site Count"].sum().reset_index()
        st.subheader("Overall Total Site Count by Zone")
        st.dataframe(overall_total)

    except Exception as e:
        st.error(f"Error processing RMS Site List: {e}")

# Final Message
if yesterday_file and rms_site_file:
    st.sidebar.success("All files have been uploaded and processed successfully!")
