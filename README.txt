This calculator computes the expected MW of cooling and heating required based on input climate data, crop climate parameters, and
the configuration of the greenhouse (area, # of AHUs, etc.)

There are two methods of calculating the heating load:
(1) Temperature difference to the minimum allowed temperature in the greenhouse
(2) Temperature difference to the exact temperature setpoint for the greenhouse

Heating load is then calculated using the combined heat loss coefficients of the roof, leakage, and the screens. The second (black out screen)
is considered closed only during the night and during the day, the energy screen is considered fully closed any time heating is required.

There are also two methods of calculating the cooling load
(1) Cooling needed to reach the exact temperature AND relative humidity setpoints
(2) Cooling needed to reach maximum allowed temperature in the greenhouse and relative humidity is unrestricted

The pad wall is included in the active cooling load calculations, but RH_cap (an input) is included to avoid an overly high latent load
From the calculated output of the air conditions leaving the pad wall: T_pw and RH_pw
OPTION (1)
The cold block will cool to T_set and RH_set

OPTION (2)
The cold block will cool to T_max and W_pw.
NOTE: This may still be higher RH than RH_cap if T_pw is lower than T_max
