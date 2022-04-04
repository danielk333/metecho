import metecho
import metecho.generalized_matched_filter as mgmf
import pathlib 
import numpy as np
from math import floor


# MUSIC

## reg

# h5_mu_file = pathlib.Path('.').home() / 'clones' / 'metecho_clone' / 'metecho' / 'docs' / 'source' / 'examples' / 'data' / 'MU_h5' / '2009' / '06' / '27' / '2009-06-27T09.54.05.690000000.h5'


h5_mu_file = pathlib.Path('.').home() / 'clones' / 'metecho_clone' / 'metecho' / 'docs' / 'source' / 'examples' / 'data' / 'MU_h5' / '2009' / '06' / '27' / '2009-06-27T09.54.05.690000000.h5'

raw = metecho.data.RawDataInterface(h5_mu_file)
raw_data = raw.data

print('raw_data type: ', type(raw.data))
print('raw_data pulse count: ', (raw_data.shape[raw.axis["pulse"]]))
print('raw_data: ', (raw_data))
print('raw_data_channel: ', raw.axis['channel'])

print('test1: ', np.shape(raw.data[0]))
print('test2: ', np.shape(raw.data[raw.axis['channel']]))


#start_values = matched_filter_output['best_start']
start_values = np.load('indecies.npy')
ipps = np.arange(len(start_values))
ipp_range = [190, 260]

data_selector = np.logical_and.reduce([
    ipps >= ipp_range[0], 
    ipps <= ipp_range[1],
    np.logical_not(np.isnan(start_values)),
])

# IPP_n gives np.array with all element numbers from existant start_values
IPP_n = ipps[data_selector]

# Data_n gives np.array with all existant start_values
DATA_n = start_values[data_selector]
DATA_n = np.floor(DATA_n)

print('data_selector: ', data_selector)
print('IPP_n: ', IPP_n)
print('DATA_n: ', DATA_n)


simultaneous_meteors = 1

# so here they seem to be creating empty lists for values that are to be calculated?
# is this really nessesary? and then why work with NaN and nog just .empty or .zero
MUSIC_peaks = np.empty(len(IPP_n)).fill(np.NaN)
azimuth = np.empty(len(IPP_n)).fill(np.NaN)
elevation = np.empty(len(IPP_n)).fill(np.NaN)
k_vector = np.empty(
    (3, len(IPP_n))
).fill(np.NaN)

# note to self: the fck should i solve this?? what does this look like in the matlab code??
eigs = np.empty((raw.data[raw.axis['channel']], len(IPP_n))).fill(np.NaN)
eigs = np.empty((0, len(IPP_n))).fill(np.NaN)





# # IPP / R-matrix func
# def calc_k_vector(raw_data, I, DATA_n, IPP_n, p):
#     """ Calculates R-matrix

#     """

#     nhigh = raw.data.shape[raw.axis['samples']]
    
#     select_range_gates = DATA_n(I) : (DATA_n(I) + raw_data.radar.encoding.Bits)

#     if select_range_gates[len(select_range_gates) - 1] > nhigh:
#         select_range_gates(select_range_gates > nhigh) = np.array([])

#     amp3_subset = squeeze(raw_data.amp3[:, select_range_gates, IPP_n(I)]

#     R_matrix = (amp3_subset * np.transpose(amp3_subset)) / (amp3_subset,1).size
    

#     return R_matrix


for i in range(0, len(IPP_n) - 1):

    k_vector_out = None

    #eigs = np.append(eigs, i)
    # eigs(:,i) = eigs_out;
    # MUSIC_peaks(i,:) = transpose(peaks_out(:))
    # azimuth(i,:) = transpose(azimuth_out(:))
    # elevation(i,:) = transpose(elevation_out(:))
    
    for dim in range(0,2):
        k_vector[[dim],[i]] = k_vector_out





## coherent integration








# Beamforming

## reg








## coherent integration








