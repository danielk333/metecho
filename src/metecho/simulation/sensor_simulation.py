class SensorSimulation:
    STEPS = [
        "transmission",
        "tx-propagation",
        "scattering",
        "rx-propagation",
        "reception",
        "digitization",
    ]

    def __init__(
        self,
        waveform_generator,
        noise_generator,
        sampler,
        inverse_time_of_flight,
        step_functions,
        step_parameters={},
    ):
        self.waveform_generator = waveform_generator
        self.noise_generator = noise_generator
        self.inverse_time_of_flight = inverse_time_of_flight
        self.sampler = sampler
        assert all(
            [key in self.STEPS for key in step_functions]
        ), "All steps are needed"
        self.step_functions = step_functions
        self.step_parameters = step_parameters

    def evaluate(self, parameters, waveform_parameters={}, noise_parameters={}):
        kw_args = {
            key: {var: parameters[var] for var in variables}
            for key, variables in self.step_parameters.items()
        }
        t_rec = self.sampler()
        t = self.inverse_time_of_flight(t_rec)
        signal = self.waveform_generator(t, **waveform_parameters)
        for step in self.STEPS:
            func = self.step_functions[step]
            params = kw_args.get(step, {})
            if step.endswith("propagation"):
                t, signal = func(t, signal, **params)
            else:
                signal = func(t, signal, **params)
        signal = signal + self.noise_generator(t, signal.shape, **noise_parameters)
        return t_rec, signal
