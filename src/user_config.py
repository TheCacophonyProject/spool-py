# Threshold for triggering the Analog PIR sensors
APIR_DISPLACEMENT_THRESHOLD = 0.5
APIR_GRADIENT_THRESHOLD = 600

# Max current in mA for the spool reset motor.
MAX_CURRENT = 1600

# After the spool has triggered it will wait this long before resetting the spool.
SPOOL_RESET_DELAY_MINUTES = 10

# Position (Used for day and night calculations)
LATITUDE = -43.532055
LONGITUDE = 172.636230

# Loop interval in minutes, on program 9 this is how often it will loop the program.
TEST_LOOP_INTERVAL = 180

# Switch disables.
# This can be configured to disable the trap from triggering when one or both of the switches is "OPEN" or "CLOSED".
# If not using this leave it at "IGNORE"
# SWITCH1_DISABLE and SWITCH2_DISABLE should be one of "IGNORE", "OPEN", or "CLOSED"
SWITCH1_DISABLE = "IGNORE"
SWITCH2_DISABLE = "IGNORE"
# Switch logic, should be one of "AND" or "OR". If "OR" then the trap will be disabled if either of the
# switches are wanting to disable the trap. If set to "AND" then the trap will only be disabled if both switches are wanting to disabling the trap.
SWITCH_LOGIC = "OR"
# For an example. If setting up a reed switch that is "CLOSED" when the holding cage door is open 
# (a reed switch is closed when next to a magnet) and we want to disable the trap when the holding cage 
# door is closed, we would configure the switch that the reed switch is connected to as "OPEN", other one as 
# "IGNORE" and set the the logic as "OR". 
# So when the cage door closes, the switch goes from "CLOSED" to "OPEN" and the trap will be disabled until the cage door is open again.

# Observation Mode
# In Observation Mode the trap will reset just at boot and not trigger at all.
# If setup in a mode that will report events instead of sending a "triggered" event when the trap triggers it will instead send a "dry-trigger" event instead.
# This can be useful for testing how well the AI trigger works without scaring the animals.
# We might just add a "motion" event so we don't need to add details on if the trap is in observation mode or not.
OBSERVATION_MODE = False
