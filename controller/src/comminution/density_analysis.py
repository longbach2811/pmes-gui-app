import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde

def analyze_particle_density(density):
    D10 = np.percentile(density, 10)
    D50 = np.percentile(density, 50)
    D90 = np.percentile(density, 90)
    
    kde = gaussian_kde(density)
    x_vals = np.linspace(min(density), max(density), 500)
    pdf_vals = kde(x_vals)
    
    fig = plt.figure(figsize=(8,5))
    plt.plot(x_vals, pdf_vals, lw=2)
    
    for d_val, color, label in zip([D10, D50, D90], ['red','green','purple'], ['D10','D50','D90']):
        y_val = kde(d_val)
        plt.axvline(d_val, color=color, linestyle='--', label=f'{label} ({d_val:.2f})')
        plt.scatter(d_val, y_val, color=color, s=50)
    
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    
    return fig, D10, D50, D90
