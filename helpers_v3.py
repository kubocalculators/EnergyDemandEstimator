"""

This script contains all helper functions needed for web app user interface
(ie. submit buttons, forms, etc.) 

Updates from v2:
- updated call_crop_temp_and_rh_setRanges function for new crop data, pull optimal temperatures when available

"""

import pandas as pd
import numpy as np
from io import BytesIO


def prepare_weather_df(
    upload,
    t_day: float,
    t_night: float,
    rh_day: float,
    rh_night: float,
    rh_cap_day: float,
    rh_cap_night: float,
    tmax_day: float,
    tmax_night: float,
    tmin_day: float,
    tmin_night: float
):
    
    # Convert to DataFrame
    if upload is not None:
        df = pd.read_excel(upload)

    # Clean DataFrame
    #     Alert if there are any missing columns
    required = ["Local Time", "Temperature (C)", "Relative Humidity (%)", "Solar Radiation (W/m²)"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    #     Add column for formatted Date/Time
    df["timestamp"] = pd.to_datetime(df["Local Time"])
    #     Convert these columns to integer data type
    for col in ["Temperature (C)", "Relative Humidity (%)", "Solar Radiation (W/m²)"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    #     Add a column indicating if it is day or night based on solar radiation
    df["is_day"] = np.where(df["Solar Radiation (W/m²)"] > 0, 1, 0)

    df["T_set_C"] = np.where(df["is_day"] == 1, t_day, t_night)
    df["RH_set_pct"] = np.where(df["is_day"] == 1, rh_day, rh_night)
    df["RH_cap_pct"] = np.where(df["is_day"] == 1, rh_cap_day, rh_cap_night)
    df["T_max_C"] = np.where(df["is_day"] == 1, tmax_day, tmax_night)
    df["T_min_C"] = np.where(df["is_day"] == 1, tmin_day, tmin_night)

    return df
    
def call_cropData(crop_name):
    
    crop_df = pd.read_excel("CropData.xlsx")

    # Raise an error if the file has been changed and therefore cannot be referenced
    required = [
        "Crop",
        "Reference",
        "Variety",
        "Day_Temp_Min (degC)",
        "Day_Temp_Max (degC)",
        "Day_Temp_Optimal (degC)",
        "Night_Temp_Min (degC)",
        "Night_Temp_Max (degC)",
        "Night_Temp_Optimal (degC)",
        "Day_RH_Min (%)",
        "Day_RH_Max (%)",
        "Day_RH_Optimal (%)",
        "Night_RH_Min (%)",
        "Night_RH_Max (%)",
        "Night_RH_Optimal (%)"
        ]
    missing = [c for c in required if c not in crop_df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Select the row matching the crop
    crop_df = crop_df.set_index("Crop")
    row = crop_df.loc[crop_name]

    # Function that returns None if the Excel database is missing that data
    def nan_to_none(x):
        return None if pd.isna(x) else x

    # Retrieve values from that row
    reference = nan_to_none(row["Reference"])
    variety = nan_to_none(row["Variety"])
    day_min_temp = nan_to_none(row["Day_Temp_Min (degC)"])
    day_max_temp = nan_to_none(row["Day_Temp_Max (degC)"])
    day_opt_temp = nan_to_none(row["Day_Temp_Optimal (degC)"])

    night_min_temp = nan_to_none(row["Night_Temp_Min (degC)"])
    night_max_temp = nan_to_none(row["Night_Temp_Max (degC)"])
    night_opt_temp = nan_to_none(row["Night_Temp_Optimal (degC)"])

    day_min_rh = nan_to_none(row["Day_RH_Min (%)"])
    day_max_rh = nan_to_none(row["Day_RH_Max (%)"])
    day_opt_rh = nan_to_none(row["Day_RH_Optimal (%)"])

    night_min_rh = nan_to_none(row["Night_RH_Min (%)"])
    night_max_rh = nan_to_none(row["Night_RH_Max (%)"])
    night_opt_rh = nan_to_none(row["Night_RH_Optimal (%)"])

    # Calculate averages if no optimal is available
    if not day_opt_temp:
        day_temp_values = [v for v in (day_min_temp, day_max_temp) if v is not None]
        day_opt_temp = (sum(day_temp_values) / len(day_temp_values)) if day_temp_values else None    

    if not night_opt_temp:
        night_temp_values = [v for v in (night_min_temp, night_max_temp) if v is not None]
        night_opt_temp = (sum(night_temp_values) / len(night_temp_values)) if night_temp_values else None 
    
    if not day_opt_rh:
        day_rh_values = [v for v in (day_min_rh, day_max_rh) if v is not None]
        day_opt_rh = (sum(day_rh_values) / len(day_rh_values)) if day_rh_values else None 
    
    if not night_opt_rh:
        night_rh_values = [v for v in (night_min_rh, night_max_rh) if v is not None]
        night_opt_rh = (sum(night_rh_values) / len(night_rh_values)) if night_rh_values else None 

    return reference, variety, day_min_temp, day_max_temp, night_min_temp, night_max_temp, day_min_rh, day_max_rh, night_min_rh, night_max_rh, day_opt_temp, night_opt_temp, day_opt_rh, night_opt_rh

def airflowrate_perAHU_m3h(truss_length, trolley, AHU_count_pertruss):                   

    # Calcualte width available for the AHU fan
    trolley_width = 771 if trolley == "Standard (771mm)" else 0
    AHU_max_width = ( truss_length - (AHU_count_pertruss - 1) * trolley_width ) / AHU_count_pertruss

    # Read AHU table
    AHU_df = pd.read_excel("AHU_types_capacities.xlsx")

    # Force datatype to be numeric
    AHU_df["DADH_outside_diameter_mm"] = pd.to_numeric(AHU_df["DADH_outside_diameter_mm"], errors="coerce")
    AHU_df["ventilation_capacity_m3perh"] = pd.to_numeric(AHU_df["ventilation_capacity_m3perh"], errors="coerce")

    # Select the row for the fan with largest possible diameter
    candidates = AHU_df.loc[AHU_df["DADH_outside_diameter_mm"] <= AHU_max_width].dropna(subset=["DADH_outside_diameter_mm"])
    if candidates.empty:
        raise ValueError(
            f" No AHU fit this configuration."
        )
    
    # Call the ventilation capacity from the table
    best_row = candidates.loc[candidates["DADH_outside_diameter_mm"].idxmax()]
    airflow_rate = best_row["ventilation_capacity_m3perh"]
    AHU_type = best_row["AHU_type"]

    return AHU_type, airflow_rate

def output_excel(inputs_dict, heating_df, cooling_df):
    output = BytesIO()

    # Flatten nested dict
    rows = []
    for section, values in inputs_dict.items():
        for key, val in values.items():
            rows.append({
                "Category": section,
                "Parameter": key,
                "Value": val
            })

    inputs_df = pd.DataFrame(rows)

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        inputs_df.to_excel(writer, sheet_name="Inputs", index=False)
        heating_df.to_excel(writer, sheet_name="Heating Results", index=True)
        cooling_df.to_excel(writer, sheet_name="Cooling Results", index=True)

    output.seek(0)          # reset cursor to the beginning of the data
    return output

