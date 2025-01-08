import streamlit as st
import pandas as pd

# Set the title of the application
st.title("RMS Site List Debugging")

# Sidebar for uploading RMS Site List file
st.sidebar.header("Upload RMS Site List File")

# Step 1: Upload RMS Site List
rms_site_file = st.sidebar.file_uploader(
    "Upload RMS Site List", type=["xlsx", "xls"]
)

if rms_site_file:
    st.success("RMS Site List uploaded successfully!")
    
    try:
        # Read RMS Site List starting from row 3
        df_rms_site = pd.read_excel(rms_site_file, skiprows=2)
        
        # Check if necessary columns exist
        required_columns = ["Site", "Site Alias", "Zone", "Cluster"]
        if all(col in df_rms_site.columns for col in required_columns):
            # Extract tenant from Site Alias
            def extract_tenant(site_alias):
                if isinstance(site_alias, str) and "(" in site_alias and ")" in site_alias:
                    return site_alias.split("(")[-1].replace(")", "").strip()
                return "Unknown"
            
            # Add Tenant column
            df_rms_site["Tenant"] = df_rms_site["Site Alias"].apply(extract_tenant)
            
            # Display the table with selected columns
            debug_columns = ["Site", "Site Alias", "Zone", "Cluster", "Tenant"]
            debug_table = df_rms_site[debug_columns]
            st.subheader("All Site List with Extracted Tenant")
            st.dataframe(debug_table)
        else:
            missing_columns = [col for col in required_columns if col not in df_rms_site.columns]
            st.error(f"Required columns missing: {', '.join(missing_columns)}")
    
    except Exception as e:
        st.error(f"Error processing RMS Site List: {e}")
else:
    st.info("Please upload the RMS Site List file to debug.")
