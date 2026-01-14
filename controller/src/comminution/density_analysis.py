import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde

def analyze_particle_density(density, log_scale=None):
    area = np.asarray(density, dtype=float)
    area = area[area > 0]             

    if area.size == 0:
        raise ValueError("No positive particle areas provided.")

    sizes = area.copy()               
    weights = area.copy()              

    idx = np.argsort(sizes)
    sizes = sizes[idx]
    weights = weights[idx]

    cdf_emp = np.cumsum(weights)
    cdf_emp /= cdf_emp[-1]

    D10 = np.interp(0.10, cdf_emp, sizes)
    D50 = np.interp(0.50, cdf_emp, sizes)
    D90 = np.interp(0.90, cdf_emp, sizes)

    if log_scale:
        x_data = np.log10(sizes)
        xlabel = "log10(Particle diameter [mm])"
    else:
        x_data = sizes
        xlabel = "Particle diameter [mm]"

    weights_kde = weights / np.sum(weights)

    kde = gaussian_kde(x_data, weights=weights_kde)

    x = np.linspace(x_data.min(), x_data.max(), 2000)
    pdf = kde(x)

    dx = x[1] - x[0]
    cdf_kde = np.cumsum(pdf) * dx
    cdf_kde /= cdf_kde[-1]

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.plot(x, pdf, label="PDF")
    # ax.plot(x, cdf_kde, "--", label="CDF")

    for D, color, lbl in zip(
        [D10, D50, D90],
        ["r", "g", "b"],
        ["D10", "D50", "D90"]
    ):
        v = np.log10(D) if log_scale else D
        ax.axvline(v, linestyle=":", color=color, label=f"{lbl} = {D:.2f}")

    ax.set_xlabel(xlabel)
    ax.set_ylabel("Probability density / cumulative")
    ax.legend()
    ax.grid(True)

    plt.tight_layout()

    plt.savefig("particle_size_distribution.png", dpi=300)

    return fig, D10, D50, D90
