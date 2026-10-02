import matplotlib.pyplot as plt

from metecho.noise.types import GaussianNoiseChunks


def plot_gaussian_noise(noise: GaussianNoiseChunks) -> None:
    _, axs = plt.subplots()

    axs.plot(noise.mean)

    plt.show()
