#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <complex.h>
#include <math.h>
#define decode_single(ipp, raw_data, size, bits, samp, code, code_size, ampsum, f,...) \
    decode_single_base(ipp, raw_data, size, bits, samp, code, code_size, ampsum, f, (struct input_data){.channel_decode = false, __VA_ARGS__ })
#define precision double

void combine_precisions_to_complex(precision *realarray, precision *imagarray, int size, complex *outarray);
void multiply_precision_array_with_precision_array(precision *inarray, precision *multarray, int size, precision *outarray);
void multiply_array_with_precision(precision *inarray, int size, precision multiplicator, precision *outarray);
void int_array_to_precision(int *inarray, int size, precision *outarray);
void apply_func_on_array(precision *inarray, int insize, precision (*fun)(precision), precision *outarray);
void range_array_multiply(int size, precision multiplicator, precision *outarray);
void arange(int start, int stop, int step, precision *outarray);
void calc_VEL(precision *inarray, int insize, int multiplicator, int divider, precision *outarray);
void wrap(precision *array_before,
            int size_before,
            precision *array_between,
            int size_between,
            precision *array_after,
            int size_after,
            precision *outarray);

struct input_data {
    bool channel_decode;
};

void decode_single_base(int *ipp, 
                        precision complex **raw_data, 
                        int *raw_data_size, 
                        int bits,
                        precision samp,
                        precision *code,
                        int code_size,
                        precision complex *ampsum,
                        precision f,
                        struct input_data data){

    int STEP = 1000;
    int SPEED_OF_LIGHT = 299792458;
    int DFVAR_SIZE = (35000/STEP)+1;
    //int CODE28_SIZE = code_size + 2;
    //int **decpow;
    //int *compratio;
    //int *maxpowind;

    precision ZERO[] = {0.0};
    int ZERO_SIZE = sizeof(ZERO)/sizeof(precision);
    precision DFVAR[DFVAR_SIZE];
    precision *CODE28 = malloc((code_size + 2) * sizeof(precision));
    precision *CODE27 = code;
    precision VEL[DFVAR_SIZE];
    precision VV1[4] = {0, 0.25, 0.5, 0.75};

    //int_array_to_precision(code, code_size, CODE27);
    wrap(ZERO, ZERO_SIZE, code, code_size, ZERO, ZERO_SIZE, CODE28);
    arange(-30000, 5000, STEP, DFVAR);
    calc_VEL(DFVAR, DFVAR_SIZE, SPEED_OF_LIGHT, 2*f, VEL);



   
    for (int i = 0; i < DFVAR_SIZE; ++i)
    {
        precision *dfvar_samp = malloc(code_size*sizeof(precision));
        precision *cos_sum = malloc(code_size*sizeof(precision));
        precision *sine_sum = malloc(code_size*sizeof(precision));
        precision complex *dfvarcode = malloc(sizeof(complex)*code_size);
        range_array_multiply(code_size, 2*M_PI*DFVAR[i]*samp, dfvar_samp);
        apply_func_on_array(dfvar_samp, code_size, cos, cos_sum);
        multiply_precision_array_with_precision_array(CODE27, cos_sum, code_size, cos_sum);
        apply_func_on_array(dfvar_samp, code_size, sin, sine_sum);
        combine_precisions_to_complex(cos_sum, sine_sum, code_size, dfvarcode);
        free(dfvar_samp);
        free(cos_sum);
        free(sine_sum);
        free(dfvarcode);
        
    }
    free(CODE28);

};



void combine_precisions_to_complex(precision *realarray, precision *imagarray, int size, complex *outarray){
    for (int i = 0; i < size; ++i)
    {
        outarray[i] = realarray[i] + imagarray[i] * I;
    }
}

void multiply_precision_array_with_precision_array(precision *inarray, precision *multarray, int size, precision *outarray){
    for (int i = 0; i < size; ++i)
    {
        outarray[i] = inarray[i] * multarray[i];
    }
}

void multiply_array_with_precision(precision *inarray, int size, precision multiplicator, precision *outarray){
    for (int i = 0; i < size; ++i)
    {
        outarray[i] = inarray[i] * multiplicator; 
    }
}

void int_array_to_precision(int *inarray, int size, precision *outarray){
    for (int i = 0; i < size; ++i)
    {
        outarray[i] = (precision)inarray[i];
    }
}

void range_array_multiply(int size, precision multiplicator, precision *outarray){
    for (int i = 0; i < size; ++i)
    {
        outarray[i] = (precision)multiplicator*(i+1);
    }
}
void apply_func_on_array(precision *inarray, int insize, precision (*fun)(precision), precision *outarray){
    for (int i = 0; i < insize; ++i)
    {
        outarray[i] = (*fun)(inarray[i]);
    }
}

// "wraps" an array between two others and stores them in outarray
void wrap(  precision *array_before,
            int size_before,
            precision *array_between,
            int size_between,
            precision *array_after,
            int size_after,
            precision *outarray){
    memcpy(outarray, array_before, size_before*sizeof(precision));
    memcpy(outarray + size_before, array_between, size_between*sizeof(precision));
    memcpy(outarray + size_before + size_between, array_after, size_after*sizeof(precision));
}

// takes a start and an end and creates an array with 
// steps size between them and stores it in outarray
void arange(int start, int end, int step, precision *outarray){
    int counter = 0;
    for (int i = start; i < (end+step); i+=step)
    {
        outarray[counter] = (float)i;
        counter++;
    }
}
// calculates the velocity given the formula vel = dfvar*constants.c / (2*radar.f)
void calc_VEL(precision *inarray, int insize, int multiplicator, int divider, precision *outarray){
    for (int i = 0; i < insize; ++i)
    {
        outarray[i] = inarray[i]*(multiplicator/divider);
    }
}



int main() {
    int ipp[] = {1337, 420, 69};
    int sizeinput[] = {4, 4};
    precision complex **testinput;
    testinput = malloc(sizeof(precision) * sizeinput[0] * sizeinput[1]);
    if (testinput) {
        for (int i = 0; i < sizeinput[0]; ++i)
        {
            testinput[i] = malloc( sizeof *testinput[i] * sizeinput[1]);
            for (int j = 0; j < sizeinput[1]; ++j)
            {
                testinput[i][j] = (precision)(i+j+1) + (precision)(j*j) * I;
            }
        }
    }
    int bits = 8;
    precision t_samp = 12.0;
    precision code[] = {3.0, 5.0, 7.0, 9.0, 1.0, 23.0, 4.0, 26.0, 10.0, 11.0};
    int code_size = sizeof(code)/sizeof(precision);
    precision complex ampsum[] = {1.0 + 2.0 * I, 2.0 + 3.0 * I};
    precision f = 45000000.0;

    decode_single(ipp, testinput, sizeinput, bits, t_samp, code, code_size, ampsum, f, .channel_decode=true);
    free(testinput);
    return 0;
};