# controller/main_controller.py
from model.serial_model import SerialModel
from model.camera_model import CameraModel
from view.main_window import MainWindow
from view.settings_window import SettingsWindow
from view.dev_window import DevWindow
import time
import cv2
import numpy as np
import os

from controller.src.comminution.segment_particle import segment_particles
from controller.src.comminution.density_analysis import analyze_particle_density
from controller.src.mixing.hsv_segmentation import hsv_segmentation
from controller.src.mixing.histogram import get_hsv_histogram_figure
from controller.src.mixing.h_indices_compute import compute_hue


class MainController:
    def __init__(self, config="configs/config.yaml"):
        self.main_view = MainWindow()
        self.settings_view = SettingsWindow()
        self.dev_view = DevWindow()

        # Load hyperparameters for camera
        self.camera_config = {
            "height": config["camera"]["height"],
            "width": config["camera"]["width"],
            "exposure_time": config["camera"]["exposure_time"],
            "exposure_auto": config["camera"]["exposure_auto"],
            "gain": config["camera"]["gain"],
            "gain_auto": config["camera"]["gain_auto"],
            "whitebalance_auto": config["camera"]["whitebalance_auto"],
        }
        self.config = config

        # Load hyperparameters for serial
        self.delay_time = config["serial"]["delay_time"]

        # Load paramtter for pixel_size_mm
        self.radius_mm = config["disk_ref"]["radius_mm"]
        self.radius_px = config["disk_ref"]["radius_px"]
        self.pixel_size_mm = self.radius_mm / self.radius_px

        # Develop button events of main_window
        self.serial_model = None
        self.main_view.connect_btn.clicked.connect(self.connect_serial)
        self.main_view.setting_btn.clicked.connect(self.open_settings)
        self.main_view.analyze_comminution_btn.clicked.connect(
            self.start_comminution_analysis
        )
        self.main_view.analyze_mixing_btn.clicked.connect(self.start_mixing_analysis)
        self.main_view.analyze_mixing_btn_2.clicked.connect(self.start_mixing_analysis_2)
        self.main_view.dev_btn.clicked.connect(self.open_dev_window)

        # Develop button events of settings_window
        self.settings_view.send_led_button.connect(self.send_led_pattern)
        self.settings_view.slider_released.connect(self.handle_slider_change)
        self.settings_view.closeEvent = self.on_settings_close

        # Develop button events of dev_window
        self.dev_view.send_led_button.connect(self.send_led_pattern)
        self.dev_view.move_motor_btn.clicked.connect(self.send_motor_position_dev)

        self.main_view.show()

        ### Variable for saving
        self.comminution_data = None
        self.mixing_data_main_side_1 = None
        self.mixing_data_side_1_1 = None
        self.mixing_data_side_2_1 = None
        self.mixing_data_side_3_1 = None
        self.mixing_data_side_4_1 = None

        self.mixing_data_main_side_2 = None
        self.mixing_data_side_1_2 = None
        self.mixing_data_side_2_2 = None
        self.mixing_data_side_3_2 = None
        self.mixing_data_side_4_2 = None

    def start_comminution_analysis(self):

        self.main_view.append_log("Starting comminution analysis...")

        if self.main_view.online_radio.isChecked():
            if self.serial_model is None:
                self.main_view.show_warning("Please connect to serial port first.")
                return
            self.main_view.setEnabled(False)
            try:
                self.main_view.append_log("Initialize camera with config ... ")
                self.camera_model = CameraModel(**self.camera_config)
                # Move motor to position to capture image
                self.serial_model.send_and_wait_ok("motor 0\n")
                time.sleep(self.delay_time)
                # Turn on 5 LED for comminution analysis

                self.serial_model.send_and_wait_ok(
                    "led 1 0 0 0 1 0 0 0 1 0 0 0 1 0 0 0 0\n"
                )
                time.sleep(self.delay_time)
                # //////////////////////////////////
                # PUT CODE TO CAPTURE THE IMAGE HERE
                img_data = self.camera_model.capture_image()
                self.comminution_data = img_data
                
                # /////////////////////////////////
                if img_data is None:
                    self.main_view.show_error("Failed to capture image from camera.")
                    self.main_view.setEnabled(True)
                    return
                
                # Turn off 5 LED for comminution analysis
                self.serial_model.send_and_wait_ok(
                    "led 1 0 0 0 1 0 0 0 1 0 0 0 1 0 0 0 0\n"
                )
                time.sleep(self.delay_time)

                # Release camera resources
                self.camera_model.close()

                self.main_view.setEnabled(True)

            except Exception as e:
                self.main_view.show_error(str(e))
                self.main_view.setEnabled(True)

        if self.main_view.local_radio.isChecked():
            img_path = self.main_view.open_file_dialog()
            img_data = cv2.imread(img_path)
            if img_data is None:
                self.main_view.show_warning("No image file selected.")
                return

        try:
            segment_img, raw_crop, mask_s, contours = segment_particles(img_data)

            self.main_view.visualize_image(
                segment_img, self.main_view.comminution_segment_pb
            )

            density_area = [] 
            for i, cnt in enumerate(contours):
                particle_mask = np.zeros(mask_s.shape, dtype=np.uint8)
                cv2.drawContours(particle_mask, [cnt], -1, 255, -1)
                area = cv2.countNonZero(particle_mask)
                density_area.append(area)

            density_area = np.asarray(density_area)
            areas_mm2 = density_area * (self.pixel_size_mm ** 2)
            eq_diameter_mm = 2.0 * np.sqrt(areas_mm2 / np.pi)

            self.main_view.update_particle_size_stats_ranges(
                eq_diameter_mm, self.main_view.particle_size_stats_box, bin_size=0.01
            )

            fig, D10, D50, D90 = analyze_particle_density(eq_diameter_mm, log_scale=None)

            self.main_view.visualize_figure(fig, self.main_view.comminution_analysis_pb)
            self.main_view.d10_box.setText(f"{D10:.4f} mm")
            self.main_view.d50_box.setText(f"{D50:.4f} mm")
            self.main_view.d90_box.setText(f"{D90:.4f} mm")

        except Exception as e:
            self.main_view.show_error(str(e))

    def start_mixing_analysis(self):
        self.main_view.append_log("Starting mixing analysis...")

        if self.main_view.online_radio.isChecked():
            try:
                if self.serial_model is None:
                    self.main_view.show_warning("Please connect to serial port first.")
                    return
                self.main_view.setEnabled(False)

                # Move motor to position to capture image
                self.serial_model.send_and_wait_ok("motor 140\n")
                time.sleep(self.delay_time)

                # Turn on the led region 1 for mixing analysis
                self.camera_model = CameraModel(**self.camera_config)

                self.serial_model.send_and_wait_ok(
                    "led 1 0 0 0 1 0 0 0 1 0 0 0 1 0 0 0 0\n"
                )
                time.sleep(self.delay_time)
                # //////////////////////////////////
                # PUT CODE TO CAPTURE THE IMAGE 1 HERE
                img_data = self.camera_model.capture_image()
                # # /////////////////////////////////
                if img_data is None:
                    self.main_view.show_error("Failed to capture image from camera.")
                    self.main_view.setEnabled(True)
                    return

                self.mixing_data_main_side_1 = img_data

                self.serial_model.send_and_wait_ok(
                    "led 1 0 0 0 1 0 0 0 1 0 0 0 1 0 0 0 0\n"
                )
                time.sleep(self.delay_time)

                # Release camera resources
                self.camera_model.close()

                self.camera_config["exposure_time"] = 15000

                self.serial_model.send_and_wait_ok(
                    "led 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n"
                )
                img_data_1 = self.camera_model.capture_image()
                self.mixing_data_side_1_1 = img_data_1

                self.serial_model.send_and_wait_ok(
                    "led 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n"
                )

                self.serial_model.send_and_wait_ok(
                    "led 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0\n"
                )
                img_data_2 = self.camera_model.capture_image()
                self.mixing_data_side_2_1 = img_data_2

                self.serial_model.send_and_wait_ok(
                     "led 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0\n"
                )

                self.serial_model.send_and_wait_ok(
                    "led 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0\n"
                )
                img_data_3 = self.camera_model.capture_image()
                self.mixing_data_side_3_1 = img_data_3

                self.serial_model.send_and_wait_ok(
                    "led 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0\n"
                )

                self.serial_model.send_and_wait_ok(
                    "led 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0\n"
                )
                img_data_4 = self.camera_model.capture_image()
                self.mixing_data_side_4_1 = img_data_4

                self.serial_model.send_and_wait_ok(
                    "led 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0\n"
                )

                self.camera_model.close()

                self.main_view.setEnabled(True)
            except Exception as e:
                self.main_view.show_error(str(e))
                self.main_view.setEnabled(True)
        if self.main_view.local_radio.isChecked():
            img_path = self.main_view.open_file_dialog()
            img_data = cv2.imread(img_path)
            if img_data is None:
                self.main_view.show_warning("No image file selected.")
                return

        try:
            chewing_gum_mask = hsv_segmentation(img_data, 54, 255)
            img_data = cv2.bitwise_and(img_data, img_data, mask=chewing_gum_mask)
            hsv_data = cv2.cvtColor(img_data, cv2.COLOR_BGR2HSV)
            h_channel, s_channel, v_channel = cv2.split(hsv_data)
            fig_hist = get_hsv_histogram_figure(
                h_channel, s_channel, v_channel, chewing_gum_mask
            )
            voh, sdhue = compute_hue(h_channel[chewing_gum_mask > 0])

            self.main_view.visualize_image(img_data, self.main_view.mixing_capture_pb)
            self.main_view.visualize_image(hsv_data, self.main_view.mixing_hsv_pb)
            self.main_view.visualize_figure(
                fig_hist, self.main_view.mixing_histogram_pb
            )

            self.main_view.voh_box.setText(f"{voh:.4f}")
            self.main_view.sdh_box.setText(f"{sdhue:.4f}")

        except Exception as e:
            self.main_view.show_error(str(e))

    def start_mixing_analysis_2(self):
        self.main_view.append_log("Starting mixing analysis...")

        if self.main_view.online_radio.isChecked():
            try:
                if self.serial_model is None:
                    self.main_view.show_warning("Please connect to serial port first.")
                    return
                self.main_view.setEnabled(False)

                # Move motor to position to capture image
                self.serial_model.send_and_wait_ok("motor 140\n")
                time.sleep(self.delay_time)

                # Turn on the led region 1 for mixing analysis
                self.camera_model = CameraModel(**self.camera_config)

                self.serial_model.send_and_wait_ok(
                    "led 1 0 0 0 1 0 0 0 1 0 0 0 1 0 0 0 0\n"
                )
                time.sleep(self.delay_time)
                # //////////////////////////////////
                # PUT CODE TO CAPTURE THE IMAGE 1 HERE
                img_data = self.camera_model.capture_image()
                # # /////////////////////////////////
                if img_data is None:
                    self.main_view.show_error("Failed to capture image from camera.")
                    self.main_view.setEnabled(True)
                    return

                self.mixing_data_main_side_2 = img_data

                self.serial_model.send_and_wait_ok(
                    "led 1 0 0 0 1 0 0 0 1 0 0 0 1 0 0 0 0\n"
                )
                time.sleep(self.delay_time)

                # Release camera resources
                self.camera_model.close()

                self.camera_config["exposure_time"] = 15000

                self.serial_model.send_and_wait_ok(
                    "led 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n"
                )
                img_data_1 = self.camera_model.capture_image()
                self.mixing_data_side_1_2 = img_data_1

                self.serial_model.send_and_wait_ok(
                    "led 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n"
                )

                self.serial_model.send_and_wait_ok(
                    "led 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0\n"
                )
                img_data_2 = self.camera_model.capture_image()
                self.mixing_data_side_2_2 = img_data_2

                self.serial_model.send_and_wait_ok(
                     "led 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0\n"
                )

                self.serial_model.send_and_wait_ok(
                    "led 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0\n"
                )
                img_data_3 = self.camera_model.capture_image()
                self.mixing_data_side_3_2 = img_data_3

                self.serial_model.send_and_wait_ok(
                    "led 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0\n"
                )

                self.serial_model.send_and_wait_ok(
                    "led 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0\n"
                )
                img_data_4 = self.camera_model.capture_image()
                self.mixing_data_side_4_2 = img_data_4

                self.serial_model.send_and_wait_ok(
                    "led 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0\n"
                )

                self.camera_model.close()

                self.main_view.setEnabled(True)
            except Exception as e:
                self.main_view.show_error(str(e))
                self.main_view.setEnabled(True)
        if self.main_view.local_radio.isChecked():
            img_path = self.main_view.open_file_dialog()
            img_data = cv2.imread(img_path)
            if img_data is None:
                self.main_view.show_warning("No image file selected.")
                return

        try:
            chewing_gum_mask = hsv_segmentation(img_data, 54, 255)
            img_data = cv2.bitwise_and(img_data, img_data, mask=chewing_gum_mask)
            hsv_data = cv2.cvtColor(img_data, cv2.COLOR_BGR2HSV)
            h_channel, s_channel, v_channel = cv2.split(hsv_data)
            fig_hist = get_hsv_histogram_figure(
                h_channel, s_channel, v_channel, chewing_gum_mask
            )
            voh, sdhue = compute_hue(h_channel[chewing_gum_mask > 0])

            self.main_view.visualize_image(img_data, self.main_view.mixing_capture_pb)
            self.main_view.visualize_image(hsv_data, self.main_view.mixing_hsv_pb)
            self.main_view.visualize_figure(
                fig_hist, self.main_view.mixing_histogram_pb
            )

            self.main_view.voh_box.setText(f"{voh:.4f}")
            self.main_view.sdh_box.setText(f"{sdhue:.4f}")

        except Exception as e:
            self.main_view.show_error(str(e))
        
    def save_comminution_data(self):
        try:
            name = self.main_view.get_name()
            gender = self.main_view.get_gender()
            age = self.main_view.get_age()

            saved_path = "saved_data"

            os.makedirs(self.save_data, exist_ok=True)
            
            comminution_path = os.path.join(saved_path, "comminution")
            os.makedirs(comminution_path, exist_ok=True)


            if self.comminution_data is not None:
                chewing_cycles = self.main_view.get_comminution_chewing_cycles()
                comminution_save_dir = os.path.join(comminution_path, f"{name}_{gender}_{age}")
                os.makedirs(comminution_save_dir, exist_ok=True)
                comminution_save_path = os.path.join(comminution_save_dir, f"{chewing_cycles}.png")
                cv2.imwrite(comminution_save_path, self.comminution_data)
            else:
                self.main_view.show_warning("No comminution data to save.")

        except Exception as e:
            self.main_view.show_error(str(e))

    def save_mixing_data_side_1(self):
        try:
            name = self.main_view.get_name()
            gender = self.main_view.get_gender()
            age = self.main_view.get_age()

            saved_path = "saved_data"

            os.makedirs(self.save_data, exist_ok=True)

            mixing_path = os.path.join(saved_path, "mixing")
            os.makedirs(mixing_path, exist_ok=True)

            mixing_chewing_cycles_side_1 = self.main_view.get_mixing_chewing_cycles_side_1()
            mixing_save_dir = os.path.join(mixing_path, f"{name}_{gender}_{age}")
            os.makedirs(mixing_save_dir, exist_ok=True)
            if self.mixing_data_main_side_1 is not None:
                mixing_save_path_side_1 = os.path.join(mixing_save_dir, f"{mixing_chewing_cycles_side_1}_1.png")
                cv2.imwrite(mixing_save_path_side_1, self.mixing_data_main_side_1)
            else:
                self.main_view.show_warning("No mixing data main side 1 to save.")

            if self.mixing_data_main_side_1 is  not None:
                mixing_save_path_side_1_1 = os.path.join(mixing_save_dir, f"{mixing_chewing_cycles_side_1}_1_1.png")
                cv2.imwrite(mixing_save_path_side_1_1, self.mixing_data_side_1_1)
            else:
                self.main_view.show_warning("No mixing data side 1 to save.")

            if self.mixing_data_side_2_1 is not None:
                mixing_save_path_side_2_1 = os.path.join(mixing_save_dir, f"{mixing_chewing_cycles_side_1}_2_1.png")
                cv2.imwrite(mixing_save_path_side_2_1, self.mixing_data_side_2_1)
            else:
                self.main_view.show_warning("No mixing data side 2 to save.")

            if self.mixing_data_side_3_1 is not None:
                mixing_save_path_side_3_1 = os.path.join(mixing_save_dir, f"{mixing_chewing_cycles_side_1}_3_1.png")
                cv2.imwrite(mixing_save_path_side_3_1, self.mixing_data_side_3_1)
            else:                
                self.main_view.show_warning("No mixing data side 3 to save.")
                
            if self.mixing_data_side_4_1 is not None:
                mixing_save_path_side_4_1 = os.path.join(mixing_save_dir, f"{mixing_chewing_cycles_side_1}_4_1.png")
                cv2.imwrite(mixing_save_path_side_4_1, self.mixing_data_side_4_1)
            else:
                self.main_view.show_warning("No mixing data side 4 to save.")

        except Exception as e:
            self.main_view.show_error(str(e))

    def save_mixing_data_side_2(self):
        try:
            name = self.main_view.get_name()
            gender = self.main_view.get_gender()
            age = self.main_view.get_age()

            saved_path = "saved_data"

            os.makedirs(self.save_data, exist_ok=True)

            mixing_path = os.path.join(saved_path, "mixing")
            os.makedirs(mixing_path, exist_ok=True)

            mixing_chewing_cycles_side_2 = self.main_view.get_mixing_chewing_cycles_side_2()
            mixing_save_dir = os.path.join(mixing_path, f"{name}_{gender}_{age}")
            os.makedirs(mixing_save_dir, exist_ok=True)
            if self.mixing_data_main_side_2 is not None:
                mixing_save_path_side_2 = os.path.join(mixing_save_dir, f"{mixing_chewing_cycles_side_2}_2.png")
                cv2.imwrite(mixing_save_path_side_2, self.mixing_data_main_side_2)
            else:
                self.main_view.show_warning("No mixing data main side 2 to save.")
            if self.mixing_data_side_1_2 is not None:
                mixing_save_path_side_1_2 = os.path.join(mixing_save_dir, f"{mixing_chewing_cycles_side_2}_2_1.png")
                cv2.imwrite(mixing_save_path_side_1_2, self.mixing_data_side_1_2)
            else:
                self.main_view.show_warning("No mixing data side 1 to save.")
            if self.mixing_data_side_2_2 is not None:
                mixing_save_path_side_2_2 = os.path.join(mixing_save_dir, f"{mixing_chewing_cycles_side_2}_2_2.png")
                cv2.imwrite(mixing_save_path_side_2_2, self.mixing_data_side_2_2)
            else:
                self.main_view.show_warning("No mixing data side 2 to save.")
            if self.mixing_data_side_3_2 is not None:
                mixing_save_path_side_3_2 = os.path.join(mixing_save_dir, f"{mixing_chewing_cycles_side_2}_3_2.png")
                cv2.imwrite(mixing_save_path_side_3_2, self.mixing_data_side_3_2)
            else:
                self.main_view.show_warning("No mixing data side 3 to save.")
            if self.mixing_data_side_4_2 is not None:
                mixing_save_path_side_4_2 = os.path.join(mixing_save_dir, f"{mixing_chewing_cycles_side_2}_2_4.png")
                cv2.imwrite(mixing_save_path_side_4_2, self.mixing_data_side_4_2)
            else:
                self.main_view.show_warning("No mixing data side 4 to save.")

        except Exception as e:
            self.main_view.show_error(str(e))



    def open_settings(self):
        if self.serial_model is None:
            self.main_view.show_warning("Please connect to serial port first.")
            return

        try:
            self.main_view.setEnabled(False)
            self.settings_view.show()
            self.serial_model.send_and_wait_ok(
                "led 1 0 0 0 1 0 0 0 1 0 0 0 1 0 0 0 0\n"
            )
            time.sleep(1)
        except Exception as e:
            self.main_view.show_error(str(e))
            self.main_view.setEnabled(True)

    def on_settings_close(self, event):
        self.serial_model.send_and_wait_ok(
            "led 1 0 0 0 1 0 0 0 1 0 0 0 1 0 0 0 0\n"
            )
        self.settings_view.close()
        self.main_view.setEnabled(True)

    def connect_serial(self):
        port = self.main_view.get_port()
        baud = self.main_view.get_baudrate()

        try:
            self.serial_model = SerialModel(port, baud)
            self.main_view.append_log(f"Connected to {port} at {baud} baud.")
            self.main_view.show_info(
                f"Connected successfully to {port} at {baud} baud."
            )
        except Exception as e:
            self.main_view.show_error(str(e))

    def send_led_pattern(self, pattern):
        try:
            self.settings_view.setEnabled(False)
            self.serial_model.send_and_wait_ok(pattern)
            self.main_view.append_log("OK received")
            self.settings_view.setEnabled(True)
        except Exception as e:
            self.main_view.show_error(str(e))
            self.settings_view.setEnabled(True)

    def handle_slider_change(self, idx, new_val):
        prev_val = self.settings_view.prev_values[idx]
        diff = new_val - prev_val

        if diff == 0:
            return

        # define step patterns
        dec_pattern, inc_pattern = {
            1: (
                "led 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0",
                "led 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0",
            ),
            2: (
                "led 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0",
                "led 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0",
            ),
            3: (
                "led 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0",
                "led 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0",
            ),
            4: (
                "led 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0",
                "led 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0",
            ),
        }[idx]

        pattern = inc_pattern if diff > 0 else dec_pattern
        self.settings_view.setEnabled(False)
        for _ in range(abs(diff)):
            self.send_led_pattern(pattern)
            time.sleep(self.delay_time)
        self.settings_view.setEnabled(True)
        self.settings_view.prev_values[idx] = new_val

    def open_dev_window(self):
        if self.serial_model is None:
            self.main_view.show_warning("Please connect to serial port first.")
            return

        self.dev_view.show()

    def send_motor_position_dev(self):
        try:
            position = self.dev_view.get_position()
            if position is None:
                return

            print("[DEBUG] Motor position to send:", position)
            self.serial_model.send_and_wait_ok(f"motor {position}\n")
            self.main_view.append_log(f"Motor moved to position {position}")

        except ValueError:
            self.main_view.show_error("Invalid motor position.")
        except Exception as e:
            self.main_view.show_error(str(e))
