"""

This script runs the web app user interface

"""

import streamlit as st
import pandas as pd
from helpers_v2 import prepare_weather_df, call_crop_temp_and_rh_setRanges, airflowrate_perAHU_m3h
import active_cooling_v2
import heating_v1
import info_page_v2

eta = 0.8   # This is the maximum allowable padwall efficiency
crop_list = [
    "TOMATO ON THE VINE, large",
    "CHERRY TOMATO",
    "BEEF TOMATO",
    "CUCUMBER - LONG ENGLISH, high wire",
    "CUCUMBER - LONG ENGLISH, traditional",
    "CUCUMBER - SNACK/MINI, high wire",
    "CUCUMBER - SNACK/MINI, traditional",
    "STRAWBERRY",
    "LETTUCE, baby leaf",
    "LETTUCE, teen leaf (direct seeding)",
    "LETTUCE, teen leaf (transplanted)",
    "LETTUCE, whole head (medium)",
    "LETTUCE, whole head (large)",
    "SWEET POINT PEPPER",
    "BELL PEPPER"
]

st.sidebar.title("Navigation")

page = st.sidebar.radio("Go to:", ["Calculator","Info"], index=0)

with st.sidebar:
    with open("Productsheets.pdf", "rb") as f:
        st.download_button(
            "Open Crop Data PDF",
            f,
            file_name="Productsheets.pdf",
            mime="application/pdf"
        )

if page == "Calculator":
# ---------- STEP 1: Import climate data as Excel file ---------- #
    st.title("Energy Consumption Estimator")
    st.markdown(":red[**Red fields require attention.**]")

    # Upload and clean climate data
    st.header("Upload Climate Data")
    st.markdown(
        "**Make sure column titles match:**  \n"
        "Local Time, Temperature (C), Relative Humidity (%), Solar Radiation (W/m²)")
    weather_upload = st.file_uploader("Upload weather Excel from ksgclimatedata.streamlit.app", type=["xlsx"])

    # Upload crop data
    st.header("Upload Crop Data")
    crop_name = st.selectbox(":red[**Select Crop**]", crop_list)
    reference, variety, day_min_temp, day_max_temp, night_min_temp, night_max_temp, day_min_rh, day_max_rh, night_min_rh, night_max_rh, day_avg_temp, night_avg_temp, day_avg_rh, night_avg_rh = call_crop_temp_and_rh_setRanges(crop_name)

    st.markdown("*Temperature and RH ranges will populate with crop selection.*")
    # Display the default values, they can be overwritten
    col1, col2 = st.columns(2)
    with col1:
        tmin_day = st.number_input("Day Min Temperature (C)", value=day_min_temp)
        tmin_night = st.number_input("Night Min Temperature (C)", value=night_min_temp)
        rh_cap_day = st.number_input("Day MAX RH (%)", value=day_max_rh)
    with col2:
        tmax_day = st.number_input("Day Max Temperature (C)", value=day_max_temp)
        tmax_night = st.number_input("Night Max Temperature (C)", value=night_max_temp)
        rh_cap_night = st.number_input("Night MAX RH (%)", value=night_max_rh)
    
    
    st.header("Input Project Specifics")
    with st.form("inputData", clear_on_submit=False):
        
        st.subheader("Climate Setpoints")
        # Take in crop parameters
        st.markdown("*Default values are average between min/max ranges.*")
        t_day = st.number_input("Day Temperature Setpoint (C)", value=day_avg_temp)
        t_night = st.number_input("Night Temperature Setpoint (C)", value=night_avg_temp)
        rh_day = st.number_input("Day RH Setpoint (%)", 0.0, 100.0, value=day_avg_rh)
        rh_night = st.number_input("Night RH Setpoint (%)", 0.0, 100.0, value=night_avg_rh)

        st.subheader("Greenhouse Parameters")
        col11, col12 = st.columns(2)
        with col11:
            truss_count = st.number_input(":red[**Number of trusses**]", step=1)           
            AHU_count_pertruss = st.number_input(":red[**Number of AHUs per truss**]", step=1)
            trolley_selection = st.selectbox("Trolley Size", ["No trolley", "Standard (771mm)"])
        with col12:
            truss_length = st.number_input(":red[**Truss Length (mm)**]", value=9600, step=1)
            airtube_length = st.number_input(":red[**Air Tube Length (m)**]", value=110)
            st.markdown("*NOTE:  \n" \
            "Ventilation Rate (m3/h) per AHU is calculated using this configuration to select a fan.*")

        cladd = st.number_input("Cladd Ratio", None, None, 1.2)
        u_leak = st.number_input("U_leak (W/m2/K)", None, None, 0.7)
        u_roof = st.number_input("U_roof (W/m2/K)", None, None, 6.9)
        scr1_eff = st.number_input(":red[**Screen 1 Energy Efficiency (%)**]", 0, 100, 47, step=1)
        scr2_eff = st.number_input(":red[**Screen 2 Energy Efficiency (%)**]", 0, 100, 50, step=1)

        st.subheader("Select Calculation Methods")
        cooling_method = st.selectbox("Active Cooling Load Method", ["Maximum Allowed Temperature and Unlimited RH", "True Temperature and RH Setpoints"])
        heating_method = st.selectbox("Heating Load Method", ["Minimum Allowed Temperature", "True Setpoint"])
        hours_of_heat_storage = st.number_input("Hours of Heat Storage", value=8, step=1)
        peak_percentile = st.selectbox("Peak Demand Percentile", [95, 92.5, 90, 85])

        run = st.form_submit_button("Calculate")



# ---------- STEP 2: Run energy calculations ---------- #
    if run:

    # Clean data and append crop parameters to the weather DataFrame
        weather_df = prepare_weather_df(
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

    # Count AHU and AHU_area
        AHU_count = AHU_count_pertruss * truss_count
        area_m2 = truss_length / 1000 / AHU_count_pertruss * airtube_length
        AHU_type, airflow_m3_h = airflowrate_perAHU_m3h(truss_length, trolley_selection, AHU_count_pertruss)
    
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
        st.markdown(f"AHU type **{AHU_type}** was selected and has a max ventilation rate of **{airflow_m3_h} m3/h**")

elif page == "Info":
    info_page_v2.render()


