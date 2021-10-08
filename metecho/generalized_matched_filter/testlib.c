#include <stdio.h>
#include <complex.h>

void myprint(float, float);

void myprint(float coolstuff_real, float coolstuff_imag)
{
    complex coolstuff = coolstuff_real + coolstuff_imag * I;
    printf("Read: %f\nImag: %f\n", creal(coolstuff), cimag(coolstuff));
}