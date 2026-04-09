import numpy as np
import numpy.typing as npt


def k_c(
    v_inf: float | npt.NDArray[np.floating], start_height: float | npt.NDArray[np.floating]
) -> float | npt.NDArray[np.floating]:
    return start_height + (2.86 - 2 * np.log10(v_inf)) / 0.0612


def k_c_height_curve(
    v_inf: float | npt.NDArray[np.floating], k_c0: float | npt.NDArray[np.floating]
) -> float | npt.NDArray[np.floating]:
    return k_c0 - (2.86 - 2 * np.log10(v_inf)) / 0.0612


def k_b(
    vel_inf: float | npt.NDArray[np.floating],
    radiant_zenith_angle: float | npt.NDArray[np.floating],
    atmospheric_density: float | npt.NDArray[np.floating],
) -> float | npt.NDArray[np.floating]:
    return (
        np.log10(atmospheric_density)
        + 5 / 2 * np.log10(vel_inf)
        - 0.5 * np.log10(np.cos(radiant_zenith_angle))
    )
