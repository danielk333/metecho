import metecho
import metecho.generalized_matched_filter as mgmf
import pathlib 
import numpy as np
from math import floor


# MUSIC

## reg

# h5_mu_file = pathlib.Path('.').home() / 'clones' / 'metecho_clone' / 'metecho' / 'docs' / 'source' / 'examples' / 'data' / 'MU_h5' / '2009' / '06' / '27' / '2009-06-27T09.54.05.690000000.h5'

start_values = np.load('indecies.npy')
start_values_ones = np.array([])

for i in start_values:
    if np.isnan(i) == True:
        start_values_ones = np.append(start_values_ones, 0)
    else:
        start_values_ones = np.append(start_values_ones, 1)



indecies = start_values_ones
print('indecies: ', indecies)

#indecies = matched_filter_output['best_start']

#IPP_n = meteor.ipp(indecies)   # what happens here??
DATA_n = np.floor(indecies)

simultaneous_meteors = 1

# so here they seem to be creating empty lists for values that are to be calculated?
# is this really nessesary? and then why work with NaN and nog just .empty or .zero
MUSIC_peaks = np.empty(len(IPP_n)).fill(NaN)
azimuth = np.empty(len(IPP_n)).fill(NaN)
elevation = np.empty(len(IPP_n)).fill(NaN)
k_vector = np.empty(3, len(IPP_n)).fill(NaN)
eigs = np.empty(raw_data.radar.beam.channels, len(IPP_n)).fill(NaN)


# # IPP / R-matrix func
# def MUSIC_IPP(raw_data, I, DATA_n, IPP_n, p):
#     """ Calculates R-matrix

#     """

#     nhigh = (raw_data.amp3, 2).size     # assuming this is a np.array
    
#     select_range_gates = DATA_n(I) : (DATA_n(I) + raw_data.radar.encoding.Bits)

#     if select_range_gates[len(select_range_gates) - 1] > nhigh:
#         select_range_gates(select_range_gates > nhigh) = np.array([])

#     amp3_subset = squeeze(raw_data.amp3(:, select_range_gates, IPP_n(I)))

#     R_matrix = (amp3_subset * np.transpose(amp3_subset)) / (amp3_subset,1).size
    

#     return R_matrix




# for i in range(1,len(IPP_n)):

#     eigs = np.append(eigs, i)
#     eigs(:,i) = eigs_out;
#     MUSIC_peaks(i,:) = transpose(peaks_out(:))
#     azimuth(i,:) = transpose(azimuth_out(:))
#     elevation(i,:) = transpose(elevation_out(:))
    
#     for dim in range(1,3):
#         k_vector = np.append(k_vector, k_vector_out, dim)





## coherent integration








# Beamforming

## reg








## coherent integration








