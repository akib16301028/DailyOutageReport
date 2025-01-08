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

        # Check if necessary columns exist
        required_columns = ["Site", "Site Alias", "Zone", "Cluster"]
        if all(col in df_rms_site.columns for col in required_columns):
            # Filter out sites starting with 'L'
            df_rms_filtered = df_rms_site[~df_rms_site["Site"].str.startswith("L", na=False)]
            
            # Extract tenant from Site Alias
            def extract_tenant(site_alias):
                if isinstance(site_alias, str) and "(" in site_alias and ")" in site_alias:
                    return site_alias.split("(")[1].split(")")[0].strip()
                return "Unknown"
            
            # Add Tenant column
            df_rms_filtered["Tenant"] = df_rms_filtered["Site Alias"].apply(extract_tenant)

            # Display the RMS Site List table for debugging
            debug_columns = ["Site", "Site Alias", "Zone", "Cluster", "Tenant"]
            st.subheader("Filtered RMS Site List with Extracted Tenant")
            st.dataframe(df_rms_filtered[debug_columns])

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
                
                # Append Total Site Count column
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
        else:
            missing_columns = [col for col in required_columns if col not in df_rms_site.columns]
            st.error(f"Required columns missing: {', '.join(missing_columns)}")
    
    except Exception as e:
        st.error(f"Error processing RMS Site List: {e}")

# Final Message
if yesterday_file and rms_site_file:
    st.sidebar.success("All files have been uploaded and processed successfully!")
