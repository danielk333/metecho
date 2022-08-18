// inclusion guard
#ifndef DOA_H_
#define DOA_H_
#define precision double

void MUSIC_model_func(precision complex* (*model_ptr)(double*), precision complex *noise_space);

#endif // DOA_H_