import logging
import numpy as np


from .general import basic_matplotlib_kw
from .. import coordinates

logger = logging.getLogger(__name__)


@basic_matplotlib_kw(subplot_shape=None)
def hammer(
                ax, 
                lon, lat, solar_lon, velocity, radians = False,
                grid=True, res = 100, size=2, scatter_kw = {},
                d_lon = np.radians(30), d_lat = np.radians(15), 
            ):
    
    if grid:
        gird_lon = np.arange(-np.pi, np.pi, d_lon, dtype=np.float64)
        gird_lat = np.arange(-np.pi*0.5, np.pi*0.5, d_lat, dtype=np.float64)

        lon_V = np.linspace(-np.pi, np.pi, res)
        lat_V = np.linspace(-np.pi*0.5, np.pi*0.5, res)

        XYg = [
            coordinates.ecliptic_to_hammer(
                gird_lon[i]*np.ones((res,)), 
                lat_V, 
                radians=True,
            )
            for i in range(len(gird_lon))
        ]
        XYg += [
            coordinates.ecliptic_to_hammer(
                lon_V, 
                gird_lat[i]*np.ones((res,)), 
                radians=True,
            )
            for i in range(len(gird_lat))
        ]

        for hx, hy in XYg:
            ax.plot(hx, hy, '-b', alpha=0.2)

        x_, y_ = coordinates.ecliptic_to_hammer(
            gird_lon,
            np.zeros(gird_lon.shape),
            radians=True,
        )
        for i in range(len(x_)):
            if np.abs(y_[i] - 2) < 1e-12:
                continue
            ax.text(
                x_[i] + 0.02, y_[i] + 0.03, 
                f'{np.degrees(np.mod(1.5*np.pi - gird_lon[i], np.pi*2)):.0f}$^\\circ$', 
            )

        x_, y_ = coordinates.ecliptic_to_hammer(
            -np.pi*0.5*np.ones(gird_lat.shape),
            gird_lat,
            radians=True,
        )
        for i in range(len(x_)):
            if np.abs(y_[i]) < 1e-12:
                continue
            ax.text(
                x_[i] + 0.02*np.cos(gird_lat[i]), y_[i] + 0.03*np.sin(-gird_lat[i]), 
                f'{np.degrees(gird_lat[i]):.0f}$^\\circ$', 
            )

    ham_x, ham_y = coordinates.ecliptic_to_hammer(
        lon, lat, 
        sun_lon=solar_lon,
        radians=radians,
    )
    ax.scatter(ham_x, ham_y, size, velocity, **scatter_kw)

    return ax
