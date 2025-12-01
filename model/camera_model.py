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

            # Set up the ImageFormatConverter for OpenCV (BGR8)
            self.converter = pylon.ImageFormatConverter()
            self.converter.OutputPixelFormat = pylon.PixelType_BGR8packed
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
            # Ensure camera is not grabbing when changing parameters
            if self.camera.IsGrabbing():
                self.camera.StopGrabbing()

            # Configure Resolution (ROI)
            self.camera.Width.SetValue(self.width)
            self.camera.Height.SetValue(self.height)
            
            # Configure Exposure Time
            # Set Auto mode first
            self.camera.ExposureAuto.SetValue(self.exposure_auto)
            if self.exposure_auto == 'Off':
                # Set manual value, ensuring it's within bounds
                current_exp = self.exposure_time
                if current_exp < self.camera.ExposureTime.GetMin():
                    current_exp = self.camera.ExposureTime.GetMin()
                self.camera.ExposureTime.SetValue(current_exp)

            # Configure Gain
            # Set Auto mode first
            self.camera.GainAuto.SetValue(self.gain_auto)
            if self.gain_auto == 'Off':
                # Set manual value, ensuring it's within bounds
                current_gain = self.gain
                if current_gain < self.camera.Gain.GetMin():
                    current_gain = self.camera.Gain.GetMin()
                self.camera.Gain.SetValue(current_gain)

            self.camera.BalanceWhiteAuto.SetValue(self.whitebalance_auto)
                
            print(f"[DEBUG] Configuration applied: WxH={self.width}x{self.height}, Exp={self.exposure_time} us.")

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

        # Start grabbing for 1 frame
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
            self.camera.StopGrabbing()
            # It's important to release the buffer
            if 'grabResult' in locals() and grabResult:
                 grabResult.Release()
            
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
            self.camera.Close()
            print("Camera connection closed.")
        # pylon.PylonTerminate()
        cv2.destroyAllWindows()


# =================================================================
#               USAGE EXAMPLE / TEST SECTION
# =================================================================

if __name__ == '__main__':
    # CONFIGURE SETTINGS
    # NOTE: Ensure these values (Width, Height, ExposureTime, Gain) are within the valid range for your specific Basler camera model.
    
    # Example configuration: 1280x720, 10000 us (10ms) Exposure, 3.0 dB Gain, Auto modes Off
    camera_config = {
        'height': 2160, 
        'width': 1280, 
        'exposure_time': 10000, 
        'exposure_auto': 'Off',
        'gain': 0.0,
        'gain_auto': 'Off'
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
            print("Single image saved as 'captured_image.png'")
        
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    # 4. CLEANUP
    cam_model.close()