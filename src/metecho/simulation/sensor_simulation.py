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
        samples_to_transmissions_map,
        step_functions,
        step_parameters={},
    ):
        self.waveform_generator = waveform_generator
        self.noise_generator = noise_generator
        self.samples_to_transmissions_map = samples_to_transmissions_map
        self.sampler = sampler
        assert all(
            [key in self.STEPS for key in step_functions]
        ), "All steps are needed"
        self.step_functions = step_functions
        self.step_parameters = step_parameters

    def evaluate(
        self,
        parameters,
        waveform_parameters={},
        noise_parameters={},
        transmission_map_parameters=[],
        skip=False,
        end_shape=(),
    ):
        t_rec = self.sampler()
        if skip:
            return t_rec, self.noise_generator(t_rec, end_shape, **noise_parameters)
        func_args = {
            key: [parameters[var] for var in variables]
            for key, variables in self.step_parameters.items()
        }
        transmission_map = {key: parameters[key] for key in transmission_map_parameters}
        t = self.samples_to_transmissions_map(t_rec, **transmission_map)
        signal = self.waveform_generator(t, **waveform_parameters)
        for step in self.STEPS:
            func = self.step_functions[step]
            params = func_args.get(step, [])
            if step.endswith("propagation") or step == "digitization":
                t, signal = func(t, signal, *params)
            else:
                signal = func(t, signal, *params)
        signal = signal + self.noise_generator(t, signal.shape, **noise_parameters)
        return t_rec, signal
