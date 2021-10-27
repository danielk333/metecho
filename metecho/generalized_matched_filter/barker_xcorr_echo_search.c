#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <complex.h>
#include <math.h>
#include <time.h>
#define precision double


//precision complex* get_complex_number(int *size);
void arange(int start, int stop, int step, precision *outarray);
void complex_absolute_array(precision complex *inarray, int start, int stop, precision complex *outarray);
void crosscorrelate(precision complex *x, int size_x, precision complex *y, int size_y, int delay, precision complex *result);
void crosscorrelate_array(precision complex *x, int size_x, precision complex *y, int size_y, int min_delay, int max_delay, precision complex *result);
void max_in_array(precision complex *inarray, int size, precision complex *maxval, int *maxvalindex);
void set_abs_ampsum(precision complex abs_ampsum_sum, int start, int stop, precision complex *outarray);
precision complex complex_sum(precision complex *inarray, int size);

/*
precision complex* get_complex_number(int *size){
    precision complex *outarray;
    outarray = (precision complex*)malloc(size[0]*size[1]*sizeof(precision complex));
    for (int i = 0; i < size[0]; ++i)
    {
        for (int j = 0; j < size[1]; ++j)
        {
            precision u1 = (precision)(rand()%100)/100;
            precision u2 = (precision)(rand()%100)/100;
            outarray[i*size[0] + j] = u1 + u2 * I;

        }
    }
    return outarray;
}
*/
void perform_xcorr( precision complex *ampsum,
                    int ampsum_size, 
                    precision *DFVAR, 
                    int DFVAR_SIZE, 
                    precision *CODE27, 
                    int code_size,
                    precision complex *pows,
                    int *pows_size,
                    precision complex *powmax,
                    int powmax_size,
                    int *maxpowind,
                    int maxpowind_size,
                    precision samp
                    );


void barker_xcorr_echo_search(
                        precision complex *ampsum,
                        int ampsum_size,
                        precision *code,
                        int code_size,
                        precision complex *pows,
                        int *pows_size,
                        precision complex *powmax,
                        int powmax_size,
                        int *maxpowind,
                        int maxpowind_size,
                        precision samp
                        ){

    // Declaring constants
    int STEP = 100;
    int DFVAR_SIZE = (35000/STEP)+1;
    
    precision DFVAR[DFVAR_SIZE];
    precision *CODE27 = code;
        
    // Declaring variables
    precision bestpeak[ampsum_size];
    precision best_dop[ampsum_size];
    precision best_start[ampsum_size];

    arange(-30000, 5000, STEP, DFVAR);

    perform_xcorr(  ampsum, 
                    ampsum_size, 
                    DFVAR, 
                    DFVAR_SIZE, 
                    CODE27, 
                    code_size, 
                    pows, 
                    pows_size, 
                    powmax, 
                    powmax_size, 
                    maxpowind, 
                    maxpowind_size,
                    samp);

}

void perform_xcorr( precision complex *ampsum,
                    int ampsum_size, 
                    precision *DFVAR, 
                    int DFVAR_SIZE, 
                    precision *CODE27, 
                    int code_size,
                    precision complex *pows,
                    int *pows_size,
                    precision complex *powmax,
                    int powmax_size,
                    int *maxpowind,
                    int maxpowind_size,
                    precision samp
                    ){
    precision complex norm_coefs[ampsum_size+code_size];
    precision complex abs_ampsum[ampsum_size];
    precision complex decpow[ampsum_size+code_size];
    int norm_coefs_size = ampsum_size+code_size;
    int decpow_size = ampsum_size+code_size;
    
    // Setting arrays to zeroes
    memset(pows, (precision)0, sizeof(pows[0])*pows_size[0]*pows_size[1]);
    memset(powmax, (precision)0, sizeof(powmax[0])*powmax_size);
    memset(maxpowind, (int)0, sizeof(maxpowind[0])*maxpowind_size);
    memset(norm_coefs, (precision)0, sizeof(norm_coefs_size)*norm_coefs[0]);


     // Calculate the absolute value complex_sum of the ampsum from 0 to L
    complex_absolute_array(ampsum, 0, code_size, abs_ampsum);
    precision complex abs_ampsum_sum = complex_sum(abs_ampsum, code_size);
    set_abs_ampsum(abs_ampsum_sum, 0, code_size, norm_coefs);
    for (int i = code_size; i < ampsum_size; i++)
    {
        complex_absolute_array(ampsum, i-code_size, i, abs_ampsum);
        abs_ampsum_sum = complex_sum(abs_ampsum, code_size);
        norm_coefs[i] = abs_ampsum_sum;
    }
    complex_absolute_array(ampsum, ampsum_size-code_size, ampsum_size, abs_ampsum);
    abs_ampsum_sum = complex_sum(abs_ampsum, code_size);
    set_abs_ampsum(abs_ampsum_sum, ampsum_size, ampsum_size+code_size, norm_coefs);
    
    for (int i = 0; i < DFVAR_SIZE; i++)
    {
        
        precision dfvar_samp;
        int dfvarcode_size = code_size;
        precision complex dfvarcode[dfvarcode_size];
        int decoded_size = dfvarcode_size + ampsum_size;
        precision complex decoded[decoded_size];

        for (int j = 0; j < code_size; j++)
        {
            dfvar_samp = (j+1)*2*M_PI*DFVAR[i]*samp;
            dfvarcode[j] = (sin(dfvar_samp) * I  + cos(dfvar_samp)) * CODE27[j];
        }

        precision complex dfvar_abs_arr[dfvarcode_size];
        complex_absolute_array(dfvarcode, 0, dfvarcode_size, dfvar_abs_arr);
        precision complex dfvar_abs_sum = complex_sum(dfvar_abs_arr, dfvarcode_size);

        for (int k = 0; k < dfvarcode_size; k++)
        {
            dfvarcode[k] = dfvarcode[k]/sqrt(dfvar_abs_sum);
        }

        crosscorrelate_array(ampsum, ampsum_size, dfvarcode, dfvarcode_size, -ampsum_size, dfvarcode_size, decoded);
        for (int j = 0; j < decoded_size; j++)
        {
            if (norm_coefs[j] == 0)
            {
                norm_coefs[j] = 1;
            }
            decpow[j] = decoded[j]/sqrt(norm_coefs[j]);
            decpow[j] = cpow(cabs(decpow[j]), 2);

            if (cabs(decpow[j]) > cabs(powmax[i])){                
                powmax[i] = decpow[j];
                maxpowind[i] = j;
            }
        }
        maxpowind[i] = maxpowind[i] - code_size;
        for (int j = 0; j < decpow_size; j++)
        {
            pows[i*decpow_size+j] = decpow[j];
        }          
    }

}

void crosscorrelate_array(precision complex *x, int size_x, precision complex *y, int size_y, int min_delay, int max_delay, precision complex *result){
    if (max_delay < min_delay)
    {
        printf("max delay less than min delay, exiting.");
        return;
    }
    int count = 0;
    for (int i = max_delay; i > min_delay; i--)
    {
        crosscorrelate(x, size_x, y, size_y, i, &result[count]);
        if (cabs(result[count]) == 22)
        {
            printf("result[%d] == 22 at delay %d\n", count, i);
        }
        count++;
    }
}

void crosscorrelate(precision complex *x, int size_x, precision complex *y, int size_y, int delay, precision complex *result){
    
    precision complex correlation = 0.0 + 0.0 * I;

    for (int i=0; i < size_x; i++) {
        int j = i - delay;
        if (j < 0 || j >= size_y){
            correlation += 0.0 + 0.0 * I;
        }
        else{
            correlation += x[i] * y[j];
        }
    }
    *result = correlation;
}

// Sets the value of abs_ampsum_sum from start to stop on outarray
void set_abs_ampsum(precision complex abs_ampsum_sum, int start, int stop, precision complex *outarray){
    for (int i = start; i < stop; i++)
    {
        outarray[i] = abs_ampsum_sum;
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

void complex_absolute_array(precision complex *inarray, int start, int stop, precision complex *outarray){
    int temp = 0;
    for (int i = start; i < stop; i++)
    {
        outarray[temp] = cabs(inarray[i]);
        temp++;       
    }
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
