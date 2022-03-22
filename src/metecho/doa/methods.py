# python stuff


# MUSIC

## reg

indecies = ~isnan(meteor.start_index); 
    
IPP_n = meteor.ipp(indecies);
DATA_n = floor(meteor.start_index(indecies));

MUSIC_peaks = zeros(length(IPP_n),simultaneous_meteors)*NaN
azimuth = zeros(length(IPP_n),simultaneous_meteors)*NaN
elevation = zeros(length(IPP_n),simultaneous_meteors)*NaN
k_vector = zeros(3, length(IPP_n),simultaneous_meteors)*NaN
eigs = zeros(raw_data.radar.beam.channels, length(IPP_n))*NaN

# IPP / R-matrix func
def MUSIC_IPP(raw_data, I, DATA_n, IPP_n, p):
    """ Calculates R-matrix

    """


    nhigh = size(raw_data.amp3,2)
    
    select_range_gates = DATA_n(I):(DATA_n(I)+raw_data.radar.encoding.Bits)
    if select_range_gates(end) > nhigh:
        select_range_gates(select_range_gates > nhigh) = []
    end

    amp3_subset = squeeze(raw_data.amp3(:, select_range_gates, IPP_n(I)))

    R_matrix = (amp3_subset*amp3_subset')./size(amp3_subset,1)
    

    return peaks_out, azimuth_out, elevation_out, k_vector_out, eig_out







## coherent integration








# Beamforming

## reg








## coherent integration








