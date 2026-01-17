import numpy as np
from scipy.stats import entropy

def compute_cv_ab(img_lab, mask):
    a = img_lab[:, :, 1].astype(np.float32)
    b = img_lab[:, :, 2].astype(np.float32)
    a = a[mask > 0]
    b = b[mask > 0]
    mean_ab = np.sqrt(np.mean(a)**2 + np.mean(b)**2)
    std_ab = np.sqrt(np.var(a) + np.var(b))

    return std_ab / mean_ab

def compute_local_variance(img_lab, mask, block_size=16):
    a = img_lab[:, :, 1].astype(np.float32)
    b = img_lab[:, :, 2].astype(np.float32)

    h, w = a.shape
    local_vars = []

    for y in range(0, h - block_size, block_size):
        for x in range(0, w - block_size, block_size):
            block_mask = mask[y:y+block_size, x:x+block_size]

            if np.sum(block_mask) < 0.5 * block_size * block_size:
                continue

            a_block = a[y:y+block_size, x:x+block_size][block_mask]
            b_block = b[y:y+block_size, x:x+block_size][block_mask]

            var_block = np.var(a_block) + np.var(b_block)
            local_vars.append(var_block)

    if len(local_vars):
        return 0.0

    return np.mean(local_vars)
