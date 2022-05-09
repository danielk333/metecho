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

simultaneous_meteors = 1


# create storage arrays for numerous parameters/results
MUSIC_peaks = np.empty(len(IPP_n))
MUSIC_peaks.fill(np.NaN)
azimuth = np.empty(len(IPP_n))
azimuth.fill(np.NaN)
elevation = np.empty(len(IPP_n))
elevation.fill(np.NaN)

k_vector = np.empty(
    (3, len(IPP_n))
)
k_vector.fill(np.NaN)

eigs = np.empty(
    (raw.data.shape[raw.axis['channel']], len(IPP_n))
    )
eigs.fill(np.NaN)

k_vector_out = np.empty((3, 1))
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



# max_f_val_array = np.zeros((200,200))

# for I in range(0, 2 - 1):
# ##for I in range(0, len(IPP_n) - 1):
    
#     # calc R_matrix for I in loop
#     R_matrix = calc_R_matrix(raw, I, DATA_n, IPP_n) 

#     # calc F_vals_all with different R_matrix every loop4
#     F_vals_all, kx, ky = MUSIC_grid_search(
#             R_matrix,
#             beam,  
#             num=200, 
#         )

#     x, y = kx[0, :], ky[:, 0]

#     # calc maximum of F_vals_all to find meteor loc
#     max_f_val = np.amax(F_vals_all)

#     # calc max value indices
#     max_index = np.where(F_vals_all == max_f_val)

#     # get x index max and y index max
#     x_max_index = np.asscalar(max_index[0])
#     y_max_index = np.asscalar(max_index[1])

#     # save values for max values in array and use logical indexing for location
#     max_f_val_array[x_max_index, y_max_index] = max_f_val


# # save data in temp npy file
# np.save('temp_multi_grid_data', arr=[max_f_val_array])


# # plotting here, bc some weird shit with saving 2D arrays, dont wanna deal with that rn
# plt.figure()

# plt.pcolormesh(kx[0,:], ky[:, 0], np.log10(np.abs(max_f_val_array)))

# plt.show()









# down here when peak finder is implemented, a number of grids is generated in 
# the process of calculating k_vector_out

#for I in range(0, len(IPP_n) - 1):
for I in range(0, 4 - 1):



    # calc R_matrix for I in loop
    R_matrix = calc_R_matrix(raw, I, DATA_n, IPP_n) 

    # calc F_vals_all with different R_matrix every loop4
    F_vals_all, kx, ky = MUSIC_grid_search(
            R_matrix,
            beam,  
            num=200, 
        )

    x, y = kx[0, :], ky[:, 0]


    # Compute eigendecomposition of covariance matrix
    eigs_out, _ = np.linalg.eig(R_matrix)

    # Find r largest eigenvalues
    eigs_out = np.sort(eigs_out)[::-1]

    peaks_out, azimuth_out, elevation_out, k_vector_out = peak_finder(R_matrix, beam, F_vals_all, kx, ky)

    #eigs = np.append(eigs, i)
    eigs[:, I] = eigs_out
    #MUSIC_peaks[I, :] = np.reshape(peaks_out, newshape=(peaks_out.size, 1))
    #azimuth[I,:] = np.reshape(azimuth_out, newshape=(azimuth_out.size, 1))
    #elevation[I,:] = np.reshape(elevation_out, newshape=(azimuth_out.size, 1))

    # save k_vector output values in k_vector matrix 
    for dim in range(0,2):
        k_vector[dim, I] = k_vector_out[dim,0]

    print('peaks_out_temp: ', peaks_out)


print('peaks_out: ', peaks_out)

# plotting
plt.figure()

plt.pcolormesh(kx[0,:], ky[:, 0], np.log10(np.abs(peaks_out)))

plt.show()




## coherent integration








# Beamforming

## reg








## coherent integration








