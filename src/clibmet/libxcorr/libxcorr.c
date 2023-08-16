#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <complex.h>
#include <math.h>
#include <time.h>
#include <assert.h>
#include <float.h>
#include "libxcorr.h"



void xcorr_echo_search(
    precision doppler_freq_min,
    precision doppler_freq_max,
    precision doppler_freq_step,
    precision complex *signal_samples,
    int signal_samples_size,
    precision *code,
    int code_size,
    precision complex *pows,
    precision complex *pows_normalized,
    int *pows_size,
    precision complex *powmax,
    int powmax_size,
    int *maxpowind,
    int maxpowind_size,
    precision samp
    ){

    // Declaring constants
    int doppler_freq_size = (int)((doppler_freq_max - doppler_freq_min) / (doppler_freq_step) + 1);
    
    precision doppler_freq[doppler_freq_size];

    arange(doppler_freq_min, doppler_freq_max, doppler_freq_step, doppler_freq);

    perform_xcorr(
        signal_samples,
        signal_samples_size,
        doppler_freq,
        doppler_freq_size,
        code,
        code_size,
        pows,
        pows_normalized,
        pows_size,
        powmax,
        powmax_size,
        maxpowind,
        maxpowind_size,
        samp
    );
}

void perform_xcorr(
        precision complex *signal_samples,
        int signal_samples_size,
        precision *doppler_freq,
        int doppler_freq_size,
        precision *code,
        int code_size,
        precision complex *pows,
        precision complex *pows_normalized,
        int *pows_size,
        precision complex *powmax,
        int powmax_size,
        int *maxpowind,
        int maxpowind_size,
        precision samp
    ){

    // Initiate variables
    int decoded_size = signal_samples_size + code_size;
    precision complex norm_coefs[decoded_size];
    precision complex abs_signal_samples[code_size];
    precision complex output_power[decoded_size];
    precision doppler_freq_samp;
    precision complex signal_model[code_size];
    precision complex decoded[decoded_size];
    precision complex signal_model_abs_arr[code_size];
    precision complex abs_signal_samples_sum;

    // Setting arrays to zeroes
    memset(pows, (precision complex)0, (size_t)(pows_size[0]*pows_size[1]));
    memset(pows_normalized, (precision complex)0, (size_t)(pows_size[0]*pows_size[1]));
    memset(powmax, (precision complex)0, (size_t)powmax_size);
    memset(maxpowind, (int)0, (size_t)maxpowind_size);
    memset(norm_coefs, (precision complex)0, (size_t)decoded_size);


     // Calculate the absolute value complex_sum of the signal_samples from 0 to code_size 
    for (int i = code_size; i < signal_samples_size+code_size; i++)
    {
        elementwise_cabs_square(signal_samples, i-code_size, i, abs_signal_samples);
        abs_signal_samples_sum = complex_sum(abs_signal_samples, code_size);
        norm_coefs[i] = abs_signal_samples_sum;
    }
    elementwise_cabs_square(signal_samples, 0, code_size, abs_signal_samples);
    abs_signal_samples_sum = complex_sum(abs_signal_samples, code_size);
    set_norm_coefs(&abs_signal_samples_sum, 0, code_size, norm_coefs);
    
    elementwise_cabs_square(signal_samples, signal_samples_size-code_size, signal_samples_size, abs_signal_samples);
    abs_signal_samples_sum = complex_sum(abs_signal_samples, code_size);
    set_norm_coefs(&abs_signal_samples_sum, signal_samples_size, signal_samples_size+code_size, norm_coefs);
    
    for (int i = 0; i < doppler_freq_size; i++)
    {
        for (int j = 0; j < code_size; j++)
        {
            doppler_freq_samp = (j+1)*2*M_PI*doppler_freq[i]*samp;
            signal_model[j] = (sin(doppler_freq_samp) * I  + cos(doppler_freq_samp)) * code[j];
        }

        elementwise_cabs_square(signal_model, 0, code_size, signal_model_abs_arr);
        precision complex signal_model_abs_sum = complex_sum(signal_model_abs_arr, code_size);

        crosscorrelate(signal_samples, signal_samples_size, signal_model, code_size, -signal_samples_size, code_size, decoded);

        for (int j = 0; j < decoded_size; j++)
        {
            if (cabs(norm_coefs[j]) < FLT_EPSILON)
            {
                norm_coefs[j] = 1;
            }
            output_power[j] = decoded[j]/(sqrt(norm_coefs[j])*sqrt(signal_model_abs_sum));
            output_power[j] = cpow(cabs(output_power[j]), 2);
                        
            if (cabs(output_power[j]) > cabs(powmax[i])){
                powmax[i] = output_power[j];
                maxpowind[i] = j;
            }
        }
        maxpowind[i] = maxpowind[i] - code_size;
        for (int j = 0; j < decoded_size; j++)
        {
            pows_normalized[i*decoded_size+j] = output_power[j];
            pows[i*decoded_size+j] = decoded[j];
        }          
    }

}



void crosscorrelate(precision complex *x, int size_x, precision complex *y, int size_y, int min_delay, int max_delay, precision complex *result){
    assert(max_delay > min_delay);
    int count = 0;
    for (int i = max_delay; i > min_delay; i--)
    {
        crosscorrelate_single_delay(x, size_x, y, size_y, i, &result[count]);
        count++;
    }
}

void crosscorrelate_single_delay(precision complex *x, int size_x, precision complex *y, int size_y, int delay, precision complex *result){
    
    precision complex correlation = 0.0 + 0.0 * I;

    for (int i=0; i < size_x; i++) {
        int j = i + delay;
        if (j < 0 || j >= size_y){
            correlation += 0.0 + 0.0 * I;
        }
        else{

            correlation += x[i] * conj(y[j]);
        }
    }
    *result = correlation;
}

// Sets the value of abs_signal_samples_sum from start to stop on outarray
void set_norm_coefs(precision complex *abs_signal_samples_sum, int start, int stop, precision complex *outarray){
    for (int i = start; i < stop; i++)
    {
        outarray[i] = abs_signal_samples_sum[0];
    }
}

precision complex complex_sum(precision complex *inarray, int size){
    precision complex rv = 0.0 + 0.0 * I;
    for (int i = 0; i < size; i++)
    {
        rv += inarray[i];
    }
    return rv;
}

void elementwise_cabs_square(precision complex *inarray, int start, int stop, precision complex *outarray){
    int temp = 0;
    for (int i = start; i < stop; i++)
    {
        outarray[temp] = inarray[i]*conj(inarray[i]);
        temp++;       
    }
}

// takes a start and an end and creates an array with 
// steps size between them and stores it in outarray
void arange(precision start, precision end, precision step, precision *outarray){
    int counter = 0;
    for (precision i = start; i < (end+step); i+=step)
    {
        outarray[counter] = i;
        counter++;
    }
}
