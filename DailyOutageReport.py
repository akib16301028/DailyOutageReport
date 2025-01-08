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
        # Load Yesterday DCDB-01 Primary Disconnect History file (skip first 2 rows for header)
        df_yesterday = pd.read_excel(yesterday_file, skiprows=2)

        # Load RMS Site List file (skip first 2 rows for header)
        df_rms_site = pd.read_excel(rms_site_file, skiprows=2)

        # Filter out sites starting with 'L' in the RMS Site List
        df_rms_filtered = df_rms_site[~df_rms_site["Site"].str.startswith("L", na=False)]

        # Extract tenant from Site Alias in RMS Site List
        def extract_tenant(site_alias):
            if isinstance(site_alias, str) and "(" in site_alias and ")" in site_alias:
                return site_alias.split("(")[1].split(")")[0].strip()
            return "Unknown"

        df_rms_filtered["Tenant"] = df_rms_filtered["Site Alias"].apply(extract_tenant)

        # Define a mapping for tenant name standardization
        tenant_mapping = {
            "BANJO": "Banjo",
            "BL": "Banglalink",
            "GP": "Grameenphone",
            "ROBI": "Robi",
        }

        def standardize_tenant(tenant_name):
            return tenant_mapping.get(tenant_name, tenant_name)

        # Standardize tenant names in RMS Site List
        df_rms_filtered["Tenant"] = df_rms_filtered["Tenant"].apply(standardize_tenant)

        # Extract Zones and Clusters from both files for matching
        zones_clusters_yesterday = df_yesterday[["Zone", "Cluster", "Tenant"]].drop_duplicates()

        # Create an empty list to store the results
        zone_cluster_affected = []

        # For each tenant, match and group by Zone, then count the Site Alias entries
        for tenant in df_rms_filtered["Tenant"].unique():
            tenant_df_yesterday = df_yesterday[df_yesterday["Tenant"] == tenant]

            # Group by Zone and Cluster
            grouped = tenant_df_yesterday.groupby(["Zone", "Cluster"]).agg({"Site": "count"}).reset_index()

            # Add the Total Affected Site count to the table
            grouped["Total Affected Site"] = grouped["Site"]

            # Now append the result
            for _, row in grouped.iterrows():
                zone_cluster_affected.append({
                    "Tenant": tenant,
                    "Zone": row["Zone"],
                    "Cluster": row["Cluster"],
                    "Total Site Count": row["Site"],
                    "Total Affected Site": row["Total Affected Site"]
                })

        # Convert the list into a DataFrame
        df_zone_cluster_affected = pd.DataFrame(zone_cluster_affected)

        # Now display the table for each tenant
        for tenant in df_zone_cluster_affected["Tenant"].unique():
            tenant_table = df_zone_cluster_affected[df_zone_cluster_affected["Tenant"] == tenant]
            
            st.subheader(f"Tenant: {tenant} - Zone and Cluster Site Counts")
            st.dataframe(tenant_table[["Zone", "Cluster", "Total Site Count", "Total Affected Site"]])

        # Display the overall total Site count across all tenants
        overall_total = df_zone_cluster_affected.groupby("Zone").agg({"Total Site Count": "sum"}).reset_index()

        st.subheader("Overall Total Site Count by Zone")
        st.dataframe(overall_total)

    except Exception as e:
        st.error(f"Error processing RMS Site List or Yesterday DCDB-01 file: {e}")

# Final Message
if yesterday_file and rms_site_file:
    st.sidebar.success("Both files processed successfully!")
