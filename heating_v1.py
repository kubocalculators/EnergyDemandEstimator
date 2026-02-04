"""

This script contains all technical functions needed for the heating calculations for the energy consumption calculator

"""

import pandas as pd
import numpy as np

def build_hourly_heating_df_TWO_OPTIONS(
    df_weather: pd.DataFrame,
    scr1_eff: float,
    scr2_eff: float,
    heating_target: str = "T_set_C",
    cladd: float = 1.2,
    u_leak: float = 0.7,
    u_roof: float = 6.9
) -> pd.DataFrame:
    
    scr1_eff = scr1_eff/100
    scr2_eff = scr2_eff/100

    rows = []

    for _, r in df_weather.iterrows():
        # Extract values from weather data needed for the calculation
        t_out = r["Temperature (C)"]
        is_day = r["is_day"]
        if np.isnan(t_out):
            continue

        # Set the target temperature based on the user selection: setpoint or minimum temperature
        if heating_target == "T_set_C":
            t_target = r["T_set_C"]
        else:
            t_target = r["T_min_C"]
        if np.isnan(t_target):
            continue
            
        # Calculate the watts of heating needed, only use the blackout screen for energy savings at nighttime
        needs_heating = t_out < t_target

        if not needs_heating:
            Q = 0
        else:
            if is_day:
                u_scr = u_roof * (1 - scr1_eff)
            else:
                u_scr1 = u_roof * (1 - scr1_eff)
                u_scr = u_scr1 * (1 - scr2_eff)

            Q = (u_scr * cladd + u_leak) * (t_target - t_out)

        rows.append({
            "timestamp": r["timestamp"],
            "T_out_C": t_out,
            "T_target": t_target,
            "U_scr": u_scr,
            "Q_heat_W_m2": Q
        })

    return pd.DataFrame(rows)


def HST_volume(
    hours_backup: float,
    demand_MW: float,
    Cp_water_kjkgK: float = 4.18,
    Density_kgm3: float = 999.65,
    dT_C: float = 6    
) -> float:
    
    required_capacity_MJ = demand_MW * hours_backup * 3600
    HST_volume_m3 = required_capacity_MJ / Cp_water_kjkgK / Density_kgm3 / dT_C * 1000

    return HST_volume_m3

def heating_load_percentile_summary(
    df_output: pd.DataFrame,
    area_m2: float,
    AHU_count: float,
    load_col: str = "Q_heat_W_m2",
    percentiles=(98, 95, 92.5, 90, 85),
    label: str = "Heating Design Summary"
):

    # Checks if the load_col exists in the DataFrame
    if load_col not in df_output.columns:
        raise KeyError(f"'{load_col}' not found in df_output columns: {list(df_output.columns)}")

    # Extracts all values as a numpy array of floats, dropping all missing values
    vals = df_output[load_col].dropna().to_numpy(dtype=float)
    if vals.size == 0:
        return {}, f"--- {label} ---\nNo valid values found in '{load_col}'."

    results_dict = {}

    # For each percentile (85, 90, 92.5, 95 and 98) compute the heating requirement in W/m2, then convert to kW
    for p in percentiles:
        # Percentile of W/m²
        w_m2 = float(np.percentile(vals, p))

        # kW (W/m² * area / 1000)
        per_AHU_heating_kw = (w_m2 * area_m2) / 1000.0

        total_heating_mw = per_AHU_heating_kw * AHU_count / 1000

        results_dict[p] = {
            "W_m2": w_m2,
            "Total Heating (MW)": total_heating_mw
        }

    heating_results_df = pd.DataFrame.from_dict(results_dict, orient="index")

    return heating_results_df