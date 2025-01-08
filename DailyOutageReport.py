import streamlit as st
import pandas as pd

# Set the title of the application
st.title("Tenant-Wise Affected Site Count")

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
        # Load Yesterday DCDB-01 Primary Disconnect History
        df_yesterday = pd.read_excel(yesterday_file, skiprows=2)
        required_columns_yesterday = ["Zone", "Cluster", "Site Alias"]

        if not all(col in df_yesterday.columns for col in required_columns_yesterday):
            st.error(f"Missing columns in Yesterday DCDB-01 file. Required: {required_columns_yesterday}")
            st.write("Detected Columns:", df_yesterday.columns.tolist())
            raise ValueError("Missing required columns in Yesterday DCDB-01 file")

        # Load RMS Site List
        df_rms_site = pd.read_excel(rms_site_file, skiprows=2)
        required_columns_rms = ["Zone", "Cluster", "Site Alias", "Site"]

        if not all(col in df_rms_site.columns for col in required_columns_rms):
            st.error(f"Missing columns in RMS Site List file. Required: {required_columns_rms}")
            st.write("Detected Columns:", df_rms_site.columns.tolist())
            raise ValueError("Missing required columns in RMS Site List file")

        # Filter out sites starting with 'L' in the RMS Site List
        df_rms_filtered = df_rms_site[~df_rms_site["Site"].str.startswith("L", na=False)]

        # Extract tenant from Site Alias in RMS Site List
        def extract_tenant(site_alias):
            if isinstance(site_alias, str) and "(" in site_alias and ")" in site_alias:
                return site_alias.split("(")[1].split(")")[0].strip()
            return "Unknown"

        df_rms_filtered["Tenant"] = df_rms_filtered["Site Alias"].apply(extract_tenant)

        # Standardize tenant names
        tenant_mapping = {
            "BANJO": "Banjo",
            "BL": "Banglalink",
            "GP": "Grameenphone",
            "ROBI": "Robi",
        }
        df_rms_filtered["Tenant"] = df_rms_filtered["Tenant"].apply(
            lambda x: tenant_mapping.get(x, x)
        )

        # Match Zone and Cluster and count Site Alias
        zone_cluster_affected = (
            df_yesterday.groupby(["Zone", "Cluster"])["Site Alias"].nunique().reset_index()
        )
        zone_cluster_affected.rename(columns={"Site Alias": "Total Affected Site"}, inplace=True)

        # Ensure all combinations of Zone and Cluster exist in affected table
        all_zones_clusters = df_rms_filtered[["Zone", "Cluster"]].drop_duplicates()
        zone_cluster_affected = pd.merge(
            all_zones_clusters,
            zone_cluster_affected,
            on=["Zone", "Cluster"],
            how="left"
        ).fillna(0)

        # Tenant-wise affected sites table
        for tenant in df_rms_filtered["Tenant"].unique():
            tenant_df = df_rms_filtered[df_rms_filtered["Tenant"] == tenant]
            tenant_zones_clusters = tenant_df[["Zone", "Cluster"]].drop_duplicates()

            # Merge tenant's zones and clusters with affected data
            tenant_affected = pd.merge(
                tenant_zones_clusters,
                zone_cluster_affected,
                on=["Zone", "Cluster"],
                how="left"
            )

            # Display the affected site count table
            st.subheader(f"Affected Sites for Tenant: {tenant}")
            st.dataframe(tenant_affected[["Zone", "Cluster", "Total Affected Site"]])

    except Exception as e:
        st.error(f"Error processing files: {e}")
        st.exception(e)

# Final Message
if yesterday_file and rms_site_file:
    st.sidebar.success("Both files processed successfully!")
