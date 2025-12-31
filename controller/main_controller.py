# controller/main_controller.py
from PyQt5 import QtWidgets
from model import serial_model
from model.serial_model import SerialModel
from model.camera_model import CameraModel
from view.main_window import MainWindow
from view.settings_window import SettingsWindow
from view.dev_window import DevWindow
from PyQt6.QtCore import QCoreApplication
import time
import cv2

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
        self.main_view.dev_btn.clicked.connect(self.open_dev_window)

        # Develop button events of settings_window
        self.settings_view.send_led_button.connect(self.send_led_pattern)
        self.settings_view.slider_released.connect(self.handle_slider_change)
        self.settings_view.closeEvent = self.on_settings_close

        # Develop button events of dev_window
        self.dev_view.send_led_button.connect(self.send_led_pattern)
        self.dev_view.move_motor_btn.clicked.connect(self.send_motor_position_dev)

        self.main_view.show()

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
                # /////////////////////////////////
                if img_data is None:
                    self.main_view.show_error("Failed to capture image from camera.")
                    self.main_view.setEnabled(True)
                    return
                cv2.imwrite("comminution_capture_test.png", img_data)

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


        segment_img, segment_mask, contours = segment_particles(img_data)

        self.main_view.visualize_image(
            segment_img, self.main_view.comminution_segment_pb
        )

        areas = [cv2.contourArea(c) for c in contours]
        areas_mm2 = [area * (self.pixel_size_mm**2) for area in areas]

        self.main_view.update_particle_size_stats_ranges(
            areas_mm2, self.main_view.particle_size_stats_box, bin_size=0.01
        )

        fig, D10, D50, D90 = analyze_particle_density(areas_mm2)
        self.main_view.visualize_figure(fig, self.main_view.comminution_analysis_pb)
        self.main_view.d10_box.setText(f"{D10:.2f} mm2")
        self.main_view.d50_box.setText(f"{D50:.2f} mm2")
        self.main_view.d90_box.setText(f"{D90:.2f} mm2")

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

                cv2.imwrite("mixing_capture_test.png", img_data)

                # Turn off the led region 1 for mixing analysis

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
        self.main_view.visualize_figure(fig_hist, self.main_view.mixing_histogram_pb)

        self.main_view.voh_box.setText(f"{voh:.2f}")
        self.main_view.sdh_box.setText(f"{sdhue:.2f}")

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
        self.serial_model.send_and_wait_ok("led 1 0 0 0 1 0 0 0 1 0 0 0 1 0 0 0 0\n")
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
                return  # dừng luôn, không gửi lệnh hỏng

            print("[DEBUG] Motor position to send:", position)
            self.serial_model.send_and_wait_ok(f"motor {position}\n")
            self.main_view.append_log(f"Motor moved to position {position}")

        except ValueError:
            self.main_view.show_error("Invalid motor position.")
        except Exception as e:
            self.main_view.show_error(str(e))
