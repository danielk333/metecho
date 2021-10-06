#include <stdio.h>
#include <stdbool.h>
#include <complex.h>
#define decode_single(ipp, raw_data, size, ...) decode_single_base(ipp, raw_data, size, (struct input_data){.channel_decode = false, __VA_ARGS__ })
#define complex_size(...) sizeof(__VA_ARGS__)/2

struct input_data {
    bool channel_decode;
};

void decode_single_base(int ipp, complex *raw_data, int *size, struct input_data data){
    printf("%li\n", complex_size(raw_data));
};

int main() {
    complex testinput[] = {1.0 + 3.0 * I, 5.0 + 2.0 * I, 3.0 + 6.0 * I, 4.0 + 4.0 * I};
    int sizeinput[] = {5, 5, 2, 3};
    int ipp = 1337;
    decode_single(ipp, testinput, sizeinput, .channel_decode=true);
    return 0;
};