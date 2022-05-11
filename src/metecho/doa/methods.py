import metecho
import metecho.generalized_matched_filter as mgmf
import pathlib 
import numpy as np
from math import floor
import pyant
from pyant.functions import get_antenna_positions, calc_antenna_gain, calc_R_matrix, MUSIC_grid_search, peak_finder
from matplotlib import pyplot as plt
import sys

# numpy option to print full numpy array instead of truncation
np.set_printoptions(threshold=sys.maxsize)


# MUSIC

## reg

# h5_mu_file = pathlib.Path('.').home() / 'clones' / 'metecho_clone' / 'metecho' / 'docs' / 'source' / 'examples' / 'data' / 'MU_h5' / '2009' / '06' / '27' / '2009-06-27T09.54.05.690000000.h5'


h5_mu_file = pathlib.Path().home() / 'clones' / 'metecho_clone' / 'metecho' / 'docs' / 'source' / 'examples' / 'data' / 'MU_h5' / '2009' / '06' / '27' / '2009-06-27T09.54.05.690000000.h5'

raw = metecho.data.RawDataInterface(h5_mu_file)
raw_data = raw.data


# instantiate the beam
radarsystem = 'MU_radar'
antenna_pos = get_antenna_positions(radarsystem, requested_positions='req_ant_pos')
beam = calc_antenna_gain(radarsystem, antenna_positions=antenna_pos[0])[0]


print('beam: ', beam)

#indexing = [slice(), slice(), slice()]
#indexing[raw.axis['channel']] = 1



#start_values = matched_filter_output['best_start']
start_values = np.load('indecies.npy')
ipps = np.arange(len(start_values))
ipp_range = [190, 260]

data_selector = np.logical_and.reduce([
    ipps >= ipp_range[0], 
    ipps <= ipp_range[1],
    np.logical_not(np.isnan(start_values)
        ),
])

# IPP_n gives np.array with all element numbers from existant start_values
IPP_n = ipps[data_selector]

# Data_n gives np.array with all existant start_values
DATA_n = start_values[data_selector]
DATA_n = np.floor(DATA_n)

start_values = start_values[data_selector]

simultaneous_meteors = 1


# create storage arrays for numerous parameters/results
MUSIC_peaks = np.zeros(len(IPP_n))
MUSIC_peaks.fill(np.NaN)
azimuth = np.zeros(len(IPP_n))
azimuth.fill(np.NaN)
elevation = np.zeros(len(IPP_n))
elevation.fill(np.NaN)

k_vector = np.zeros(
    (3, len(IPP_n))
)
k_vector.fill(np.NaN)

eigs = np.zeros(
    (raw.data.shape[raw.axis['channel']], len(IPP_n))
    )
eigs.fill(np.NaN)

k_vector_out = np.zeros((3, 1))
k_vector_out.fill(np.NaN)




# function calls for testing if making 1 grid works

# R_matrix = calc_R_matrix(raw, 10, DATA_n, IPP_n)



# print('R_matrix_shape: ', R_matrix.shape)
# print('r_matrix_type: ', type(R_matrix))
# print('R_matrix: ', R_matrix)

# F_vals_all, kx, ky = MUSIC_grid_search(
#     R_matrix,
#     beam,  
#     num=200, 
#     )

# print('F_vals_all_shape: ', np.shape(F_vals_all))
# print('kx_shape: ', np.shape(kx))
# print('ky_shape: ', np.shape(ky))

# # save data in temp npy file
# np.save('temp_grid_data', arr=[F_vals_all, kx, ky])

# print('globals: ', globals())


# create empty arrays for fvals and k vectors contributing to peaks (in this case just max vals)
max_f_val_array = np.zeros(len(IPP_n))
max_f_val_array.fill(np.NaN)

kx_new = np.zeros(len(IPP_n))
max_f_val_array.fill(np.NaN)

ky_new = np.zeros(len(IPP_n))
max_f_val_array.fill(np.NaN)


for I in range(0, 10 - 1):
#for I in range(0, len(IPP_n) - 1):
    
    # calc R_matrix for I in loop
    R_matrix = calc_R_matrix(raw, I, DATA_n, IPP_n) 

    # calc F_vals_all with different R_matrix every loop4
    F_vals_all, kx, ky = MUSIC_grid_search(
            R_matrix,
            beam,  
            num=200, 
        )

    #x, y = kx[0, :], ky[:, 0]

    # calc maximum of F_vals_all to find meteor loc
    max_index = np.unravel_index(np.argmax(F_vals_all), F_vals_all.shape)

    # save values for max values in array and use logical indexing for location
    max_f_val_array[I] = F_vals_all[max_index]

    kx_new[I] = kx[max_index[0], max_index[1]]
    ky_new[I] = ky[max_index[0], max_index[1]]

kz_new = np.sqrt(1 - kx_new**2 - ky_new**2)

k_new = np.array([kx_new, ky_new, kz_new])

# calculate sample_range
sample_range = k_new * start_values

# save data in temp npy file
np.save('temp_multi_grid_data', arr=[max_f_val_array])


# plotting here, bc some weird shit with saving 2D arrays, dont wanna deal with that rn
fig = plt.figure()

ax = fig.add_subplot(projection='3d')

#plt.pcolormesh(kx[0,:], ky[:, 0], np.log10(np.abs(max_f_val_array)))
ax.scatter(sample_range[0], sample_range[1], sample_range[2])

plt.show()










# down here when peak finder is implemented, a number of grids is generated in 
# the process of calculating k_vector_out

# #for I in range(0, len(IPP_n) - 1):
# for I in range(0, 10 - 1):


#     # calc R_matrix for I in loop
#     R_matrix = calc_R_matrix(raw, I, DATA_n, IPP_n) 

#     # calc F_vals_all with different R_matrix every loop4
#     F_vals_all, kx, ky = MUSIC_grid_search(
#             R_matrix,
#             beam,  
#             num=200, 
#         )

#     peaks_out, azimuth_out, elevation_out, k_vector_out = peak_finder(R_matrix, beam, F_vals_all, kx, ky)

#     # Compute eigendecomposition of covariance matrix
#     eigs_out, _ = np.linalg.eig(R_matrix)

#     # Find r largest eigenvalues
#     eigs_out = np.sort(eigs_out)[::-1]

#     # store data in designated arrays
#     eigs[:, I] = eigs_out
#     MUSIC_peaks[I] = peaks_out
#     azimuth[I] = azimuth_out
#     elevation[I] = elevation_out

#     # save k_vector output values in k_vector matrix, 1st=x, 2nd=y, 3th=z in loop
#     for dim in range(0,3):
#         k_vector[dim, I] = k_vector_out[dim, 0]


# # calculate sample_range
# sample_range = k_vector * start_values


# # plotting
# fig = plt.figure()

# ax = fig.add_subplot(projection='3d')

# #plt.pcolormesh(kx[0,:], ky[:, 0], np.log10(np.abs(max_f_val_array)))
# ax.scatter(sample_range[0, :], sample_range[1, :], sample_range[2, :])

# plt.show()



## coherent integration








# Beamforming

## reg








## coherent integration








