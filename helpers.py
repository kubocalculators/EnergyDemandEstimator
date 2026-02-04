"""

This script contains all helper functions needed for web app user interface
(ie. submit buttons, forms, etc.)

"""

import pandas as pd
import numpy as np
import openpyxl

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
    