
import numpy as np
import pandas as pd

from psychrolib import (
    SetUnitSystem, SI,
    GetHumRatioFromRelHum,
    GetMoistAirEnthalpy,
    GetTWetBulbFromRelHum,
    GetMoistAirDensity,
    GetRelHumFromHumRatio,
    GetTDryBulbFromEnthalpyAndHumRatio
)

SetUnitSystem(SI)

"""

This script contains all technical functions needed for the active cooling calculations for the energy consumption calculator

"""

eta = 0.8


def m3h_to_mdot_dryair_kg_s(vdot_m3_h: float, t_c: float, rh_percent: float) -> float:
    p = 101325
    if vdot_m3_h <= 0:
        return 0.0
    rh_frac = rh_percent / 100.0
    W = GetHumRatioFromRelHum(t_c, rh_frac, p)
    rho_moist = GetMoistAirDensity(t_c, W, p)
    vdot_m3_s = vdot_m3_h / 3600.0
    m_dot_moist = rho_moist * vdot_m3_s
    return m_dot_moist / (1.0 + W)


def padwall_limited_by_rh_cap(
    t_in: float,
    rh_in_percent: float,
    rh_cap_percent: float,
    t_ref_for_cap: float
):
    """
    Padwall at maximum possible eta_used but limited by RH cap expressed as a W_cap
    computed at a reference temperature t_ref_for_cap.

    This makes the cap behavior closer to "RH after treatment should not exceed RH_cap"
    around the control temperature (setpoint or Tmax).
    """
    p = 101325
    
    rh_in = rh_in_percent / 100.0
    W_in = GetHumRatioFromRelHum(t_in, rh_in, p)
    h_in = GetMoistAirEnthalpy(t_in, W_in)

    t_wb = GetTWetBulbFromRelHum(t_in, rh_in, p)
    W_sat_wb = GetHumRatioFromRelHum(t_wb, 1.0, p)
    h_sat_wb = GetMoistAirEnthalpy(t_wb, W_sat_wb)

    rh_cap = rh_cap_percent / 100.0
    W_cap = GetHumRatioFromRelHum(t_ref_for_cap, rh_cap, p)

    denom_W = (W_sat_wb - W_in)
    if denom_W <= 1e-12:
        eta_used = 0.0
    else:
        eta_limit = (W_cap - W_in) / denom_W
        eta_used = float(np.clip(min(eta, eta_limit), 0.0, eta))

    W_pw = W_in + eta_used * (W_sat_wb - W_in)
    h_pw = h_in + eta_used * (h_sat_wb - h_in)

    T_pw = GetTDryBulbFromEnthalpyAndHumRatio(h_pw, W_pw)
    RH_pw_pct = GetRelHumFromHumRatio(T_pw, W_pw, p) * 100.0

    return {
        "eta_used": eta_used,
        "W_out_kgw_kgDA": W_in,
        "h_out_J_kgDA": h_in,
        "W_pw_kgw_kgDA": W_pw,
        "h_pw_J_kgDA": h_pw,
        "T_pw_C": T_pw,
        "RH_pw_pct": RH_pw_pct,
        "W_cap_kgw_kgDA": W_cap
    }


def build_hourly_padwall_activecool_df_TWO_OPTIONS(
    df_weather: pd.DataFrame,
    # airflow / area
    airflow_m3_h: float = 18000.0,
    area_m2: float = 200.0
) -> pd.DataFrame:

    p = 101325.0    # Atmospheric Pressure (Pa)
    rows = []

    for _, r in df_weather.iterrows():
        t_out = r["Temperature (C)"]
        rh_out = r["Relative Humidity (%)"]
        t_set = r["T_set_C"]
        rh_set = r["RH_set_pct"]
        rh_cap = r["RH_cap_pct"]
        t_max = r["T_max_C"]

        if np.isnan(t_out) or np.isnan(rh_out) or np.isnan(t_set) or np.isnan(rh_set) or np.isnan(rh_cap) or np.isnan(t_max):
            continue

        # outdoor
        W_out = GetHumRatioFromRelHum(t_out, rh_out/100.0, p)
        h_out = GetMoistAirEnthalpy(t_out, W_out)

        # run padwall when temperature exceeds Tmax (more realistic) OR exceeds setpoint (stricter)
        needs_cooling = (t_out > t_max)

        if not needs_cooling:
            eta_used = 0.0
            W_pw = W_out
            h_pw = h_out
            T_pw = t_out
            RH_pw = rh_out
        else:
            # Use cap referenced at Tmax (recommended for Option 2 behavior)
            st = padwall_limited_by_rh_cap(t_out, rh_out, rh_cap, t_ref_for_cap=t_max)
            eta_used = st["eta_used"]
            W_pw = st["W_pw_kgw_kgDA"]
            h_pw = st["h_pw_J_kgDA"]
            T_pw = st["T_pw_C"]
            RH_pw = st["RH_pw_pct"]

        # -------------------------
        # Option 1: strict setpoint (your current)
        # -------------------------
        W_set = GetHumRatioFromRelHum(t_set, rh_set/100.0, p)
        h_set = GetMoistAirEnthalpy(t_set, W_set)
        active1_J_kg = max(0.0, h_pw - h_set)

        # -------------------------
        # Option 2: Tmax-only (cool to Tmax at current moisture)
        # -------------------------
        h_tmax_sameW = GetMoistAirEnthalpy(t_max, W_pw)
        active2_J_kg = max(0.0, h_pw - h_tmax_sameW)

        mdot_da = m3h_to_mdot_dryair_kg_s(airflow_m3_h, t_out, rh_out)

        Q1 = (mdot_da * active1_J_kg) / area_m2
        Q2 = (mdot_da * active2_J_kg) / area_m2

        rows.append({
            "timestamp": r["timestamp"],
            "T_out_C": t_out,
            "RH_out_pct": rh_out,
            "Solar_W_m2": r["Solar Radiation (W/m²)"],
            "T_set_C": t_set,
            "RH_set_pct": rh_set,
            "T_max_C": t_max,
            "RH_cap_pct": rh_cap,
            "eta_used": eta_used,
            "T_pw_C": T_pw,
            "RH_pw_pct": RH_pw,
            "h_out_J_kgDA": h_out,
            "h_pw_J_kgDA": h_pw,
            "h_set_J_kgDA": h_set,
            "h_tmax_sameW_J_kgDA": h_tmax_sameW,
            "active_J_kg_strict_setpoint": active1_J_kg,
            "active_J_kg_Tmax": active2_J_kg,
            "m_dot_dryair_kg_s": mdot_da,
            "Q_active_W_m2_strict_setpoint": Q1,
            "Q_active_W_m2_Tmax": Q2,
            "airflow_m3_h": airflow_m3_h,
            "area_m2": area_m2,
            "vent_intensity_m3h_m2": airflow_m3_h/area_m2
        })

    return pd.DataFrame(rows)


def cooling_load_percentile_summary(
    df_output: pd.DataFrame,
    area_m2: float,
    AHU_count: float,
    load_col: str = "Q_active_W_m2",
    percentiles=(98, 95, 92.5, 90, 85),
    label: str = "Cooling Design Summary"
):

    # Checks if the load_col exists in the DataFrame
    if load_col not in df_output.columns:
        raise KeyError(f"'{load_col}' not found in df_output columns: {list(df_output.columns)}")

    # Extracts all values as a numpy array of floats, dropping all missing values
    vals = df_output[load_col].dropna().to_numpy(dtype=float)
    if vals.size == 0:
        return {}, f"--- {label} ---\nNo valid values found in '{load_col}'."

    results_dict = {}

    # For each percentile (85, 90, 92.5, 95 and 98) compute the cooling requirement in W/m2, then convert to kW
    for p in percentiles:
        # Percentile of W/m²
        w_m2 = float(np.percentile(vals, p))

        # enthalpy kW (W/m² * area / 1000)
        cooling_kw = (w_m2 * area_m2) / 1000.0

        total_cooling_mw = cooling_kw * AHU_count / 1000

        results_dict[p] = {
            "W_m2": w_m2,
            "Cooling per AHU (kW)": cooling_kw,
            "Total Cooling (MW)": total_cooling_mw
        }

    cooling_results_df = pd.DataFrame.from_dict(results_dict, orient="index")

    return cooling_results_df

