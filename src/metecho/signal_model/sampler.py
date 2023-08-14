def impulse_sampling(signal, impulse_response):
    """Impulse digital sampling using a impulse response envelope, 
    decimation does not integrate the signal.
    """
    return impulse_response(signal)


def integrated_sampling(signal, impulse_response):
    """Intgrated signal sampling summing impulse samples modified by the 
    impulse response envelope to reduce to the requested decimation rate.
    """
    return sum(impulse_response(signal))
