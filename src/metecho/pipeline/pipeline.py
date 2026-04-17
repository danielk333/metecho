# STEP 0 - whole dataset
# get data
# run event search

# STEP 1 - per event
# Target Estimation (TODO: estimate phase) (kolla matlab kod estimare inte differans!)
# Direction of arrival

# STEP 2 - whole dataset
# Calibration

# STEP 3 - per event
# Model estimation
# first step take least square
#
# later - run hardtarget simulator to get uncertainties that can be used for e.g SCAM.
# Check with Daniel if his Jacobian magic works.
#
#
# sensor modell -> range, dopppler velocity, phase (difference) as a function of time
#
# Estimera start värde för least squared (kolla mu analysis för inspo, kollar på doa+ target estimation för att estimera en "trajectory ish")
# matlab/+pipeline/+MU/analyse_event:calculate_trajectory
#
# Optimization_func = least_squared,
# output från ablate kör igenom sensor model funktionen
# kör least sqared mellan mätning och sensor modellen
#
# ge set med parameter värden för modellen (optima)
#
# Använder optimat som start för MCMC för att få sannolikhetsfördelingen av modellen

# STEP 4 - whole dataset
# Summarize all events
# Some really nice plots


# Lägg in checkar mellan stegen som throwar error som går att analysera för att förböttra pipelinen. KOlla i daniels artikel
