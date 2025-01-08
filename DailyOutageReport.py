import pandas as pd

# Set the title of the application
st.title("Tenant-Wise Data Processing Application")

# Sidebar for uploading files
st.sidebar.header("Upload Required Excel Files")

# Step 1: Upload MTA Site List
mta_site_file = st.sidebar.file_uploader(
    "1. MTA Site List", type=["xlsx", "xls"]
)

# Step 2: Upload Yesterday Alarm History
alarm_history_file = st.sidebar.file_uploader(
    "2. Yesterday Alarm History", type=["xlsx", "xls"]
)

if mta_site_file and alarm_history_file:
    try:
        # Read the MTA Site List file
        df_mta = pd.read_excel(mta_site_file)

        # Filter the relevant columns from MTA Site List
        columns_to_show_mta = ["Site"]
        df_mta_filtered = df_mta[columns_to_show_mta]

        # Read Yesterday Alarm History file
        df_alarm_history = pd.read_excel(alarm_history_file, skiprows=2)

        # Filter the relevant columns from Yesterday Alarm History
        columns_to_show_alarm = ["Site Alias", "Cluster", "Zone", "Elapsed Time"]
        df_alarm_history_filtered = df_alarm_history[columns_to_show_alarm]

        # Tag each site in Yesterday Alarm History as "MTA" or "Not MTA"
        def tag_mta(site):
            # If the Site in Alarm History exists in the MTA Site List, tag as MTA, otherwise Not MTA
            if site in df_mta_filtered["Site"].values:
                return "MTA"
            return "Not MTA"

        # Apply the tag function to the 'Site Alias' column in Alarm History data
        df_alarm_history_filtered["MTA/Not MTA"] = df_alarm_history_filtered["Site Alias"].apply(tag_mta)

        # Display the matched data table
        st.subheader("Matched Data from Yesterday Alarm History with MTA/Not MTA Tag")
        st.dataframe(df_alarm_history_filtered)

    except Exception as e:
        st.error(f"Error processing files: {e}")
else:
    st.warning("Please upload both MTA Site List and Yesterday Alarm History files.")
