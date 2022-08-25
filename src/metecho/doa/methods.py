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
from metecho import tools

import copy

# numpy option to print full numpy array instead of truncation
np.set_printoptions(threshold=sys.maxsize)


# profiler stuff

# init profiler
metecho.profiler.init('IPP_and_storage', True)
metecho.profiler.init('input_args_appending', True)
metecho.profiler.init('mp_calculations', True)
metecho.profiler.init('trajectory_and_spacial_units_scaling', True)
metecho.profiler.init('mp_launch', True)

metecho.profiler.init('full', True)
metecho.profiler.start('full')
metecho.profiler.enable('')


# MUSIC

## reg

h5_mu_file = pathlib.Path().home() / 'clones' / 'metecho_clone' / 'metecho' / 'docs' / 'source' / 'examples' / 'data' / 'MU_h5' / '2009' / '06' / '27' / '2009-06-27T09.54.05.690000000.h5'

raw = metecho.data.RawDataInterface(h5_mu_file)
raw_data = raw.data

print('\n\nraw_type: ', type(raw))

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

@tools.profiling.timeing(f'{__name__}')
def total_func(all_inds, child_conn, raw, DATA_n, IPP_n, beam, num):
    """ Total function for doa calculation. Implemented for mp
    """

    # create empty lists to store result values from this process's inds chunk
    eigs_out_list = []
    peaks_out_list = []
    azimuth_out_list = []
    elevation_out_list = []
    k_vector_out_list = []

    for I in all_inds:
    
        # calc R_matrix for I in loop
        R_matrix = calc_R_matrix(raw, I, DATA_n, IPP_n)

        # calc F-vals and k values
        F_vals_all, kx, ky = MUSIC_grid_search(R_matrix, beam, num)

        peaks_out, azimuth_out, elevation_out, k_vector_out = peak_finder(R_matrix, beam, F_vals_all, kx, ky)

        # Compute eigendecomposition of covariance matrix
        eigs_out, _ = np.linalg.eig(R_matrix)

        # Find r largest eigenvalues
        eigs_out = np.sort(eigs_out)[::-1]

        # start profiler
        metecho.profiler.start('input_args_appending')

        # append result values to lists
        eigs_out_list.append(eigs_out)
        peaks_out_list.append(peaks_out)
        azimuth_out_list.append(azimuth_out)
        elevation_out_list.append(elevation_out)
        k_vector_out_list.append(k_vector_out)

        # stop profiler
        metecho.profiler.stop('input_args_appending')

    child_conn.send((eigs_out_list, peaks_out_list, azimuth_out_list, elevation_out_list, k_vector_out_list))

    #return eigs_out, peaks_out, azimuth_out, elevation_out, k_vector_out

def calc_doa(raw, starting_point = None):
    """ Calcuated the doa --> k vectors and peaks
    Note to self: call function with non default input for starting values
    """

    # profiler stuff
    metecho.profiler.start('IPP_and_storage')

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

    all_inds = list(range(len(IPP_n)))
    all_peaks_out = np.empty(len(all_inds), dtype=np.float64)
    all_azimuth_out = np.empty(len(all_inds), dtype=np.float64)
    all_elevation_out = np.empty(len(all_inds), dtype=np.float64)
    all_k_vector = np.ndarray([3, len(all_inds)], dtype=np.float64)
    all_eigs_out = np.full(shape=(raw.data.shape[raw.axis['channel']], len(IPP_n)), fill_value=np.NaN)

    # stop profiler
    metecho.profiler.stop('IPP_and_storage')


    # start profiler
    metecho.profiler.start('mp_calculations')

    # define empty temp storage for processes and pipes
    cores = 8
    processes = []
    pipes = []

    # start profiler
    metecho.profiler.start('mp_launch')

    # for mpi impl. no for-loop needed here
    for core in range(cores):

        # make copies of input args -> ask lars-hendrick
        #raw_copy = copy.deepcopy(raw)   # dont work

        parent_conn, child_conn = mp.Pipe()
        p = mp.Process(target=total_func, args=(all_inds[core::cores], child_conn, raw, DATA_n, IPP_n, beam, num))
        processes.append(p)

        # pipe to parent
        pipes.append(parent_conn)

    # start stuff
    for p in processes:
        p.start()

    # stop profiler
    metecho.profiler.stop('mp_launch')

    # all running
    # wait for done


    for p, pipe, core in zip(processes, pipes, range(cores)):

        eigs_out_list, peaks_out_list, azimuth_out_list, elevation_out_list, k_vector_out_list = pipe.recv()
        p.join()

        for I, eigs, peaks, azimuth, elevation, k_vector in zip(all_inds[core::cores], eigs_out_list, peaks_out_list, azimuth_out_list, elevation_out_list, k_vector_out_list):

            all_eigs_out[:,I] = eigs
            all_peaks_out[I] = peaks
            all_azimuth_out[I] = azimuth
            all_elevation_out[I] = elevation

            for dim in range(0,3):
                all_k_vector[dim, I] = k_vector[dim]

    # stop profiler
    metecho.profiler.stop('mp_calculations')


    # start profiler
    metecho.profiler.start('trajectory_and_spacial_units_scaling')

    # calculate sample_range
    sample_range = all_k_vector * start_values

    # stop profiler
    metecho.profiler.stop('trajectory_and_spacial_units_scaling')

    return all_k_vector, all_peaks_out, sample_range


k_vector, MUSIC_peaks, sample_range = calc_doa(raw)

# stop MPI right here

# id of process is called rank of process --> acces by   comm.rank

# if comm.rank != 0:
#     exit()


doa_example_data_file = pathlib.Path().home() / 'clones' / 'metecho_clone' / 'metecho' / 'src' / 'metecho' / 'data' /'doa_data_example.npy'

# save sample_range data for use in doa plotting example --> temp code
np.save(doa_example_data_file, sample_range)

# stop metecho_frofiler_full and print in output
metecho.profiler.stop('full')
print(metecho.profiler)


# plotting
fig = plt.figure()

ax = fig.add_subplot(projection='3d')

ax.scatter(sample_range[0, :], sample_range[1, :], sample_range[2, :])

plt.show()



## coherent integration

# dude its actually so sad that i cant even implement this --> think about
# doing extra work in summer after finishing report and france visit.






# Beamforming

## reg








## coherent integration








