import streamlit as st
import pandas as pd

# Function to extract tenant from Site Alias
def extract_tenant(site_alias):
    if isinstance(site_alias, str) and "(" in site_alias and ")" in site_alias:
        tenant = site_alias.split("(")[1].split(")")[0]
        return tenant.strip()
    return ""

# Load Yesterday DCDB-01 Primary Disconnect History
def load_yesterday_file(file):
    df = pd.read_excel(file, header=2)  # Start reading from row 3 (index 2)
    return df

# Load RMS Site List and extract the tenant names
def load_rms_file(file):
    df_rms = pd.read_excel(file, header=2)  # Start reading from row 3 (index 2)
    df_rms['Tenant'] = df_rms['Site Alias'].apply(extract_tenant)
    return df_rms

# Load the uploaded files
st.title("Data Upload Application")

# Sidebar for uploading files
st.sidebar.header("Upload Required Excel Files")

# Step 1: Upload Yesterday DCDB-01 Primary Disconnect History
yesterday_file = st.sidebar.file_uploader("1. Yesterday DCDB-01 Primary Disconnect History", type=["xlsx", "xls"])
if yesterday_file:
    st.success("Yesterday's disconnect history uploaded successfully!")
    df_yesterday = load_yesterday_file(yesterday_file)
    st.subheader("Yesterday DCDB-01 Primary Disconnect History")
    st.dataframe(df_yesterday)

# Step 2: Upload RMS Site List
rms_site_file = st.sidebar.file_uploader("2. RMS Site List", type=["xlsx", "xls"])
if rms_site_file:
    st.success("RMS site list uploaded successfully!")
    df_rms_site = load_rms_file(rms_site_file)
    st.subheader("RMS Site List with Tenant")
    st.dataframe(df_rms_site)

# Filtering function for the Zone and Tenant grouping
def generate_tenant_wise_table(df_yesterday, df_rms_site):
    # Group by Tenant and Zone from RMS Site List
    tenant_zone_groups = df_rms_site.groupby(['Tenant', 'Zone', 'Cluster']).size().reset_index(name='Total Site Count')

    # Group by Tenant and Zone in Yesterday's DCDB History
    df_yesterday_grouped = df_yesterday.groupby(['Tenant', 'Zone']).size().reset_index(name='Total Affected Site')

    # Merge RMS Site Count with Yesterday Site Counts
    result_df = pd.merge(tenant_zone_groups, df_yesterday_grouped, on=['Tenant', 'Zone'], how='left')

    # Fix empty counts to 0
    result_df['Total Affected Site'] = result_df['Total Affected Site'].fillna(0)

    # Remove Tenant column for the final table
    result_df = result_df[['Cluster', 'Zone', 'Total Site Count', 'Total Affected Site']]

    return result_df

# Display tenant-wise table with zone and cluster
if yesterday_file and rms_site_file:
    tenant_wise_table = generate_tenant_wise_table(df_yesterday, df_rms_site)
    st.subheader("Tenant-wise Zone and Site Count")
    st.dataframe(tenant_wise_table)

