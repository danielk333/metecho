import numpy as np


def k_c(v_inf, start_height):
    return start_height + (2.86 - 2 * np.log10(v_inf)) / 0.0612


def k_c_height_curve(v_inf, k_c0):
    return k_c0 - (2.86 - 2 * np.log10(v_inf)) / 0.0612


def k_b(vel_inf, radiant_zenith_angle, atmospheric_density):
    return (
        np.log10(atmospheric_density)
        + 5 / 2 * np.log10(vel_inf)
        - 0.5 * np.log10(np.cos(radiant_zenith_angle))
    )
