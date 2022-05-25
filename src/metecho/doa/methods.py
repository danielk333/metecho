import metecho
import metecho.generalized_matched_filter as mgmf
import pathlib 
import numpy as np
from math import floor
import pyant
from pyant.functions import get_antenna_positions, calc_antenna_gain, calc_R_matrix, MUSIC_grid_search, peak_finder
from matplotlib import pyplot as plt
import sys
import multiprocessing as mp


# numpy option to print full numpy array instead of truncation
np.set_printoptions(threshold=sys.maxsize)

metecho.profiler.init('full', True)
metecho.profiler.start('full')
metecho.profiler.enable('')

# MUSIC

## reg

# h5_mu_file = pathlib.Path('.').home() / 'clones' / 'metecho_clone' / 'metecho' / 'docs' / 'source' / 'examples' / 'data' / 'MU_h5' / '2009' / '06' / '27' / '2009-06-27T09.54.05.690000000.h5'


h5_mu_file = pathlib.Path().home() / 'clones' / 'metecho_clone' / 'metecho' / 'docs' / 'source' / 'examples' / 'data' / 'MU_h5' / '2009' / '06' / '27' / '2009-06-27T09.54.05.690000000.h5'

raw = metecho.data.RawDataInterface(h5_mu_file)
raw_data = raw.data

simultaneous_meteors = 1


# instantiate the beam
radarsystem = 'MU_radar'
antenna_pos = get_antenna_positions(radarsystem, requested_positions='req_ant_pos')
beam = calc_antenna_gain(radarsystem, antenna_positions=antenna_pos[0])[0]


def meteor_start():
    """ Iniciates the starting point of the meteor data of where the actual meteor observations start,
    should probably be moved to a more general location --> metecho.tools?
    """
    
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

    return IPP_n, DATA_n, start_values


def storage_arrays(IPP_n):
    """
    """

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

    return MUSIC_peaks, azimuth, elevation, k_vector, eigs, k_vector_out


def total_func(raw, I, DATA_n, IPP_n, beam, num, eigs, MUSIC_peaks, azimuth, elevation, k_vector):
    """ Total function for doa calculation. Implemented for mp
    """
    
    # calc R_matrix for I in loop
    R_matrix = calc_R_matrix(raw, I, DATA_n, IPP_n)

    # calc F-vals and k values
    F_vals_all, kx, ky = MUSIC_grid_search(R_matrix, beam, num)

    peaks_out, azimuth_out, elevation_out, k_vector_out = peak_finder(R_matrix, beam, F_vals_all, kx, ky)

    # Compute eigendecomposition of covariance matrix
    eigs_out, _ = np.linalg.eig(R_matrix)

    # Find r largest eigenvalues
    eigs_out = np.sort(eigs_out)[::-1]

    # store data in designated arrays
    eigs[:, I] = eigs_out
    MUSIC_peaks[I] = peaks_out
    azimuth[I] = azimuth_out
    elevation[I] = elevation_out

    # save k_vector output values in k_vector matrix, 1st=x, 2nd=y, 3th=z in loop
    for dim in range(0,3):
        k_vector[dim, I] = k_vector_out[dim, 0]

    return eigs_out, peaks_out, azimuth_out, elevation_out, k_vector_out 


def calc_doa(starting_point = None):
    """ Calcuated the doa --> k vectors and peaks
    Note to self: call function with non default input for starting values
    """

    #If user doesnt input their own meteor start values (from their own algorithm), use the default
    if starting_point == None: 
        # get start values
        IPP_n, DATA_n, start_values = meteor_start()
    else: 
        IPP_n, DATA_n, start_values = starting_point[0], starting_point[1], starting_point[2]

    # get storage arrays for further doa calculation
    MUSIC_peaks, azimuth, elevation, k_vector, eigs, k_vector_out = storage_arrays(IPP_n)

    # create empty list to store return values from mp function calls and define num
    input_args = []
    num = 200

    #for I in range(0, len(IPP_n) - 1):
    for I in range(0, 10 - 1):
        input_args.append((raw, I, DATA_n, IPP_n, beam, num, eigs, MUSIC_peaks, azimuth, elevation, k_vector))

    with mp.Pool(processes=8) as pool:

        results = pool.starmap(total_func, input_args)

        print('\n\nresults: ', [x.shape for x in results[8]])

        k_vector = results[0]
        MUSIC_peaks = results[1]

    print('\n\nk_vector: ', type(k_vector))


        # calc R_matrix for I in loop
        # R_matrix = calc_R_matrix(raw, I, DATA_n, IPP_n)


        # # make return dict for mp to have return statements from function call
        # manager = mp.Manager()
        # return_dict = manager.dict()

        # # create lock to that multiple processes don't do same action while working in paralel
        # lock = mp.Lock()

        # num = 200

        # p1 = mp.Process(target=MUSIC_grid_search, args=(R_matrix, beam, num, return_dict, lock))
        # p2 = mp.Process(target=MUSIC_grid_search, args=(R_matrix, beam, num, return_dict, lock))

        # p1.start()
        # p2.start()

        # p1.join()
        # p2.join()

        # F_vals_all = return_dict['F_vals']
        # kx = return_dict['kx']
        # ky = return_dict['ky']



    # calculate sample_range
    sample_range = k_vector * start_values

    # scale 3D axis to units of meters
    #######

    return k_vector, MUSIC_peaks, sample_range

k_vector, MUSIC_peaks, sample_range = calc_doa()


doa_example_data_file = pathlib.Path().home() / 'clones' / 'metecho_clone' / 'metecho' / 'src' / 'metecho' / 'data' /'doa_data_example.npy'

# save sample_range data for use in doa plotting example --> temp code
np.save(doa_example_data_file, sample_range)

metecho.profiler.stop('full')
print(metecho.profiler)

# plotting
fig = plt.figure()

ax = fig.add_subplot(projection='3d')

#plt.pcolormesh(kx[0,:], ky[:, 0], np.log10(np.abs(max_f_val_array)))
ax.scatter(sample_range[0, :], sample_range[1, :], sample_range[2, :])

plt.show()



## coherent integration








# Beamforming

## reg








## coherent integration








