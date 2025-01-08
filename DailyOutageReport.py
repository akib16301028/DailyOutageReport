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
        zones_clusters_yesterday = df_yesterday[["Zone", "Cluster"]].drop_duplicates()
        zones_clusters_rms = df_rms_filtered[["Zone", "Cluster"]].drop_duplicates()

        # For each unique Zone and Cluster in the RMS Site List, match it with Yesterday DCDB-01 file and find Site Alias count
        zone_cluster_affected = []

        for _, row in zones_clusters_rms.iterrows():
            zone = row["Zone"]
            cluster = row["Cluster"]

            # Match the zones and clusters from the Yesterday DCDB-01 Primary Disconnect History
            matching_rows = df_yesterday[(df_yesterday["Zone"] == zone) & (df_yesterday["Cluster"] == cluster)]
            
            # Count the corresponding Site Aliases in the matching rows
            site_alias_count = matching_rows["Site Alias"].nunique()

            # Append the result as a dictionary
            zone_cluster_affected.append({
                "Zone": zone,
                "Cluster": cluster,
                "Total Affected Site": site_alias_count
            })

        # Convert the result into a DataFrame
        df_zone_cluster_affected = pd.DataFrame(zone_cluster_affected)

        # Now for each tenant, we will create a table grouped by Cluster and Zone, adding the Total Affected Site count
        for tenant in df_rms_filtered["Tenant"].unique():
            tenant_df = df_rms_filtered[df_rms_filtered["Tenant"] == tenant]
            
            # Group data by Cluster and Zone
            grouped_df = tenant_df.groupby(["Cluster", "Zone"]).size().reset_index(name="Total Site Count")

            # Merge with the previously computed Total Affected Site count
            grouped_df = pd.merge(grouped_df, df_zone_cluster_affected, on=["Cluster", "Zone"], how="left").fillna(0)

            # Display the table for each tenant
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
 
