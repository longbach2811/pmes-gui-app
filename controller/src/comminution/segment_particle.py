import cv2
import numpy as np
import random


def crop_circle(img, center, radius):
    rows, cols = img.shape[:2]
    x, y = center
    r = radius

    x1 = max(x - r, 0)
    y1 = max(y - r, 0)
    x2 = min(x + r, cols)
    y2 = min(y + r, rows)

    crop = img[y1:y2, x1:x2]

    cx = x - x1
    cy = y - y1

    mask = np.zeros((y2 - y1, x2 - x1), dtype=np.uint8)
    cv2.circle(mask, (cx, cy), r, 255, -1)

    crop = cv2.bitwise_and(crop, crop, mask=mask)
    return crop, mask


def segment_particles(img_bgr, thresh_s=54):
    rows, cols, _ = img_bgr.shape
    img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    img_blurred = cv2.medianBlur(img_gray, 5)

    # circles = cv2.HoughCircles(
    #     img_blurred,
    #     cv2.HOUGH_GRADIENT,
    #     dp=1,
    #     minDist=120,
    #     param1=50,
    #     param2=51,
    #     minRadius=1150,
    #     maxRadius=1200,
    # )

    circles = cv2.HoughCircles(
        img_blurred, 
        cv2.HOUGH_GRADIENT, 
        dp=1,             
        minDist=150,       
        param1=50,         
        param2=51,         
        minRadius=1130,     
        maxRadius=1200      
    )


    if circles is None:
        raise RuntimeError("No circles found")

    x_f, y_f, r_f = circles[0, 0]
    x, y, r = int(round(x_f)), int(round(y_f)), int(round(r_f))

    full_hough_mask = np.zeros((rows, cols), dtype=np.uint8)
    cv2.circle(full_hough_mask, (x, y), r - 10, 255, -1)

    hsv_full = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    s_channel_full = hsv_full[:, :, 1]

    s_masked_full = cv2.bitwise_and(
        s_channel_full, s_channel_full, mask=full_hough_mask
    )
    otsu_threshold_value, _ = cv2.threshold(
        s_masked_full, thresh_s, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    crop_img, circle_mask_crop = crop_circle(img_bgr, (x, y), r - 10)
    
    hsv_crop = cv2.cvtColor(crop_img, cv2.COLOR_BGR2HSV)
    s_channel_crop = hsv_crop[:, :, 1]

    _, mask_s = cv2.threshold(
        s_channel_crop, otsu_threshold_value, 255, cv2.THRESH_BINARY
    )

    mask_s = cv2.bitwise_and(mask_s, circle_mask_crop)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask_s = cv2.morphologyEx(mask_s, cv2.MORPH_CLOSE, kernel, iterations=2)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask_s, connectivity=8)
    print(f"[DEBUG] Connected components found: {num_labels - 1}")  

    vis_img = crop_img.copy()
    contours = []
    valid_idx = 0
    for i in range(1, num_labels):
        # Create a mask for the current component to find its specific contour
        component_mask = (labels == i).astype("uint8")
        cnts, _ = cv2.findContours(component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        if not cnts:
            continue

        pixel_count = stats[i, cv2.CC_STAT_AREA]
        if pixel_count <=1:
            continue

        contours.append(cnts[0])

        bx, by, bw, bh = stats[i, cv2.CC_STAT_LEFT], stats[i, cv2.CC_STAT_TOP], stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]

        color = (
            random.randint(50, 255),
            random.randint(50, 255),
            random.randint(50, 255),
        )
        cv2.drawContours(vis_img, cnts, -1, color, 2)  # Draw the contour outline
        cv2.rectangle(vis_img, (bx, by), (bx + bw, by + bh), color, 2)
        cv2.putText(
            vis_img, str(valid_idx), (bx, by - 5), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2
        )
        valid_idx += 1

    return vis_img, crop_img, mask_s, contours


if __name__ == "__main__":
    img_bgr = cv2.imread(
        r"D:\workspace\wyshieh_workspace\Mastication_project\images\comminution\Image__2025-12-26__16-41-57.png"
    )
    crop_result, mask_result, contours = segment_particles(img_bgr)

    cv2.imwrite("segmented_particles.png", crop_result)
    cv2.imwrite("particle_mask.png", mask_result)
