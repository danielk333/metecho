from typing import Callable, Optional, TypedDict, Unpack

import numpy as np
import numpy.typing as npt
from tqdm import tqdm


class ScamKwargs(TypedDict, total=False):
    accept_max: float
    accept_min: float
    adapt_interval: int
    proposal_adapt_interval: int
    tune: int
    proposal: str
    progress_bar: bool


class Scam:
    """Markov Chain Monte Carlo sampling of the posterior,
    assuming all measurement errors are Gaussian (thus the log likelihood
    becomes a least squares).
    """

    def __init__(self, base_step_size: int, **kwargs: Unpack[ScamKwargs]) -> None:
        self.base_step_size = base_step_size
        self.options: ScamKwargs = ScamKwargs(
            accept_max=0.5,
            accept_min=0.3,
            adapt_interval=1000,
            proposal_adapt_interval=10000,
            tune=1000,
            proposal="normal",
            progress_bar=True,
        )
        self.options.update(kwargs)

    def run(
        self,
        posterior: Callable,
        start: npt.NDArray,
        steps: int,
        seed: Optional[float | npt.NDArray[np.floating]] = None,
    ) -> npt.NDArray:
        if seed is not None:
            seed_state = np.random.seed()
            np.random.seed(seed)
        xnow = np.copy(start)
        step = np.copy(self.base_step_size)

        n_var = len(start)

        run_steps = self.options["tune"] + steps
        chain = np.empty((n_var, run_steps), dtype=np.float64)

        logpost = posterior(xnow)

        accept = np.zeros((n_var,), dtype=np.float64)
        tries = np.zeros((n_var,), dtype=np.float64)

        if self.options["proposal"] in ["normal", "adaptive"]:
            proposal_mu = np.zeros((n_var,), dtype=np.float64)
            proposal_cov = np.eye(n_var, dtype=np.float64)
            proposal_axis = np.eye(n_var, dtype=np.float64)
        else:
            raise ValueError(
                f'proposal option "{self.options["proposal"]}"\
                not recognized'
            )

        if self.options["progress_bar"]:
            pbar = tqdm(position=0, total=run_steps)

        for ind in range(run_steps):
            if self.options["progress_bar"]:
                pbar.update(1)
                pbar.set_description("Sampling log-posterior = {:<10.3f} ".format(logpost))

            xtry = np.copy(xnow)

            pi = int(np.floor(np.random.rand(1) * n_var))

            proposal0 = np.random.multivariate_normal(proposal_mu, proposal_cov)
            proposal = proposal0[pi] * proposal_axis[:, pi]

            xtry += proposal * step[pi]

            logpost_try = posterior(xtry)
            alpha = np.log(np.random.rand(1))

            if logpost_try > logpost:
                _accept = True
            elif (logpost_try - alpha) > logpost:
                _accept = True
            else:
                _accept = False

            tries[pi] += 1.0

            if _accept:
                logpost = logpost_try
                xnow = xtry
                accept[pi] += 1.0

            ad_inv = self.options["adapt_interval"]
            cov_ad_inv = self.options["proposal_adapt_interval"]
            ac_min = self.options["accept_min"]
            ac_max = self.options["accept_max"]
            if ind % ad_inv == 0 and ind > 0:
                for var_ind in range(n_var):
                    ratio = accept[var_ind] / tries[var_ind]

                    if ratio > ac_max:
                        step[var_ind] *= 2.0
                    elif ratio < ac_min:
                        step[var_ind] /= 2.0

                    accept[var_ind] = 0.0
                    tries[var_ind] = 0.0

            if ind % cov_ad_inv == 0 and ind > 0 and self.options["proposal"] == "adaptive":
                _data = chain[var_ind, :ind]
                _proposal_cov = np.corrcoef(_data)

                if not np.any(np.isnan(_proposal_cov)):
                    eigs, proposal_axis = np.linalg.eig(_proposal_cov)
                    proposal_cov = np.diag(eigs)

            chain[:, ind] = xnow

        if seed is not None:
            np.random.seed(seed_state)

        return chain[:, self.options["tune"] :]
