#include <stdio.h>
#include <stdbool.h>
#include "hdf5.h"
#include "hdf5_hl.h"
/* Macro for making Keyword Arguments possible */
#define decode_single(h5_file_path, ...) decode_single_base(h5_file_path, (struct input_data){.channel_decode = false, __VA_ARGS__ })

struct input_data {
    bool channel_decode;
};

void decode_single_base(char *h5_file_path, struct input_data data){
    hid_t           file; /* File identifier */
    herr_t          status;

    /* Opens the h5 file in Read Only mode. */
    file = H5Fcreate(h5_file_path, H5F_ACC_RDONLY, H5P_DEFAULT, H5P_DEFAULT);
    /* Closes the file. */
    status = H5Fclose(file);

}

int main() {
    decode_single("/mnt/e/Kurser/X7007E/data/2009/06/27/2009-06-27T09.54.05.690000000.h5", .channel_decode=true);
    return 0;
}