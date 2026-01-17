import numpy as np
import cv2
import matplotlib.pyplot as plt

def extract_unmixed_regions(img_bgr, gum_mask):

    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    a = lab[:, :, 1].astype(np.int16) - 128
    b = lab[:, :, 2].astype(np.int16) - 128

    green_mask = (
        (a >= -80) & (a <= -30) &
        (b >= 0) & (b <= 50) &
        (gum_mask > 0)
    )

    red_mask = (
        (a >= 30) & (a <= 80) &
        (b >= 0) & (b <= 50) &
        (gum_mask > 0)
    )

    return (
        green_mask.astype(np.uint8) * 255,
        red_mask.astype(np.uint8) * 255
    )

def compute_uaf(gum_mask, color_mask):
    A_total = np.count_nonzero(gum_mask)
    A_color = np.count_nonzero(color_mask)

    if A_total == 0:
        return 0.0

    return A_color / A_total

def analyze_unmixed_area_fraction(img, gum_mask):
    green_mask, red_mask = extract_unmixed_regions(img, gum_mask)

    uaf_green = compute_uaf(gum_mask, green_mask)
    uaf_red = compute_uaf(gum_mask, red_mask)
    uaf_total = uaf_green + uaf_red

    return uaf_green, uaf_red, uaf_total, green_mask, red_mask

if __name__ == "__main__":
    import cv2
    from hsv_segmentation import hsv_segmentation

    img_bgr = cv2.imread(r"D:\workspace\wyshieh_workspace\Mastication_project\images\mixing\multi_shot\Ting\10_1.png")
    gum_mask = hsv_segmentation(img_bgr, hsv_lower=54, hsv_upper=255)
    uaf_green, uaf_red, uaf_total, green_mask, red_mask = analyze_unmixed_area_fraction(img_bgr, gum_mask)

    # print(f"UAF: {uaf:.4f}")

    # Visualize results
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    fig, axs = plt.subplots(2, 2, figsize=(12, 8))

    axs[0, 0].imshow(img_rgb)
    axs[0, 0].set_title("Original")

    axs[0, 1].imshow(gum_mask, cmap="gray")
    axs[0, 1].set_title("Gum mask")

    axs[1, 0].imshow(green_mask, cmap="Greens")
    axs[1, 0].set_title(f"Green UAF: {uaf_green:.3f}")

    axs[1, 1].imshow(red_mask, cmap="Reds")
    axs[1, 1].set_title(f"Red UAF: {uaf_red:.3f}")

    for ax in axs.ravel():
        ax.axis("off")

    plt.tight_layout()
    plt.show()