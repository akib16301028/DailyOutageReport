import streamlit as st
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

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

        # Filter out sites starting with 'L'
        df_rms_filtered = df_rms_site[~df_rms_site["Site"].str.startswith("L", na=False)]

        # Step 2: Upload MTA Site List
        mta_file_path = "MTA Site List.xlsx"  # Ensure this file is in the same directory as the script
        df_mta = pd.read_excel(mta_file_path)

        # Filter the MTA Site List for the "Site" column
        mta_sites = df_mta["Site"].unique()

        # Step 3: Upload Yesterday Alarm History File
        alarm_history_file = st.sidebar.file_uploader(
            "2. Yesterday Alarm History", type=["xlsx", "xls"]
        )
        if alarm_history_file:
            st.success("Yesterday Alarm History uploaded successfully!")

            try:
                # Read Yesterday Alarm History file, skip first 3 rows
                df_alarm_history = pd.read_excel(alarm_history_file, skiprows=2)

                # Filter out sites starting with 'L' in the Site column of Yesterday Alarm History
                df_alarm_history = df_alarm_history[~df_alarm_history["Site"].str.startswith("L", na=False)]

                # Tag the Site as "MTA" or "Not MTA" based on matching with MTA Site List
                def tag_mta_status(site):
                    return "MTA" if site in mta_sites else "Not MTA"

                # Apply the function to tag the sites
                df_alarm_history["MTA/Not MTA"] = df_alarm_history["Site"].apply(tag_mta_status)

                # Filter to show only rows that match MTA (Optional: Show all rows tagged as "MTA" or "Not MTA")
                tagged_alarm_data = df_alarm_history[["Site Alias", "Cluster", "Zone", "Elapsed Time", "MTA/Not MTA"]]

                # Display the tagged data
                st.subheader("Matched Data from Yesterday Alarm History")
                st.dataframe(tagged_alarm_data)

            except Exception as e:
                st.error(f"Error processing Yesterday Alarm History: {e}")

    except Exception as e:
        st.error(f"Error processing RMS Site List or MTA Site List: {e}")

# Final Message
if rms_site_file and alarm_history_file:
    st.sidebar.success("All files processed successfully!")
