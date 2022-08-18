#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <complex.h>
#include <math.h>
#include <time.h>
#include <assert.h>
#include <float.h>
#include "libdoa.h"


void 
MUSIC_model_func(
    precision complex* (*model_ptr)(double*), 
    precision complex *noise_space
)
{

/*F_vals[xi, yi] = (a.T @ a) / (a.T @ Qn @ Qn.T @ a)*/

}