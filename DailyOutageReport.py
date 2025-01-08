import streamlit as st
import pandas as pd
from io import StringIO

# Set the title of the application
st.title("Data Upload and Tenant-Wise Analysis Application")

# Sidebar for uploading files
st.sidebar.header("Upload Required Excel Files")

# Step 1: Upload Yesterday DCDB-01 Primary Disconnect History
yesterday_file = st.sidebar.file_uploader(
    "1. Yesterday DCDB-01 Primary Disconnect History", type=["xlsx", "xls"]
)

if yesterday_file:
    st.success("Yesterday's disconnect history uploaded successfully!")
    # Read the Excel file starting from row 3
    df_yesterday = pd.read_excel(yesterday_file, skiprows=2)
    
    # Extract required columns for processing
    tenant_column = "Tenant"  # Replace with actual column name
    cluster_column = "Cluster"  # Replace with actual column name
    zone_column = "Zone"  # Replace with actual column name
    
    required_columns = [tenant_column, cluster_column, zone_column]
    if all(col in df_yesterday.columns for col in required_columns):
        tenants = df_yesterday[tenant_column].unique()
        
        # Group by Tenant, Cluster (RIO), and Zone
        tenant_grouped_data = (
            df_yesterday.groupby([tenant_column, cluster_column, zone_column])
            .size()
            .reset_index(name="Count")
        )
        
        # Overall tenant count table
        overall_data = (
            tenant_grouped_data.groupby([cluster_column, zone_column])
            .agg({"Count": "sum"})
            .reset_index()
        )
        overall_data["Tenant"] = "Overall"

        # Display selectbox for tenant selection
        selected_tenant = st.sidebar.selectbox("Select Tenant or View All", ["All"] + list(tenants))

        # Filter based on selection
        if selected_tenant == "All":
            display_data = overall_data.copy()
        else:
            display_data = tenant_grouped_data[tenant_grouped_data[tenant_column] == selected_tenant].copy()

        # Merge and center RIO (Cluster) names
        display_data["RIO"] = display_data[cluster_column]
        display_data = display_data.drop(columns=[cluster_column])
        
        # Display the table
        st.subheader(f"Tenant Data: {selected_tenant}")
        st.dataframe(display_data)

        # Display overall count table
        st.subheader("Overall Tenant Count Table")
        st.dataframe(overall_data)
    else:
        st.error(f"Required columns missing: {', '.join([col for col in required_columns if col not in df_yesterday.columns])}")

# Step 2: Upload RMS Site List
rms_site_file = st.sidebar.file_uploader(
    "2. RMS Site List", type=["xlsx", "xls"]
)

if rms_site_file:
    st.success("RMS Site List uploaded successfully!")
    # Read RMS Site List starting from row 3
    df_rms_site = pd.read_excel(rms_site_file, skiprows=2)
    
    site_column = "Site"
    site_alias_column = "Site Alias"
    zone_column = "Zone"
    
    if all(col in df_rms_site.columns for col in [site_column, site_alias_column, zone_column]):
        # Extract tenant from Site Alias
        def extract_tenant(site_alias):
            if "(" in site_alias and ")" in site_alias:
                return site_alias.split("(")[-1].replace(")", "").strip()
            return None

        df_rms_site["Tenant"] = df_rms_site[site_alias_column].apply(extract_tenant)
        
        # Filter out sites starting with "L"
        df_rms_site = df_rms_site[~df_rms_site[site_column].str.startswith("L")]

        # Count sites zone-wise for each tenant
        tenant_zone_site_count = (
            df_rms_site.groupby(["Tenant", zone_column])
            .size()
            .reset_index(name="Total Site Count")
        )

        # Match zones with tenant table and merge site counts
        site_count_merged = tenant_grouped_data.merge(
            tenant_zone_site_count,
            how="left",
            left_on=[tenant_column, zone_column],
            right_on=["Tenant", zone_column]
        )
        
        # Fill missing counts with 0
        site_count_merged["Total Site Count"] = site_count_merged["Total Site Count"].fillna(0).astype(int)
        
        # Display the updated table
        st.subheader("Updated Tenant Table with Total Site Count")
        st.dataframe(site_count_merged)
        
        # Overall count
        overall_site_count = (
            df_rms_site.groupby(zone_column)
            .size()
            .reset_index(name="Total Site Count")
        )
        st.subheader("Overall Zone-Wise Site Count")
        st.dataframe(overall_site_count)
    else:
        st.error("Required columns missing from RMS Site List.")

# Final Message
if yesterday_file and rms_site_file:
    st.sidebar.success("All files have been uploaded and processed successfully!")
