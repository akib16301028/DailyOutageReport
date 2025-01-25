import streamlit as st
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

# Helper function to standardize tenant names
def standardize_tenant(tenant_name):
    tenant_mapping = {
        "BANJO": "Banjo",
        "BL": "Banglalink",
        "GP": "Grameenphone",
        "ROBI": "Robi",
    }
    return tenant_mapping.get(tenant_name, tenant_name)

# Helper function to convert elapsed time to decimal hours
def convert_to_decimal_hours(elapsed_time):
    if pd.notnull(elapsed_time):
        total_seconds = elapsed_time.total_seconds()
        decimal_hours = total_seconds / 3600
        return Decimal(decimal_hours).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
    return Decimal(0.0)

# Step 1: Load MTA Site List from the repository (automatically)
mta_site_list_file = "MTA Site List.xlsx"  # Assuming the file is in the repository
df_mta_site_list = pd.read_excel(mta_site_list_file, skiprows=0)

# Group by Cluster and Zone
mta_grouped = df_mta_site_list.groupby(["Cluster", "Zone"])

# Total Site Count: Count of Site Alias for corresponding zones
total_site_count = mta_grouped.size().reset_index(name="Total Site Count")

# Step 2: Load Yesterday Alarm History file (from repository or automatically)
alarm_history_file = "Yesterday Alarm History.xlsx"  # Assuming the file is in the repository
df_alarm_history = pd.read_excel(alarm_history_file, skiprows=2)

# Filter rows where Site Alias matches those in MTA Site List
matched_alarm_data = df_alarm_history[df_alarm_history["Site Alias"].isin(df_mta_site_list["Site Alias"])]

# Total Affected Site: Count of matching Site Alias per Cluster and Zone
affected_site_count = matched_alarm_data.groupby(["Cluster", "Zone"]).size().reset_index(name="Total Affected Site")

# Calculate Elapsed Time (Decimal) for the matched Site Alias
matched_alarm_data["Elapsed Time"] = pd.to_timedelta(matched_alarm_data["Elapsed Time"], errors="coerce")
elapsed_time_sum = matched_alarm_data.groupby(["Cluster", "Zone"])["Elapsed Time"].sum().reset_index()
elapsed_time_sum["Elapsed Time (Decimal)"] = elapsed_time_sum["Elapsed Time"].apply(convert_to_decimal_hours)

# Step 3: Load Grid Data (from repository or automatically)
grid_data_file = "Grid Data.xlsx"  # Assuming the file is in the repository
df_grid_data = pd.read_excel(grid_data_file, sheet_name="Site Wise Summary", skiprows=2)

# Filter rows where Site Alias matches those in MTA Site List
matched_grid_data = df_grid_data[df_grid_data["Site"].isin(df_mta_site_list["Site Alias"])]

# Grid Availability: Average of AC Availability (%) per Cluster and Zone
grid_availability = matched_grid_data.groupby(["Cluster", "Zone"])["AC Availability (%)"].mean().reset_index()
grid_availability.rename(columns={"AC Availability (%)": "Grid Availability"}, inplace=True)

# Step 4: Load Total Elapse Till Date file (from repository or automatically)
total_elapse_file = "Total Elapse Till Date.xlsx"  # Assuming the file is in the repository
df_total_elapse = pd.read_excel(total_elapse_file, skiprows=0)

# Filter rows where Site Alias matches those in MTA Site List
matched_total_elapsed = df_total_elapse[df_total_elapse["Site"].isin(df_mta_site_list["Site Alias"])]

# Total Reedemed Hour: Sum of Elapsed Time for the matching Site Alias
matched_total_elapsed["Elapsed Time"] = pd.to_timedelta(matched_total_elapsed["Elapsed Time"], errors="coerce")
total_redeemed = matched_total_elapsed.groupby(["Cluster", "Zone"])["Elapsed Time"].sum().reset_index()
total_redeemed["Total Reedemed Hour"] = total_redeemed["Elapsed Time"].apply(convert_to_decimal_hours)

# Step 5: Merge all data into a final table for MTA Sites
mta_final = total_site_count
mta_final = pd.merge(mta_final, affected_site_count, on=["Cluster", "Zone"], how="left")
mta_final = pd.merge(mta_final, elapsed_time_sum[["Cluster", "Zone", "Elapsed Time (Decimal)"]], on=["Cluster", "Zone"], how="left")
mta_final = pd.merge(mta_final, grid_availability, on=["Cluster", "Zone"], how="left")
mta_final = pd.merge(mta_final, total_redeemed[["Cluster", "Zone", "Total Reedemed Hour"]], on=["Cluster", "Zone"], how="left")

# Fill missing values
mta_final["Total Site Count"] = mta_final["Total Site Count"].fillna(0).astype(int)
mta_final["Total Affected Site"] = mta_final["Total Affected Site"].fillna(0).astype(int)
mta_final["Elapsed Time (Decimal)"] = mta_final["Elapsed Time (Decimal)"].fillna(Decimal(0.0))
mta_final["Total Reedemed Hour"] = mta_final["Total Reedemed Hour"].fillna(Decimal(0.0))

# Total Allowable Limit (Hr) calculation
mta_final["Total Allowable Limit (Hr)"] = mta_final["Total Site Count"] * 24 * 30 * (1 - 0.9985)
mta_final["Remaining Hour"] = mta_final["Total Allowable Limit (Hr)"] - mta_final["Total Reedemed Hour"]

# Step 6: Display MTA Site Final Table
st.subheader("MTA Site Final Table")
st.dataframe(
    mta_final[
        [
            "Cluster",
            "Zone",
            "Total Site Count",
            "Total Affected Site",
            "Elapsed Time (Decimal)",
            "Grid Availability",
            "Total Reedemed Hour",
            "Total Allowable Limit (Hr)",
            "Remaining Hour",
        ]
    ]
)
