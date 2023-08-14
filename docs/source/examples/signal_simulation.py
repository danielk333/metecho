import numpy as np
import matplotlib.pyplot as plt
import scipy.constants

import metecho
import pyant

freq = 50e6
k0 = pyant.coordinates.sph_to_cart(np.array([0, 89, 1.0]), degrees=True)
baud_length = 1e-6
Ptx = 1e6
amp2P = 7.2e6
tx_area = np.pi*100**2
A0 = Ptx/tx_area
target_range = 100e3
target_vel = 25e3
delta_f = (target_vel/scipy.constants.c)*freq
rcs = 10.0**2
noise_sigma = 1e-2
inter_freq = 5e6
samp_freq = 20e6
out_freq = 1/(baud_length/2)
decimation = samp_freq/out_freq

barker13 = np.array([1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1],
                    dtype=np.float64)

beam = pyant.models.Airy(
    azimuth=0,
    elevation=90.0,
    frequency=freq,
    I0=10**4.81,
    radius=10.0,
    degrees=True,
)

lam = beam.wavelength

t0 = 0


def waveform_generator(t):
    t_ind = ((t - t0)//baud_length).astype(np.int64)
    s = np.zeros(t.shape, dtype=np.complex128)
    inds = np.logical_and(t >= 0, t <= baud_length*len(barker13))
    s[inds] = np.exp(-1j*2*np.pi*freq*t[inds])*barker13[t_ind[inds]]
    return s


step_functions = {
    "transmission": lambda t, s: s*A0*beam.gain(k0),
    "tx-propagation": lambda t, s: [t + target_range/scipy.constants.c, np.exp(-1j*2*np.pi*lam*target_range)*s/target_range**2],
    "scattering": lambda t, s: np.exp(-1j*2*np.pi*delta_f*t)*s*rcs,
    "rx-propagation": lambda t, s: [t + target_range/scipy.constants.c, np.exp(-1j*2*np.pi*lam*target_range)*s/target_range**2],
    "reception": lambda t, s: s*amp2P*beam.gain(k0),
    "digitization": lambda t, s: s*np.exp(1j*2*np.pi*freq*t),
}


def sampler():
    return np.arange(-100, 2000)*baud_length/100 + target_range/scipy.constants.c*2


def inverse_time_of_flight(t): 
    return t - target_range/scipy.constants.c*2


def noise_generator(t, shape): 
    return noise_sigma*(np.random.randn(*shape) + 1j*np.random.randn(*shape))


sim = metecho.simulation.SensorSimulation(
    waveform_generator, 
    noise_generator, 
    sampler,
    inverse_time_of_flight, 
    step_functions, 
    step_parameters = {}, 
)

t_rec, s_rec = sim.evaluate(
    parameters={}, 
    waveform_parameters={}, 
    noise_parameters={},
)

t = sampler()
t = inverse_time_of_flight(t)
s_gen = waveform_generator(t)*np.exp(1j*2*np.pi*freq*t)

fig, axes = plt.subplots(2, 1)
axes[0].plot(t*1e3, np.real(s_gen), ls="-", color="black", label="real")
axes[0].plot(t*1e3, np.imag(s_gen), ls="-", color="blue", label="imag")
axes[0].set_xlabel("Time [ms]")
axes[0].set_ylabel("Signal [1]")
axes[0].legend()

axes[1].plot(t_rec*1e3, np.real(s_rec), ls="-", color="black", label="real")
axes[1].plot(t_rec*1e3, np.imag(s_rec), ls="-", color="blue", label="imag")
axes[1].set_xlabel("Time [ms]")

plt.show()
