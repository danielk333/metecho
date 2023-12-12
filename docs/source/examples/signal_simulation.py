from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import scipy.constants
from tqdm import tqdm

import metecho
import pyant

freq = 50e6
k0 = pyant.coordinates.sph_to_cart(np.array([0, 89, 1.0]), degrees=True)
baud_length = 1e-6
Ptx = 1e6
amp2P = 7.2e6
tx_area = np.pi*100**2
A0 = Ptx/tx_area
target_range = 90e3
target_vel = 25e3
delta_f = (target_vel/scipy.constants.c)*freq
peak_rcs = 1.0**2
noise_sigma = 1e-1
inter_freq = 5e6
samp_freq = 20e6
samp_time = 1/samp_freq
out_freq = 1/(baud_length/2)
decimation = int(samp_freq/out_freq)
measure_time = 80e3/scipy.constants.c
start_time = 2*80e3/scipy.constants.c
samples = int(measure_time/samp_time)

pulses = 512
ipp = 3e-3
ipps = np.arange(0, pulses)
rcs = peak_rcs*np.exp(-((ipps - 200)/30.0)**2)
met_inds = rcs >= peak_rcs/100
t = np.arange(met_inds.sum())*ipp
rcs[np.logical_not(met_inds)] = 0

down_shift_freq = freq - inter_freq

barker13 = np.array(
    [1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1],
    dtype=np.float64,
)

cache_path = Path("./docs/source/examples/data/mu_interp_array.npz").resolve()

beam = pyant.beam_of_radar("mu", "array")

model = metecho.meteor_model.ExpVelocity(
    p0 = np.array([2e3, 0, 100e3]), 
    r0 = np.array([0, -1, -1])/np.sqrt(2),
    vel_params = np.array([60e3, 200, 10]),
)

r, v = model.evaluate(t)

lam = beam.wavelength

t0 = 0


def waveform_generator(t, oversampling=2):
    t_ind = ((t - t0)//(baud_length*oversampling)).astype(np.int64)
    s = np.zeros(t.shape, dtype=np.complex128)
    inds = np.logical_and(t >= 0, t <= baud_length*len(barker13)*oversampling)
    s[inds] = np.exp(-1j*2*np.pi*freq*t[inds])*barker13[t_ind[inds]]
    return s


def vacuum_propagation(t, signal, distance, carrier_frequency):
    t = t + distance/scipy.constants.c
    wavelength = scipy.constants.c/carrier_frequency
    signal = np.exp(-1j*2*np.pi*wavelength*distance)*signal/distance**2
    return t, signal


def sampler():
    return np.arange(0, samples)*samp_time + start_time


def samples_to_transmissions_map(t, distance):
    return t - 2*distance/scipy.constants.c


def noise_generator(t, shape): 
    return noise_sigma*(np.random.randn(*shape) + 1j*np.random.randn(*shape))


def moving_hard_target(t, signal, velocity, frequency, radar_cross_section):
    delta_f = (velocity/scipy.constants.c)*frequency
    return np.exp(-1j*2*np.pi*delta_f*t)*signal*radar_cross_section


def integrating_digitizer(t, signal):
    t_dec = t[np.arange(0, len(t), decimation)]
    signal_dec = np.empty((signal.shape[0], len(t_dec)), dtype=np.complex128)
    down_converter = np.exp(1j*2*np.pi*freq*t)
    signal = signal*down_converter[None, :]
    for chn in range(signal.shape[0]):
        for dind, ind in zip(range(len(t_dec)), range(0, len(t), decimation)):
            signal_dec[chn, dind] = np.sum(signal[chn, ind:(ind+decimation)])
    return t_dec, signal_dec


step_functions = {
    "transmission": lambda t, s, k: s*A0*beam.gain(k),
    "tx-propagation": vacuum_propagation,
    "scattering": moving_hard_target,
    "rx-propagation": vacuum_propagation,
    "reception": lambda t, s, k: amp2P*s[None, :]*beam.channel_signals(k)[:, None],
    "digitization": integrating_digitizer,
}

sim = metecho.simulation.SensorSimulation(
    waveform_generator, 
    noise_generator, 
    sampler,
    samples_to_transmissions_map, 
    step_functions, 
    step_parameters = {
        "tx-propagation": ["distance", "frequency"],
        "scattering": ["velocity", "frequency", "radar_cross_section"],
        "rx-propagation": ["distance", "rx_carrier_frequency"],
        "transmission": ["k"],
        "reception": ["k"],
    }, 
)

dr = target_vel*ipp
meas_samples = int(samples/decimation) + 1

t = sampler()
t = samples_to_transmissions_map(t, target_range)
s_gen = waveform_generator(t)*np.exp(1j*2*np.pi*freq*t)

t_rec, s_rec = sim.evaluate(
    parameters={
        "distance": target_range,
        "velocity": target_vel,
        "frequency": freq,
        "radar_cross_section": peak_rcs,
        "rx_carrier_frequency": freq - delta_f,
        "k": k0,
    }, 
    waveform_parameters={}, 
    noise_parameters={},
    transmission_map_parameters=["distance"],
)
s_rec = np.sum(s_rec, axis=0)
t_rec = t_rec[np.arange(0, len(t), decimation)]

fig, axes = plt.subplots(2, 1)
axes[0].plot(t*1e3, np.real(s_gen), ls="-", color="black", label="real")
axes[0].plot(t*1e3, np.imag(s_gen), ls="-", color="blue", label="imag")
axes[0].set_xlabel("Time [ms]")
axes[0].set_ylabel("Signal [1]")
axes[0].legend()

axes[1].plot(t_rec*1e3, np.real(s_rec), ls="-", color="black", label="real")
axes[1].plot(t_rec*1e3, np.imag(s_rec), ls="-", color="blue", label="imag")
axes[1].set_xlabel("Time [ms]")

# plt.show()
# exit()

amp3 = np.zeros((beam.channels, pulses, meas_samples), dtype=np.complex128)

mind = 0
for ind in tqdm(ipps):
    if met_inds[ind]:
        r_tx = r[:, mind]
        r_tx_n = np.linalg.norm(r_tx)
        v_tx_n = np.sum(r_tx*v[:, mind], axis=0) / r_tx_n
        parameters = {
            "distance": r_tx_n,
            "velocity": v_tx_n,
            "frequency": freq,
            "radar_cross_section": rcs[ind],
            "rx_carrier_frequency": freq*(1 - v_tx_n/scipy.constants.c),
            "k": r_tx / r_tx_n,
        }
        mind += 1
    else:
        parameters = {}

    t_rec, s_rec = sim.evaluate(
        parameters=parameters, 
        waveform_parameters={}, 
        noise_parameters={},
        transmission_map_parameters=["distance"],
        skip=len(parameters) == 0,
        end_shape=(amp3.shape[0], amp3.shape[2]),
    )
    amp3[:, ind, :] = s_rec

fig, ax = plt.subplots()

Imat, Rmat = np.meshgrid(ipps, np.arange(meas_samples))
amp2 = np.sum(amp3, axis=0)
powsum = np.log10(np.abs(amp2.T))*10
# ax.pcolor(Imat, Rmat, powsum)

pmesh = ax.pcolormesh(Imat, Rmat, powsum)
ax.set_xlabel('IPP')
ax.set_ylabel('Sample')


plt.show()