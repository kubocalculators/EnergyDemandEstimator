"""
If the user selects "info" in the side bar, the following inforamtion will be displayed
"""

import streamlit as st

def render():
    st.title("How This Calculator Works")
    
    st.markdown(
        """
    This app estimates the greenhouse heating and active cooling demands from hourly climate data and user-set climate targets.
    """
    )

    st.header("Inputs Explained")
    st.markdown(
            """

    **Crop Climate Parameters**
    - **Setpoint Temperature**: This is the ideal temperature for the crop at day/night
    - **Setpoint RH**: This is the ideal relative humidity for the crop at day/night
    - **Max/Min**: These are the extreme, but allowable temperatures and humidities. These are used to generate more moderate energy loads during periods of extreme outdoor conditions.
 
    **Greenhouse Parameters**  \n
    The layout of the greenhouse determines the total energy consumption = energy in W/m2 is multiplied by area per AHU and # of AHUs.
    - **Cladd Ratio**: This describes the ratio of the floor area to the total surface area of the "cladding" (ie. the glass of the greenhouse). It is multiplied by the U_roof (W/m2/k) so that it is applied for the "true" surface area of the roof.
    - **U_leak**: Accounts for heat loss which can be attributed to air "leaking" out of the greenhouse.
    - **U_roof**: Accounts for heat loss through the glass roof. Adjust this value only if the roof is not made of glass.
    - **Screen 1 Energy Efficiency**: This is the energy saving efficiency of the lower, "first" screen and will be assumed closed during the day & night in the calculations
    - **Screen 2 Energy Efficiency**: This is the energy saving efficiency of the upper, "second" screen and will be assumed closed during the night in the calculations
    
    """
    )
    
    st.header("Calculation Methods")
    st.subheader("Active Cooling Load Method")

    st.markdown(
        """
    **Step 1**: Extracts information needed from hourly climate data
    - Outside Temperature (C) and Relative Humidity (%)
    - Crop Ideal Temperature Setpoint (C) and Relative Humidity Setpoint (%)
    - Crop Maximun Temperature (C) and Relative Humidity (%)  \n
    **Step 2**: Calculates humidity ratio and enthalpy from outside conditions (T and RH)  \n
    **Step 3**: Checks if cooling is required (hourly) by comparing the temperautre outside to the maximum allowed temperature for the crop  \n
    **Step 4**: Calculates the air conditions (T and RH) after the padwall
    - The padwall is limited by a maximum efficiency of 80%, but can be further limited by the humidity cap,
    calculated from the maximum allowable T and RH. This is to prevent an extreme latent energy load on the cold blocks.
    - **NOTE**: This does not limit the outlet of the padwall to the max RH ***and*** T, only to the humidity ratio calculated by
    their combined influence.  \n
    **Step 5**: Calculates the hourly cooling demand (J/kg) based on the selected method:
    - ***True Temperature and RH Setpoints***: The demand of the cold block is to bring the air conditions to setpoint T and RH   \n
    """)
    st.latex(r"""
    \text{Humidity Ratio} = W_{\text{set}} = f(T_{\text{set}}, RH_{\text{set}}, P_{\text{atm}}) \\
    \text{Enthalpy} = h_{\text{set}} = f(T_{\text{set}}, W_{\text{set}}) \\
    \text{Cooling Load, J/kg} = Q_{\text{cooling}} = h_{\text{padwall}} - h_{\text{set}}
    """)

    st.markdown(
        """
    - ***Maximum Allowed Temperature and Unlimited RH***: The demand of the cold block is to bring the air conditions to max allowed T and leaving humidity ratio as it left the padwall  \n
    """
    )
    st.latex(r"""
    \text{Humidity Ratio} = W_{\text{padwall}} \\
    \text{Enthalpy} = h_{\text{T,max}} = f(T_{\text{max}}, W_{\text{padwall}}) \\
    \text{Cooling Load, J/kg} = Q_{\text{cooling}} = h_{\text{padwall}} - h_{\text{T,max}}
    """)

    st.markdown(
        """
    **Step 6**: Using the airflow rate (per AHU) and area (per AHU), calculates the hourly cooling demand in W/m2  \n
    """
    )

    pdf_file_path = "active_cooling_v2_visualized.pdf"

    try:
        with open(pdf_file_path, "rb") as f:
            pdf_bytes = f.read()

        st.download_button(
            label="Download Visualization of Active Cooling Calculation (PDF)",
            data=pdf_bytes,                         # bytes-like object
            file_name="active_cooling_v2_visualized.pdf",
            mime="application/pdf",                 # correct MIME for PDF
        )

    except FileNotFoundError:
        st.error(f"Error: {pdf_file_path} not found. Please ensure the file is present.")

    st.subheader("Heating Load Method")
    st.markdown(
        """
    **Step 1**: Extracts information needed from hourly climate data (outside temperature and whether or not it is daytime)  \n
    **Step 2**: Sets the target temperature based on the calculation method selected
    - ***True Setpoint***: The heating load will be calculated in order to bring the outside temperature up to the ideal setpoint temperature
    - ***Minimum Allowed Temperature***: The heating load will be calculate in order to bring the outside temperuatre up to the minimum temperature  \n
    **Step 3**: Checks if heating is required (hourly) by comparing the temperature outside to the selected target temperature  \n
    **Step 4**: Calculates the heat loss coefficient. Screen 1 is closed all the time. Screen 2 is closed only at night.  \n
    **Step 5**: Calculates the hourly heating demand (W/m2)  \n
    """)
    st.latex(r"""
    Q = \left( u_{\text{roof}} (1 - \text{scr1\_eff}) (1 - \text{scr2\_eff}) \cdot \text{cladd}
        + u_{\text{leak}} \right)(T_{\text{target}} - T_{\text{out}})
    """)


    st.markdown(
    """    
    ---
    **Hours of Heat Storage**: The HST volume is calculated based on the number of hours of storage at a specific heating load. The ΔT of supply/return from the HST is set to be 15C.  \n
    """
    )
    st.latex(r"""
    V_{HST} = \frac{\text{Peak Demand} \times \text{Hours}}
    {C_{p,\text{water}} \times \rho_{\text{water}} \times \Delta T}
    """)
    st.markdown(
        """
    **Peak Demand Percentile**: This selection determines which percentile of calculated heating demand will be used in the calculation of HST volume.
    """
    )
