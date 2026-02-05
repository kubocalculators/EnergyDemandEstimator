"""

This script runs the web app user interface

"""

import streamlit as st
import pandas as pd
import helpers
import active_cooling_v2
import heating_v1
import info_page

eta = 0.8   # This is the maximum allowable padwall efficiency

st.sidebar.title("Navigation")

page = st.sidebar.radio("Go to:", ["Calculator","Info"], index=0)

if page == "Calculator":
# ---------- STEP 1: Import climate data as Excel file ---------- #
    st.title("Energy Consumption Estimator")
    st.header("Input Climate and Crop Information")

    with st.form("inputData", clear_on_submit=False):
        
        # Upload and clean climate data
        st.subheader("Upload Climate Data")
        st.markdown(
            "**Make sure column titles match:**  \n"
            "Local Time, Temperature (C), Relative Humidity (%), Solar Radiation (W/m²)")
        weather_upload = st.file_uploader("Upload weather Excel from ksgclimatedata.streamlit.app", type=["xlsx"])
        
        # Take in crop parameters
        st.subheader("Crop Climate Parameters")
        t_day = st.number_input("Day Temperature Setpoint (C)", step=1)
        t_night = st.number_input("Night Temperature Setpoint (C)", step=1)
        rh_day = st.number_input("Day RH Setpoint (%)", 0, 100, step=1)
        rh_night = st.number_input("Night RH Setpoint (%)", 0, 100, step=1)
        rh_cap_day = st.number_input("Day Max RH (%)", 0, 100, step=1)
        rh_cap_night = st.number_input("Night Max RH (%)", 0, 100, step=1)
        tmax_day = st.number_input("Day Max Temperature (C)", step=1)
        tmax_night = st.number_input("Night Max Temperature (C)", step=1)
        tmin_day = st.number_input("Day Min Temperature (C)", step=1)
        tmin_night = st.number_input("Night Min Temperature (C)", step=1)

        st.subheader("Greenhouse Parameters")
        st.markdown("The airflow rate is per AHU.")
        airflow_m3_h = st.number_input("Air Flow Rate (m3/h)", None, None, 18000) # default = 18,000 m3/h
        st. markdown("The total number of AHUs is equal to the number of AHUs per truss x the number of trusses")
        AHU_count = st.number_input("Total Number of AHUs", step=1)
        st.markdown("The area per AHU is the truss width divided by the number of AHUs per truss and multiplied by the length of the air hose")
        area_m2 = st.number_input("Area (m2) per AHU", None, None, 200) # default = 200 m2 per AHU
        cladd = st.number_input("Cladd Ratio", None, None, 1.2)
        u_leak = st.number_input("U_leak (W/m2/K)", None, None, 0.7)
        u_roof = st.number_input("U_roof (W/m2/K)", None, None, 6.9)
        scr1_eff = st.number_input("Screen 1 Energy Efficiency (%)", 0, 100, 47, step=1)
        scr2_eff = st.number_input("Screen 2 Energy Efficiency (%)", 0, 100, 50, step=1)

        st.subheader("Select Calculation Methods")
        cooling_method = st.selectbox("Active Cooling Load Method", ["True Temperature and RH Setpoints","Maximum Allowed Temperature and Unlimited RH"])
        heating_method = st.selectbox("Heating Load Method", ["True Setpoint","Minimum Allowed Temperature"])
        hours_of_heat_storage = st.number_input("Hours of Heat Storage", step=1)
        peak_percentile = st.selectbox("Peak Demand Percentile", [98, 95, 92.5, 90, 85])

        run = st.form_submit_button("Calculate")



# ---------- STEP 2: Run energy calculations ---------- #
    if run:

    # Clean data and append crop parameters to the weather DataFrame
        weather_df = helpers.prepare_weather_df(
            weather_upload,
            t_day,
            t_night,
            rh_day, 
            rh_night,
            rh_cap_day,
            rh_cap_night,
            tmax_day,
            tmax_night,
            tmin_day,
            tmin_night
        )
        st.success("Weather data successfully processed")

    # Run heating load calculation

        if heating_method == "True Setpoint":
            heating_target = "T_set_C"
        else:
            heating_target = "T_min_C"

        heating_df = heating_v1.build_hourly_heating_df_TWO_OPTIONS(weather_df, scr1_eff, scr2_eff, heating_target)
        
        heating_results = heating_v1.heating_load_percentile_summary(heating_df, area_m2, AHU_count)
        
        st.success("Heating model completed.")



    # Run active cooling load calculation
        cooling_df = active_cooling_v2.build_hourly_padwall_activecool_df_TWO_OPTIONS(weather_df, airflow_m3_h, area_m2)

        if cooling_method == "True Temperature and RH Setpoints":
            load_col = "Q_active_W_m2_strict_setpoint"
        else:
            load_col = "Q_active_W_m2_Tmax"

        cooling_results = active_cooling_v2.cooling_load_percentile_summary(cooling_df, area_m2, AHU_count, load_col)
        st.success("Active cooling model completed.")



# ---------- STEP 3: Format the outputs of each calculation ---------- #
        st.subheader("Heating Load Percentile Summary")
        st. dataframe(heating_results)

        demand_MW = heating_results.loc[peak_percentile, "Total Heating (MW)"]
        HST_volume_m3 = heating_v1.HST_volume(hours_of_heat_storage,demand_MW)
        st.markdown(
            f"**Recommended HST volume:** {HST_volume_m3:,.0f} m³ to store {hours_of_heat_storage} hours of heat."
        )


        st.subheader("Cooling Load Percentile Summary")
        st.dataframe(cooling_results)

elif page == "Info":
    info_page.render()

