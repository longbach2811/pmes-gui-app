# view/dev_window.py
from PyQt6 import QtWidgets
from PyQt6.uic import loadUi
from PyQt6.QtCore import pyqtSignal
import os

class DevWindow(QtWidgets.QMainWindow):
    send_led_button = pyqtSignal(str)
    slider_released = pyqtSignal(int, int)

    def __init__(self):
        super().__init__()
        loadUi(os.path.join(os.path.dirname(__file__), "dev_window.ui"), self)

        # Map LED button → pattern
        self.led_button_patterns = {
            self.change_led_1_btn: "led 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0",
            self.change_led_2_btn: "led 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0",
            self.change_led_3_btn: "led 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0",
            self.change_led_4_btn: "led 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0",
        }

        # Map LED ON button → pattern
        self.on_off_button_patterns = {
            self.on_led1_btn: "led 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0",
            self.on_led2_btn: "led 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0",
            self.on_led3_btn: "led 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0",
            self.on_led4_btn: "led 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0",
        }

        # Connect LED buttons
        for btn, p in self.led_button_patterns.items():
            btn.clicked.connect(lambda _, pattern=p: self.send_led_button.emit(pattern))

        for btn, p in self.on_off_button_patterns.items():
            btn.clicked.connect(lambda _, pattern=p: self.send_led_button.emit(pattern))

        # Map sliders
        self.slider_map = {
            1: self.intensity_led_1_slider,
            2: self.intensity_led_2_slider,
            3: self.intensity_led_3_slider,
            4: self.intensity_led_4_slider,
        }

        # Store previous slider values
        self.prev_values = {
            i: slider.value() for i, slider in self.slider_map.items()
        }

        # Connect sliders
        for idx, slider in self.slider_map.items():
            slider.sliderReleased.connect(
                lambda _, i=idx, s=slider: self._emit_slider_value(i, s)
            )

    def _emit_slider_value(self, idx, slider):
        self.slider_released.emit(idx, slider.value())

    def get_position(self) -> int:
        return int(self.target_mm_box.text().strip())

    def show_error(self, msg):
        QtWidgets.QMessageBox.critical(self, "Error", msg)

    def show_info(self, msg):
        QtWidgets.QMessageBox.information(self, "Info", msg)

    def show_warning(self, msg):
        QtWidgets.QMessageBox.warning(self, "Warning", msg)
