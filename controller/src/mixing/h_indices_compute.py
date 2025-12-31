import numpy as np

def compute_hue(hue_array_degree):

    # Convert degrees to radians
    hue_rad = hue_array_degree * np.pi / 90.0

    # Circular components
    C = np.mean(np.cos(hue_rad))
    S = np.mean(np.sin(hue_rad))

    # Resultant vector length
    R = np.sqrt(C**2 + S**2)

    # Circular variance
    voh = 1.0 - R

    # SDHue
    sdhue = np.sqrt(voh)

    return voh, sdhue