import logging
import numpy as np


from .general import basic_matplotlib_kw
from .. import coordinates
from .. import meteoroid_streams

logger = logging.getLogger(__name__)


def add_hammer_grid(
    ax,
    d_lon=np.radians(30),
    d_lat=np.radians(15),
    res=100,
    alpha=0.2,
    color="black",
):
    gird_lon = np.arange(-np.pi, np.pi + d_lon, d_lon, dtype=np.float64)
    gird_lat = np.arange(-np.pi * 0.5, np.pi * 0.5, d_lat, dtype=np.float64)

    lon_V = np.linspace(-np.pi, np.pi, res)
    lat_V = np.linspace(-np.pi * 0.5, np.pi * 0.5, res)

    XYg = [
        coordinates.ecliptic_to_hammer(
            gird_lon[i] * np.ones((res,)),
            lat_V,
            radians=True,
        )
        for i in range(len(gird_lon))
    ]
    XYg += [
        coordinates.ecliptic_to_hammer(
            lon_V,
            gird_lat[i] * np.ones((res,)),
            radians=True,
        )
        for i in range(len(gird_lat))
    ]

    for hx, hy in XYg:
        ax.plot(hx, hy, "-", color=color, alpha=alpha)

    x_, y_ = coordinates.ecliptic_to_hammer(
        gird_lon,
        np.zeros(gird_lon.shape),
        radians=True,
    )
    for i in range(len(x_)):
        if np.abs(y_[i] - 2) < 1e-12:
            continue
        ax.text(
            x_[i] + 0.02,
            y_[i] + 0.03,
            f"{np.degrees(np.mod(1.5*np.pi - gird_lon[i], np.pi*2)):.0f}$^\\circ$",
            color=color,
        )

    x_, y_ = coordinates.ecliptic_to_hammer(
        -np.pi * 0.5 * np.ones(gird_lat.shape),
        gird_lat,
        radians=True,
    )
    for i in range(len(x_)):
        if np.abs(y_[i]) < 1e-12:
            continue
        ax.text(
            x_[i] + 0.02 * np.cos(gird_lat[i]),
            y_[i] + 0.03 * np.sin(-gird_lat[i]),
            f"{np.degrees(gird_lat[i]):.0f}$^\\circ$",
            color=color,
        )


@basic_matplotlib_kw(subplot_shape=None)
def hammer(
    ax,
    lon,
    lat,
    solar_lon,
    velocity,
    radians=False,
    grid=True,
    grid_res=100,
    grid_alpha=0.2,
    grid_color="black",
    d_lon=np.radians(30),
    d_lat=np.radians(15),
    size=2,
    mpl_kw={},
):
    if grid:
        add_hammer_grid(
            ax,
            d_lon=d_lon,
            d_lat=d_lat,
            res=grid_res,
            alpha=grid_alpha,
            color=grid_color,
        )

    ham_x, ham_y = coordinates.ecliptic_to_hammer(
        lon,
        lat,
        sun_lon=solar_lon,
        radians=radians,
    )
    sc = ax.scatter(ham_x, ham_y, size, velocity, **mpl_kw)

    return ax, [sc]


@basic_matplotlib_kw(subplot_shape=None)
def hammer_density(
    ax,
    lon,
    lat,
    solar_lon,
    radians=False,
    grid=True,
    grid_alpha=0.2,
    grid_res=100,
    d_lon=np.radians(30),
    d_lat=np.radians(15),
    bins=200,
    mpl_kw={},
):
    ham_x, ham_y = coordinates.ecliptic_to_hammer(
        lon,
        lat,
        sun_lon=solar_lon,
        radians=radians,
    )

    H, xedges, yedges = np.histogram2d(ham_x, ham_y, bins=bins)
    X, Y = np.meshgrid(
        0.5 * (xedges[1:] + xedges[:-1]),
        0.5 * (yedges[1:] + yedges[:-1]),
    )

    pc = ax.pcolormesh(X, Y, H.T, **mpl_kw)

    if grid:
        add_hammer_grid(
            ax,
            d_lon=d_lon,
            d_lat=d_lat,
            res=grid_res,
            alpha=grid_alpha,
        )

    return ax, [pc]


@basic_matplotlib_kw(subplot_shape=None)
def hammer_iau_streams(ax, showers, mean_radiant=True, size=300, text_offset=(0.03, 0.02), mpl_kw={}):
    data, _ = meteoroid_streams.iau.get_streams_data()
    all_showers = data["Code"].unique()

    ham_x = []
    ham_y = []
    for shower in showers:
        inds = data["Code"] == shower
        if shower not in all_showers:
            continue
        if inds.size == 0:
            continue

        if mean_radiant:
            radiant = meteoroid_streams.radiant.ecliptic(
                np.nanmean(data[inds]["Ra"]),
                np.nanmean(data[inds]["De"]),
            )
            sun_lon = np.nanmean(data[inds]["LaSun"])
        else:
            radiant = meteoroid_streams.radiant.ecliptic(
                data[inds]["Ra"],
                data[inds]["De"],
            )
            sun_lon = data[inds]["LaSun"]
        lon = radiant.lon.deg
        lat = radiant.lat.deg

        hx, hy = coordinates.ecliptic_to_hammer(
            lon,
            lat,
            sun_lon=sun_lon,
            radians=False,
        )
        ham_x.append(hx)
        ham_y.append(hy)
        if mean_radiant:
            ax.text(
                hx + text_offset[0],
                hy + text_offset[1],
                shower,
            )
        else:
            for (
                x,
                y,
            ) in zip(hx, hy):
                ax.text(
                    x + text_offset[0],
                    y + text_offset[1],
                    shower,
                )
    if not mean_radiant:
        ham_x = np.concatenate(ham_x)
        ham_y = np.concatenate(ham_y)

    sc = ax.scatter(ham_x, ham_y, size, **mpl_kw)

    return ax, [sc]
