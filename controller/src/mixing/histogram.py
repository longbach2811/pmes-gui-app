import cv2
import matplotlib.pyplot as plt

def get_hsv_histogram_figure(h_channel, s_channel, v_channel, mask):

    hist_h = cv2.calcHist([h_channel], [0], mask, [180], [0, 180])
    hist_s = cv2.calcHist([s_channel], [0], mask, [256], [0, 256])
    hist_v = cv2.calcHist([v_channel], [0], mask, [256], [0, 256])

    hist_h = hist_h / hist_h.sum() if hist_h.sum() > 0 else hist_h
    hist_s = hist_s / hist_s.sum() if hist_s.sum() > 0 else hist_s
    hist_v = hist_v / hist_v.sum() if hist_v.sum() > 0 else hist_v

    fig, ax = plt.subplots(figsize=(8,5))
    ax.plot(hist_h, color='r', label='Hue')
    ax.plot(hist_s, color='g', label='Saturation')
    ax.plot(hist_v, color='b', label='Value')
    ax.legend()
    plt.tight_layout()

    return fig