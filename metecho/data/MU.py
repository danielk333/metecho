import numpy as np


def _get_header_data(fid):
    header_data = dict()

    # Copyright Csilla Szasz, Kenneth Kullbrandt, Daniel Kastinen
    """
    %-- Row 1 of the header
    %-- Reading the header of one record
    %-- (Byte position: 1-24) The first 6 numbers are integers,
    %-- four bytes long, each byte consisting of 8 bits -> each
    %-- integer is represented by 4x8=32 bits.
    """
    header_data["mu_head_1_to_24"] = np.fromfile(fid, dtype=np.int32, count=6)
    """

    %-- (25-32) The data taking program name is 8 bytes
    %-- -> 8x8=64 bits and is written in ASCII[sic] (the format is decoded with
    %-- UTF-8, so I must assume it is encoded as such).
    """
    header_data["program_name"] = _decode_utf(
        np.fromfile(fid, dtype='S8', count=1, offset=24))

    """
    %-- (33-56) Parameter file load time: 24 bytes, of characters: dd-mmm-yyyy hh:mm:ss(.ss?)
    """
    header_data["file_load_time"] = np.datetime64(_convert_date(
        np.fromfile(fid, dtype='S24', count=1, offset=32)), 'ns')

    """
    %-- (57-60) The data taking program number, 4 bytes -> 4*8=32 bits.
    """
    header_data["program_number"] = np.fromfile(
        fid, dtype=np.int32, count=1, offset=56)

    """
    %-- (61-84) Record start time: DD-MMM-YYYY hh:mm:ss.ss is 24 bytes long, each 8 bits
    """
    header_data["record_start_time"] = np.datetime64(_convert_date(
        np.fromfile(fid, dtype='S24', count=1, offset=60)), 'ns')

    """
    %-- (85-96) Record end time: hh:mm:ss.ss is 12 bytes long
    %-- Since "record_end_time" is only given in hh:mm:ss.ss, we want to use the 'dd-mmm-yyy ' part
    %-- of "record_start_time" to be able to convert recend into matlab serial date number.
    %-- To do this we need to convert it to a string and extract the first 10 symbsols and then
    %-- decode the rest from the file. After this we check so an edge case where the day rolled over
    %-- hasn't occured.
    """
    start_date = np.datetime_as_string(header_data["record_start_time"])[0:10]
    end_time = _decode_utf(np.fromfile(fid, dtype='S12', count=1, offset=84))
    temp_end_time = np.datetime64(start_date + " " + end_time, 'ns')
    header_data["record_end_time"] = _fix_date_edge_case(header_data["record_start_time"], temp_end_time)
    """
    %-- (97-172) The next 19 numbers are 4 byte integers, i.e. 4*8=32 bits long
    """
    header_data["mu_head_25_to_43"] = np.fromfile(fid, dtype=np.int32, count=19, offset=96)
    """
    %-- (173-256) The lag number of each ACF point is 21 unsigned longwords represented by 84 bytes,
    %-- i.e. each longword is 84/21=4 bytes of 8 bits each, i.e., the same thing as matlab's int32
    """

    header_data["lag_number_per_ACF"] = np.fromfile(fid, dtype=np.uint32, count=21, offset=172)
    """
    %-- (257-320) The beam direction number in first 16 beams is represented by 16 unsigned longwords
    %-- of 4 bytes and 4*8=32 bits each
    """

    header_data["beam_direction_number"] = np.fromfile(fid, dtype=np.uint32, count=16, offset=256)
    """
    %-- (321-336) The next 4 parameters are 4 byte, 4*8=32 bit, integers
    """
    header_data["mu_head_81_to_84"] = np.fromfile(fid, dtype=np.int32, count=4, offset=320)
    """
    %-- (337-344) The HP parameter file name is 8 bytes, i.e. 8*8=64 bits
    %-- cannot add characters to the 'head' matrix
    """

    header_data["hp_file_name"] = _decode_utf(np.fromfile(fid, dtype='S8', count=1, offset=336))
    """
    %-- (345-352) The next two parameters are 4 byte, i.e. 4*8=32 bit, integers
    """

    header_data["mu_head_87_to_88"] = np.fromfile(fid, dtype=np.int32, count=2, offset=344)
    """
    %-- (353-416) The number of sum (ACF method): 16 unsigned longwords -> 16 * 4 byte (4*8=32 bit) integers
    """

    header_data["number_of_sum_ACF"] = np.fromfile(fid, dtype=np.uint32, count=16, offset=352)
    """
    %-- (417-420) Number of sample poinst: 4 bytes = 32 bits
    """

    header_data["sample_points"] = np.fromfile(fid, dtype=np.int32, count=1, offset=416)
    """
    %-- (421-600) The next 180 bytes are empty, reserved for the future, so we step
    %-- (601-616) Observation parameter name: 16 bytes
    """

    header_data["observation_param_name"] = _decode_utf(np.fromfile(fid, dtype='S16', count=1, offset=600))
    """
    %-- (617-640) The next 6 parameters are 4 bytes (4*8=32bits) each
    """

    header_data["mu_head_155_to_160"] = np.fromfile(fid, dtype=np.int32, count=6, offset=616)
    """
    %-- (641-896) Transmitted pulse pattern: 32 bits * 64
    """

    header_data["transmitted_pulse_pattern"] = np.fromfile(fid, dtype=np.int32, count=64, offset=640)
    """
    %-- (897-904) The next 2 parameters are 4 bytes (4*8=32 bits) each
    """

    header_data["mu_head_224_to_225"] = np.fromfile(fid, dtype=np.int32, count=2, offset=896)
    """
    %-- (905-1160) Pulse decoding pattern for all channels: 32 bits * 64
    """

    header_data["pulse_decoding_patterns"] = np.fromfile(fid, dtype=np.int32, count=64, offset=904)
    """
    %-- (1161-1164) Beam stearing interval: 4 bytes (4*8=32 bits)
    """

    header_data["beam_stearing_interval"] = np.fromfile(fid, dtype=np.int32, count=1, offset=1160)
    """
    %-- (1165-1676) Beam direction: 2 bytes (2*8=16 bits) * 256
    %-- Cannot put this into the matrix - 256 numbers into 128 slots
    """

    header_data["beam_directions"] = np.fromfile(fid, dtype=np.int16, count=256, offset=1164)
    """
    %-- (1677-1696) The next 5 parameters are 4 bytes (2*8=32 bits) each
    """

    header_data["mu_head_420_to_424"] = np.fromfile(fid, dtype=np.int32, count=4, offset=1676)
    """
    %-- (1697-1716) TX frequency offset of 5 unsigned longwords -> 5 * 4 byte (4*8=32 bit) integers
    """

    header_data["tx_frequency"] = np.fromfile(fid, dtype=np.uint32, count=5, offset=1696)
    """
    %-- (1717-1724) The next 2 parameters are 4 bytes (2*8=32 bits) each
    """

    header_data["mu_head_430_to_431"] = np.fromfile(fid, dtype=np.int32, count=2, offset=1716)
    """
    %-- (1725-1740) The RX attenuator is 4 unsigned longwords -> 4 * 4 byte (4*8=32 bit) integers
    """

    header_data["rx_attentuator"] = np.fromfile(fid, dtype=np.uint32, count=4, offset=1724)
    """
    %-- (1741-1744) The state of the TX is given by a 4 byte (4*8=32 bit) integer
    """

    header_data["tx_state"] = np.fromfile(fid, dtype=np.int32, count=1, offset=1740)
    """
    %-- (1745-1760) The state of the RX is given by 4 unsigned longwords -> 4 * 4 byte (4*8=32 bit) integers
    """

    header_data["rx_state"] = np.fromfile(fid, dtype=np.uint32, count=4, offset=1744)
    """
    %-- (1761:1812) The RX module selection is given by 2 bytes * (25+1)
    %-- -> cannot be saved in the head matrix (no room for it)
    """

    header_data["rx_module_selection"] = np.fromfile(fid, dtype=np.int16, count=26, offset=1760)
    """
    %-- (1813:1820) The next 2 parameters are 4 bytes (2*8=32 bits) each
    """

    header_data["mu_head_454_to_455"] = np.fromfile(fid, dtype=np.int32, count=2, offset=1812)
    """
    %-- (1821-2844) The sample start time is represented by 256
    %-- unsigned longwords (unit of sub-pulse/4) -> 256 * 4 byte (4*8=32 bit) integer
    """

    header_data["sample_start_time"] = np.fromfile(fid, dtype=np.uint32, count=256, offset=1820)
    """
    %-- (2845-2848) The reception sequence: 4 byte (4*8=32 bit) integer
    """

    header_data["reception_sequence"] = np.fromfile(fid, dtype=np.int32, count=1, offset=2844)
    """
    %-- (2849-2964) The channel number in digital combine: 29 * 4 bytes (4*4=32 bits)
    """

    header_data["channel_number_digital"] = np.fromfile(fid, dtype=np.int32, count=29, offset=2848)
    """
    %-- (2965-3080) Number of coherent integrations for each combined channel:
    %-- 29 unsigned longwords -> 29 * 4 byte (4*8=32 bit) integers
    """

    header_data["coherent_integrations"] = np.fromfile(fid, dtype=np.uint32, count=29, offset=2964)
    """
    %-- (3081-3196) Number of FFT points for each combined channel:
    %-- 29 unsigned longwords -> 29 * 4 byte (4*8=32 bit) integers
    """

    header_data["fft_points"] = np.fromfile(fid, dtype=np.uint32, count=29, offset=3080)
    """
    %-- (3197-3312) Number of data points for each combined channel:
    %-- 29 unsigned longwords -> 29 * 4 byte (4*8=32 bit) integers
    """

    header_data["data_points"] = np.fromfile(fid, dtype=np.uint32, count=29, offset=3196)
    """
    %-- (3313-3428) Lower and upper boundary of FFT number in each combined channel:
    %-- 2 * 29 * 2 bytes (2*8=16 bits)
    """

    header_data["lo_hi_bound_fft"][0] = np.fromfile(fid, dtype=np.int16, count=58, offset=3312)
    """
    %-- (3429-3544) Lower and upper boundary of FFT number in each combined channel:
    %-- 2 * 29 * 2 bytes (2*8=16 bits)
    """

    header_data["lo_hi_bound_fft"][1] = np.fromfile(fid, dtype=np.int16, count=58, offset=3428)
    """
    %-- (3545-3660) Lower and upper boundary of FFT number in each combined channel:
    %-- 2 * 29 * 2 bytes (2*8=16 bits)
    """

    header_data["lo_hi_bound_fft"][2] = np.fromfile(fid, dtype=np.int16, count=58, offset=3544)
    """
    %-- The above numbers don't fit into the head matrix (58 numbers but 29 slots)
    %-- They are put into a matrix of their own: IFFT = [IFFT1  IFFT2  IFFT3]
    %-- (3661-3776) RX frequency offset for ach combined channel:
    %-- 29 unsigned longwords -> 29 * 4 byte (4*8=32 bit) integers
    """

    header_data["rx_frequency_offset"] = np.fromfile(fid, dtype=np.uint32, count=29, offset=3660)
    """
    %-- (3777-3808) FIR coefficient in RX: 16 * 2 bytes (2*8=16 bits)
    %-- Doesn't fit into the head matrix: 16 numbers into 8 slots...
    """

    header_data["fir_rx_coefficient"] = np.fromfile(fid, dtype=np.int16, count=16, offset=3776)
    """
    %-- (3809-3924) Gain adjustment of FIR filter in RX for each combined channel:
    %-- 29 * 2 bytes (2*8=16 bits each)
    %-- Cannot fit into the head matrix: 58 number into 29 slots
    """

    header_data["fir_rx_gain"] = np.fromfile(fid, dtype=np.int16, count=58, offset=3808)
    """
    %-- (3925-3940) The next four parameters are 4 bytes each, i.e. 4*8=32 bits
    """

    header_data["mu_head_982_to_985"] = np.fromfile(fid, dtype=np.int32, count=4, offset=3924)
    """
    %-- (3941-4056) Number of CIC filter in RX for each cmobined channel:
    %-- 29 unsigned longwords -> 29 * 4 byte (4*8=32 bit) integers
    """

    header_data["cic_rx_filter_amount"] = np.fromfile(fid, dtype=np.uint32, count=29, offset=3940)
    """
    %-- (4057-4172) CIC cropping rate in RX for each combined channel:
    %-- 29 unsigned longwords -> 29 * 4 byte (4*8=32 bit) integers
    """

    header_data["cic_rx_cropping_rate"] = np.fromfile(fid, dtype=np.uint32, count=29, offset=4056)
    """
    %-- (4173-4176) Above sea level:
    """

    header_data["above_sea_level"] = np.fromfile(fid, dtype=np.float32, count=1, offset=4172)
    """
    %-- (4177-4180) Header flag: 4 bytes, i.e., 4*8=32 bits
    """

    header_data["header_flag"] = np.fromfile(fid, dtype=np.int32, count=1, offset=4176)
    """
    %-- (4181-4260) Comment by user: 80 bytes (80*8=640 bits)
    """

    header_data["user_comment"] = _decode_utf(np.fromfile(fid, dtype='S80', count=1, offset=4180))
    """
    %-- (4261-4272) The next 3 parameters are 4 bytes (4*8=32 bits) each
    """

    header_data["mu_head_1066_to_1068"] = np.fromfile(fid, dtype=np.int32, count=3, offset=4260)
    """
    %-- (4273-4480) User header: 4480-4273+1 = 208 bytes
    """

    header_data["user_header"] = _decode_utf(np.fromfile(fid, dtype='S208', count=1, offset=4272))
    return header_data


# Converts a UCS-4 numpy ndarray into a UTF-8 python string.
# It first views it as a chararray to access the decode method,
# then squeezes it and converts it from a ndarray into a python string.
# After this, I remove the ' at the beginning and end of the string.
def _decode_utf(ucs_str):
    return np.array2string(ucs_str.view(np.chararray).decode('utf-8').squeeze())[1:-1]

# Since the datetimes involved are given in the form "DD-MMM-YYYY hh:mm:ss.ss"
# and numpy expects the form "YYYY-MM-DD hh:mm:ss.ss(...)", we must first convert
# the MU date to numpy standard format. This is accomplished with the help of the
# month dictionary and the _decode_utf function.


def _convert_date(date_str):
    if type(date_str) == np.ndarray:
        date_str = _decode_utf(date_str)
    return date_str[7:11] + "-" + month[date_str[3:6]] + "-" + date_str[0:2] + date_str[11:]


month = {
    "JAN": "01",
    "FEB": "02",
    "MAR": "03",
    "APR": "04",
    "MAY": "05",
    "JUN": "06",
    "JUL": "07",
    "AUG": "08",
    "SEP": "09",
    "OCT": "10",
    "NOV": "11",
    "DEC": "12"
}

# Checks so the date hasn't rolled over, and if it has it adds a day to the counter.


def _fix_date_edge_case(start_time, end_time):
    if end_time - start_time < 0:
        return end_time + np.timedelta64(1, 'D')
    return end_time

def convert_MUI_to_h5(in_path, out_path):

    header_data = _get_header_data(in_path)
    #
    #file.attrs['file_end_time'] = 0
    pass
