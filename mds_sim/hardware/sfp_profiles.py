"""SFP transceiver capability profiles.

Each profile defines the max supported speed and the set of speeds
the ASIC will negotiate to when this SFP type is installed.
"""

SFP_PROFILES = {
    "4G_SW":   {"max_speed": 4000,   "supported": [1000, 2000, 4000, "auto"]},
    "8G_SW":   {"max_speed": 8000,   "supported": [2000, 4000, 8000, "auto"]},
    "16G_SW":  {"max_speed": 16000,  "supported": [4000, 8000, 16000, "auto"]},
    "32G_SW":  {"max_speed": 32000,  "supported": [8000, 16000, 32000, "auto"]},
    "64G_SW":  {"max_speed": 64000,  "supported": [16000, 32000, 64000, "auto"]},
    "128G_SW": {"max_speed": 128000, "supported": [32000, 64000, 128000, "auto"]},
}

DEFAULT_DOM = {
    "temperature_c": 32.5,
    "voltage_v": 3.3,
    "tx_power_dbm": -2.8,
    "rx_power_dbm": -3.2,
    "tx_bias_ma": 6.5,
}


def get_profile(sfp_type):
    return SFP_PROFILES.get(sfp_type)
