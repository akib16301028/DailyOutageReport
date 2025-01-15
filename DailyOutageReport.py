import streamlit as st
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

# Function to standardize tenant names
def standardize_tenant(tenant_name):
    tenant_mapping = {
        "BANJO": "Banjo",
        "BL": "Banglalink",
        "GP": "Grameenphone",
        "ROBI": "Robi",
    }
    return tenant_mapping.get(tenant_name, tenant_name)

# Function to convert elapsed time to decimal hours
def convert_to_decimal_hours(elapsed_time):
    if pd.notnull(elapsed_time):
        total_seconds = elapsed_time.total_seconds()
        decimal_hours = total_seconds / 3600
        return Decimal(decimal_hours).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
    return Decimal(0.0)

# Your existing code that processes files...

# Merge Overall and Tenant-Specific Data
if rms_site_file and alarm_history_file and grid_data_file and total_elapse_file:
    try:
        for tenant, tenant_merged in tenant_merged_data.items():
            grid_data = tenant_zone_grid.get(tenant, pd.DataFrame())

            # Merge tenant-specific data with Grid Data
            merged_tenant_final = pd.merge(
                tenant_merged,
                grid_data[["Cluster", "Zone", "AC Availability (%)"]],
                on=["Cluster", "Zone"],
                how="left"
            )

            merged_tenant_final["Grid Availability"] = merged_tenant_final["AC Availability (%)"]
            
            # Merge with Total Reedemed Hour for each tenant
            total_elapsed_data = tenant_total_elapsed.get(tenant, pd.DataFrame())
            merged_tenant_final = pd.merge(
                merged_tenant_final,
                total_elapsed_data[["Cluster", "Zone", "Total Reedemed Hour"]],
                on=["Cluster", "Zone"],
                how="left"
            )

            # Step 1: Replace None/NaN with 0 and convert all numeric columns to float
            numeric_columns = ["Total Site Count", "Total Affected Site", "Elapsed Time (Decimal)", "Total Reedemed Hour"]
            merged_tenant_final[numeric_columns] = merged_tenant_final[numeric_columns].fillna(0).astype(float)

            # Step 2: Calculate Total Allowable Limit (Hr)
            merged_tenant_final["Total Allowable Limit (Hr)"] = (
                merged_tenant_final["Total Site Count"] * 24 * 30 * (1 - 0.9985)
            ).astype(float)  # Ensure it's a float

            # Step 3: Calculate Remaining Hour
            merged_tenant_final["Remaining Hour"] = (
                merged_tenant_final["Total Allowable Limit (Hr)"] - merged_tenant_final["Total Reedemed Hour"]
            ).astype(float)  # Ensure it's a float

            # Display the tenant-specific table with the new column
            st.subheader(f"Tenant: {tenant} - Final Merged Table")
            st.dataframe(
                merged_tenant_final[
                    [
                        "Cluster",
                        "Zone",
                        "Total Site Count",
                        "Total Affected Site",
                        "Elapsed Time (Decimal)",
                        "Grid Availability",
                        "Total Reedemed Hour",
                        "Total Allowable Limit (Hr)",
                        "Remaining Hour"
                    ]
                ]
            )

        # Combine all tenants for the overall table
        combined_grid_data = df_grid_data.groupby(["Cluster", "Zone"]).agg({
            "AC Availability (%)": "mean",
        }).reset_index()

        overall_final_merged = pd.merge(
            merged_all_tenants.groupby(["Cluster", "Zone"]).sum().reset_index(),
            combined_grid_data,
            on=["Cluster", "Zone"],
            how="left"
        )

        overall_final_merged["Grid Availability"] = overall_final_merged["AC Availability (%)"]

        # Merge with Total Reedemed Hour for overall data
        overall_elapsed = (
            df_total_elapse.groupby(["Cluster", "Zone"])["Elapsed Time"]
            .sum()
            .reset_index()
        )
        overall_elapsed["Total Reedemed Hour"] = overall_elapsed["Elapsed Time"].apply(convert_to_decimal_hours)

        overall_final_merged = pd.merge(
            overall_final_merged,
            overall_elapsed[["Cluster", "Zone", "Total Reedemed Hour"]],
            on=["Cluster", "Zone"],
            how="left"
        )

        # Calculate Total Allowable Limit (Hr) for overall data
        overall_final_merged["Total Allowable Limit (Hr)"] = (
            overall_final_merged["Total Site Count"] * 24 * 30 * (1 - 0.9985)
        ).astype(float)  # Ensure it's a float

        # Calculate Remaining Hour for overall data
        overall_final_merged["Remaining Hour"] = (
            overall_final_merged["Total Allowable Limit (Hr)"] - overall_final_merged["Total Reedemed Hour"]
        ).astype(float)  # Ensure it's a float

        st.subheader("Overall Final Merged Table")
        st.dataframe(
            overall_final_merged[
                [
                    "Cluster",
                    "Zone",
                    "Total Site Count",
                    "Total Affected Site",
                    "Elapsed Time (Decimal)",
                    "Grid Availability",
                    "Total Reedemed Hour",
                    "Total Allowable Limit (Hr)",
                    "Remaining Hour"
                ]
            ]
        )

    except Exception as e:
        st.error(f"Error merging data: {e}")
