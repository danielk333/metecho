'''
Using a meteor model
=========================
'''

import metecho
import numpy as np
import matplotlib.pyplot as plt

model = metecho.meteor_model.ExpVelocity(
    p0 = np.array([0, 0, 100e3]), 
    r0 = np.array([0, -1, -1])/np.sqrt(2),
    vel_params = np.array([60e3, 200, 10]),
)

t = np.linspace(0, 0.3, num=1000)

r, v = model.evaluate(t)

fig, axes = plt.subplots(2, 1)
axes[0].plot(t, r[2, :]*1e-3)
axes[1].plot(t, np.linalg.norm(v, axis=0)*1e-3)
axes[0].set_ylabel('Up [km]')
axes[1].set_ylabel('Velocity [km/s]')
axes[1].set_xlabel('Time [s]')

plt.show()
