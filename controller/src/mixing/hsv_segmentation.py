import cv2
import numpy as np

def hsv_segmentation(img_bgr: np.ndarray, hsv_lower = 54, hsv_upper=255):
    rows, cols, _ = img_bgr.shape
    img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    img_blurred_hough = cv2.medianBlur(img_gray, 5)

    circles = cv2.HoughCircles(
        img_blurred_hough, 
        cv2.HOUGH_GRADIENT, 
        dp=1, 
        minDist=120, 
        param1=50, 
        param2=51, 
        minRadius=730, 
        maxRadius=800
    )

    hough_circle_mask = np.zeros((rows, cols), dtype=np.uint8)

    if circles is not None:
        circles = np.uint16(np.around(circles))
        x, y, r = circles[0, 0]

        cv2.circle(hough_circle_mask, (x, y), r, 255, thickness=-1)
        print(f"[DEBUG] Hough Circle FOUND: Center=({x}, {y}), Radius={r}")
    else:
        hough_circle_mask[:] = 255
        print("[DEBUG] WARNING: No Hough circle detected → using full mask.")

    img_bgr_cropped = cv2.bitwise_and(img_bgr, img_bgr, mask=hough_circle_mask)
    
    img_hsv = cv2.cvtColor(img_bgr_cropped, cv2.COLOR_BGR2HSV)
    h_channel, s_channel, v_channel = cv2.split(img_hsv)

    s_channel_blurred = cv2.medianBlur(s_channel, 3)

    
    _, foreground_mask_saturation = cv2.threshold(
        s_channel_blurred, 
        hsv_lower, 
        hsv_upper, 
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))
    foreground_mask_saturation = cv2.morphologyEx(foreground_mask_saturation, cv2.MORPH_CLOSE, kernel)


    # Morphology
    kernel_fill = np.ones((9, 9), np.uint8)
    mask_filled = cv2.dilate(foreground_mask_saturation, kernel_fill, iterations=1)
    # cv2.imwrite("mask_filled.png", mask_filled)

    kernel_sharpen = np.ones((11, 11), np.uint8)
    segmentation_mask = cv2.erode(mask_filled, kernel_sharpen, iterations=1)

    final_mask = cv2.bitwise_and(segmentation_mask, hough_circle_mask)

    return final_mask
    
