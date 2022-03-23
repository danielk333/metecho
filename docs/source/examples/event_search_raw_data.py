'''
Searching for meteor events
============================
'''

import pathlib

import metecho

try:
    HERE = pathlib.Path(__file__).parent.resolve()
except NameError:
    HERE = pathlib.Path('.').parent.resolve()

metecho.debug()

h5_mu_file = HERE / 'data' / 'MU_h5' / '2009' / '06' / '27' / '2009-06-27T09.54.05.690000000.h5'

raw = metecho.data.RawDataInterface(h5_mu_file)

config = metecho.events.generate_event_search_config()
signal = metecho.generalized_matched_filter.signal_model.barker_code_13(raw.data.shape[raw.axis['pulse']], 2)
events, nonhead, best_data, noise = metecho.events.search(raw, config, None, signal)

print(metecho.profiler)
