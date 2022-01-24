'''
Advanced analysis: IAU meteor showers
========================================

'''
import numpy as np
import matplotlib.pyplot as plt
from astropy.time import Time

from metecho import meteoroid_streams as ms

# Get the IAU data
data, meta = ms.iau.get_streams_data()

# Cols to print
cols = ['shower name', 'Ra', 'De', 'Vg', 'activity', 'Parent body', 'Ote']

# Select a meteor shower
gemenid_data = data[data['shower name'] == 'Orionids']

print(gemenid_data[cols])

ra = gemenid_data['Ra'].values[0]
dec = gemenid_data['De'].values[0]

# Lets reproduce the radiant elevation in Kero et. al 2011
# observing time 2009 October 19 23:00 JST (UTC +9)
epoch = Time('2009-10-19T14:00:00', format='isot', scale='utc')
t = np.linspace(0, 33, num=1000)

# Mu radar location
lat = 34.854028
lon = 136.10562

# Calculate the local radiant
radiant = ms.radiant.local(t*3600.0, epoch, ra, dec, lon, lat)

above = radiant.alt > 0

fig, axes = plt.subplots(2, 1)

az = radiant.az.value.copy()
az[np.logical_not(above)] = np.nan
el = radiant.alt.value.copy()
el[np.logical_not(above)] = np.nan

axes[0].plot(t, az, '-', label='Above horizon')
axes[0].plot(t[np.logical_not(above)], radiant.az[np.logical_not(above)], '--', label='Below horizon')
axes[0].set_xlabel('Time past epoch [h]')
axes[0].set_ylabel('Radiant azimuth [deg]')
axes[0].legend()

axes[1].plot(t, el, '-', label='Above horizon')
axes[1].plot(t[np.logical_not(above)], radiant.alt[np.logical_not(above)], '--', label='Below horizon')
axes[1].set_xlabel('Time past epoch [h]')
axes[1].set_ylabel('Radiant elevation (altitude) [deg]')

fig.suptitle(f'Orionids local radiant at MU radar on {epoch}')

plt.show()
