// inclusion guard
#ifndef BARKER_XCORR_ECHO_SEARCH_H_
#define BARKER_XCORR_ECHO_SEARCH_H_
#define precision double

void arange(precision start, precision stop, precision step, precision *outarray);
void elementwise_cabs(precision complex *inarray, int start, int stop, precision complex *outarray);
void crosscorrelate_single_delay(precision complex *x, int size_x, precision complex *y, int size_y, int delay, precision complex *result);
void crosscorrelate(precision complex *x, int size_x, precision complex *y, int size_y, int min_delay, int max_delay, precision complex *result);
void max_in_array(precision complex *inarray, int size, precision complex *maxval, int *maxvalindex);
void set_norm_coefs(precision complex abs_signal_samples_sum, int start, int stop, precision complex *outarray);
precision complex complex_sum(precision complex *inarray, int size);

void perform_xcorr( precision complex *signal_samples,
                    int signal_samples_size,
                    precision *doppler_freq,
                    int doppler_freq_size,
                    precision *code,
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
                        precision complex *signal_samples,
                        int signal_samples_size,
                        precision *code,
                        int code_size,
                        precision complex *pows,
                        int *pows_size,
                        precision complex *powmax,
                        int powmax_size,
                        int *maxpowind,
                        int maxpowind_size,
                        precision samp
                        );

#endif // BARKER_XCORR_ECHO_SEARCH_H_