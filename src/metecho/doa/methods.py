import metecho
import metecho.generalized_matched_filter as mgmf
import pathlib 
import numpy as np
from math import floor
import pyant


# use IPP's to calc R-matrix func
def R_matrix(raw_data, I, DATA_n, IPP_n, p):
    """ Calculates R-matrix

    """

    # get number of sample values (85 for used data)
    nhigh = raw.data.shape[raw.axis['sample']]
    
    # create 1D array for select range gates
    select_range_gates = np.arange(DATA_n[I], DATA_n[I] + len(raw.meta['code']) + 1)


    # option 1
    if select_range_gates[-1] > nhigh:

        # hopefully: if element in select_range_gates > nhigh, delete it from array
        np.delete(select_range_gates, select_range_gates > nhigh)


    # # option 2
    # # if element in select_range_gates > nhigh, delete it from array
    # select_range_gates = np.delete(select_range_gates, np.where(
    #     (select_range_gates[-1] > nhigh) & (select_range_gates > nhigh))
    # )



    # calc samples_subset
    samples_subset = squeeze(raw.data[raw.axis['sample']][:, select_range_gates, IPP_n[I]])

    # calc R_matrix
    R_matrix = (samples_subset @ samples_subset.T) / np.shape((samples_subset, 1))
    

    return R_matrix


def MUSIC_grid_search(R_matrix, num, radar, **options):
    """ creates a grid for 1 ore more multiple simultanious meteors.

    INPUT: 

    # covariance matrix
    R_matrix = np.array([])
    # resolution
    num = int
    radar = 

    """
    
#     options_array = np.array([
#         ['met_n', 'restriction', 'elevation'], 
#         [1, np.array([[-1, 1],[-1, 1]]), 0]])

# # this doenst work of course, but what would?
#     # for option, std_value in options_array:
#     #     if option in options:
#     #        options[option] = value



    # number of meteors to analyse simultaniously
    if 'met_n' not in options:
        met_n = 1

    # area of signal range in which to analyse results
    if 'restriction' not in options:    
    restriction = np.array([[-1, 1],[-1, 1]])

    # angle of elevation
    if 'elevation' not in options:
    elevation = 0


    N = np.shape(R_matrix, 1)

    # Compute eigendecomposition of covariance matrix
    Q ,D = np.linalg.eig(R_matrix)

    # Find r largest eigenvalues
    I = numpy.sort(np.diag(D))[::-1]

    # # n maximum indecies
    # n = 2
    # indecies = (-D).argsort()[:n]
    # I = Q[indecies]


    kx, ky = np.meshgrid(np.linspace(restriction(1, 1),restriction(1, 2), num), 
        np.linspace(restriction(2, 1),restriction(2, 2), num))

    kz = np.sqrt(1 - kx**2 - ky**2)

    # Sort the eigenvectors to put signal eigenvectors first
    Q = Q[:, I]

    # Get the signal eigenvectors
    # Qs = Q (:,1:met_n)

    if met_n > 1:

        Qn = np.empty((met_n, 1))
        Qn.fill(np.NaN)

        for ind in np.arange(1, met_n + 1):
            Qn[ind] = Q[:, 
            np.array(
                [np.array(1, [ind-1] + 1), np.arange([ind+1], N + 1)]
                )
            ]
    else:

        # Get the noise eigenvectors
        Qn = Q[:, np.arange(2, N + 1)]

    if met_n > 1:

        F_vals = np.zeros([num, num, met_n])
        
        for xi in np.arange(1, num + 1):

            for yi in np.arange(1, num + 1):

                if kx[xi, yi]**2 + ky[xi, yi]**2 <= np.cos(elevation_limit):

                    a = pyant.Array.complex(k=
                        [kx[xi, yi], 
                        ky[xi, yi], 
                        kz[xi, yi]].T
                        )
                    
                    for ind in np.arange(1, met_n + 1):

                        F_vals[xi, yi, ind] = (a.T @ a) / (a.T @ Qn[ind] @ Qn[ind].T @ a)
        

    else:
        F_vals = np.zeros([num, num])
        
        for xi in np.arange(1, num + 1):

            for yi in np.arange(1, num + 1):

                if kx[xi, yi]**2 + ky[xi, yi]**2 <= np.cos(elevation_limit):

                    a = pyant.Array.complex(k=
                        [kx(xi, yi), 
                        ky(xi, yi), 
                        kz(xi, yi)].T
                        )

                    F_vals[xi, yi] = (a.T @ a) / (a.T @ Qn @ Qn.T @ a)

    return F_vals, kx, ky


# MUSIC

## reg

# h5_mu_file = pathlib.Path('.').home() / 'clones' / 'metecho_clone' / 'metecho' / 'docs' / 'source' / 'examples' / 'data' / 'MU_h5' / '2009' / '06' / '27' / '2009-06-27T09.54.05.690000000.h5'


h5_mu_file = pathlib.Path('.').home() / 'clones' / 'metecho_clone' / 'metecho' / 'docs' / 'source' / 'examples' / 'data' / 'MU_h5' / '2009' / '06' / '27' / '2009-06-27T09.54.05.690000000.h5'

raw = metecho.data.RawDataInterface(h5_mu_file)
raw_data = raw.data

print('raw_data shape: ', np.shape(raw.data))
print('raw_data pulse count: ', (raw_data.shape[raw.axis["pulse"]]))
print('raw_data: ', (raw_data))
print('raw_data_channel: ', raw.axis['channel'])

#indexing = [slice(), slice(), slice()]
#indexing[raw.axis['channel']] = 1

print('test1: ', np.shape(raw.data[0,7,9]))
print('test2: ', np.shape(raw.data[raw.axis['channel']]))
#print('test2: ', np.shape(raw.data[tuple(indexing)]))
print('test3: ', raw.data[raw.axis['sample']])
#print('test4: ', raw.data.radar)
print('nhigh: ', raw.data.shape[raw.axis['sample']])
print('test 5: ', np.arange(0,10,1)[-2])
print('radar.encoding.bits: ', len(raw.meta['code']))

print('samples_len: ', len(raw.data[raw.axis['sample']]))
print('samples: ', raw.data[raw.axis['sample']])

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


F_vals_all, kx, ky = MUSIC_grid_search(
    R_matrix, 
    resolution, 
    raw_data.radar
    )






for I in range(0, len(IPP_n) - 1):

    # calc k_vector values
    k_vector_out = None

    #eigs = np.append(eigs, i)
    # eigs(:,i) = eigs_out;
    # MUSIC_peaks(i,:) = transpose(peaks_out(:))
    # azimuth(i,:) = transpose(azimuth_out(:))
    # elevation(i,:) = transpose(elevation_out(:))
    
    for dim in range(0,2):
        k_vector[dim, I] = k_vector_out





## coherent integration








# Beamforming

## reg








## coherent integration








