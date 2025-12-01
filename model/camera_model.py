import pypylon.pylon as pylon
import cv2

class CameraModel:
    def __init__(self, height=2160, width=4200, exposure_time=5000, exposure_auto='Off', gain=0.0, gain_auto='Off', whitebalance_auto='Once'):
        
        # 1. Initialize core attributes
        self.height = height
        self.width = width
        self.exposure_time = exposure_time
        self.exposure_auto = exposure_auto
        self.gain = gain
        self.gain_auto = gain_auto
        self.whitebalance_auto = whitebalance_auto
        self.camera = None
        self.converter = None
        self._initialize_camera()

    def _initialize_camera(self):
        """Connects to the Basler camera and sets up the ImageFormatConverter."""
        try:
            # Get the Factory Instance
            tlFactory = pylon.TlFactory.GetInstance()
            
            # Create InstantCamera for the first device found
            self.camera = pylon.InstantCamera(tlFactory.CreateFirstDevice())
            self.camera.Open()

            # --- Improvement: Set RAW format for the camera so WhiteBalance works ---
            # The ImageFormatConverter will then handle BGR8packed conversion
            if self.whitebalance_auto != 'Off':
                # Set camera to RAW mode for automatic White Balance to function
                # Use BayerGB8 or BayerRG8 depending on your camera model
                self.camera.PixelFormat.SetValue('BayerGB8') 
                print("[DEBUG] Camera PixelFormat set to BayerGB8 for Auto White Balance.")
            else:
                 # If Auto White Balance is off, setting BGR8packed can reduce CPU load
                self.camera.PixelFormat.SetValue('BGR8packed')


            # Set up the ImageFormatConverter for OpenCV (BGR8)
            self.converter = pylon.ImageFormatConverter()
            self.converter.OutputPixelFormat = pylon.PixelType_BGR8packed
            # Ensure the ImageFormatConverter can handle BayerGB8 -> BGR8packed
            self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
            
            print("[DEBUG] Camera successfully initialized.")
            self._apply_settings()

        except pylon.RuntimeException as e:
            print(f"[DEBUG] Pylon error during camera initialization: {e}")
            self.camera = None
        
        except Exception as e:
            print(f"[DEBUG] Unknown error during initialization: {e}")
            self.camera = None


    def _apply_settings(self):
        """Applies configuration parameters to the camera using GenICam nodes."""
        if not self.camera or not self.camera.IsOpen():
            print("[DEBUG] Camera is not open to apply settings.")
            return

        try:
            # --- Improvement: Optimize Start/Stop Grabbing ---
            # In a real-world scenario, it's better to StartGrabbing once.
            if self.camera.IsGrabbing():
                self.camera.StopGrabbing()

            # Configure Resolution (ROI)
            self.camera.Width.SetValue(self.width)
            self.camera.Height.SetValue(self.height)
            
            # Configure Exposure Time
            self.camera.ExposureAuto.SetValue(self.exposure_auto)
            if self.exposure_auto == 'Off':
                # --- Improvement: Ensure the value is within Min/Max limits ---
                current_exp = max(self.camera.ExposureTime.GetMin(), self.exposure_time)
                current_exp = min(self.camera.ExposureTime.GetMax(), current_exp)
                self.camera.ExposureTime.SetValue(current_exp)

            # Configure Gain
            self.camera.GainAuto.SetValue(self.gain_auto)
            if self.gain_auto == 'Off':
                # --- Improvement: Ensure the value is within Min/Max limits ---
                current_gain = max(self.camera.Gain.GetMin(), self.gain)
                current_gain = min(self.camera.Gain.GetMax(), current_gain)
                self.camera.Gain.SetValue(current_gain)

            self.camera.BalanceWhiteAuto.SetValue(self.whitebalance_auto)
                
            print(f"[DEBUG] Configuration applied: WxH={self.camera.Width.GetValue()}x{self.camera.Height.GetValue()}, Exp={self.camera.ExposureTime.GetValue()} us.")

        except pylon.RuntimeException as e:
            print(f"Pylon error when applying settings: {e}")

    # -------------------------------------------------------------
    # Core method: Capture Image
    # -------------------------------------------------------------
    def capture_image(self):
        """Captures a single image and returns it as a BGR NumPy array."""
        if not self.camera or not self.camera.IsOpen():
            print("[DEBUG] Cannot capture image. Camera is not initialized or connected.")
            return None
        
        grabResult = None
        
        # --- Improvement: StartGrabbing(1) for a single frame ---
        # While slower, this ensures the camera doesn't grab continuously if not needed.
        self.camera.StartGrabbing(1) 
        
        try:
            # Retrieve the grab result (5s timeout)
            grabResult = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

            if grabResult.GrabSucceeded():
                # Convert to BGR format
                image = self.converter.Convert(grabResult)
                img_bgr = image.GetArray()
                print("[DEBUG] Image captured successfully.")
                
                return img_bgr

            else:
                print(f"[DEBUG] Grab failed: {grabResult.ErrorCode} {grabResult.ErrorDescription}")
                return None

        except pylon.TimeoutException:
            print("[DEBUG] Timeout occurred while capturing image.")
            return None
            
        except pylon.RuntimeException as e:
            print(f"[DEBUG] Runtime error while capturing image: {e}")
            return None
        
        finally:
            # --- Improvement: Ensure buffer is Released before StopGrabbing ---
            if grabResult:
                grabResult.Release()
            
            # --- Ensure StopGrabbing if StartGrabbing(1) was called ---
            if self.camera.IsGrabbing():
                self.camera.StopGrabbing()


    # -------------------------------------------------------------
    # Core method: Record Video
    # -------------------------------------------------------------
    def record_video(self):
        pass


    # -------------------------------------------------------------
    # Cleanup method
    # -------------------------------------------------------------
    def close(self):
        """Closes the camera connection and cleans up resources."""
        if self.camera and self.camera.IsOpen():
            # Ensure grabbing is stopped before closing
            if self.camera.IsGrabbing():
                 self.camera.StopGrabbing()
            self.camera.Close()
            print("Camera connection closed.")
        # pylon.PylonTerminate()
        # Removed cv2.destroyAllWindows() from here (it belongs in the calling function)


# =================================================================
#                         USAGE EXAMPLE / TEST SECTION
# =================================================================

if __name__ == '__main__':
    # CONFIGURE SETTINGS
    # NOTE: Ensure these values (Width, Height, ExposureTime, Gain) are within the valid range for your specific Basler camera model.
    camera_config = {
        'height': 720,  # Changed to a more common resolution for testing
        'width': 1280, 
        'exposure_time': 10000, 
        'exposure_auto': 'Off',
        'gain': 0.0,
        'gain_auto': 'Off',
        'whitebalance_auto': 'Once'
    }

    # 1. INITIALIZE
    cam_model = CameraModel(**camera_config)

    if cam_model.camera and cam_model.camera.IsOpen():
        
        # 2. CAPTURE AND DISPLAY SINGLE IMAGE
        print("\n--- Starting Single Image Capture Test ---")
        image_data = cam_model.capture_image()
        
        if image_data is not None:
            # Display image using OpenCV
            cv2.imshow("Captured Basler Image", image_data)
            cv2.waitKey(1) # Need a 1ms waitKey for the window to display
        
        # 3. RECORD VIDEO TEST (New)
        # print("\n--- Starting Video Recording Test (Press 'q' to stop) ---")
        # cam_model.record_video()
        
        cv2.waitKey(0) # Wait for a key press to close the static image window
        cv2.destroyAllWindows()


    # 4. CLEANUP
    cam_model.close()