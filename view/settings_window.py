# view/settings_window.py
from PyQt6 import QtWidgets
from PyQt6.uic import loadUi
from PyQt6.QtCore import pyqtSignal
import os
from functools import partial

class SettingsWindow(QtWidgets.QMainWindow):
    send_led_button = pyqtSignal(str)     # button → pattern
    slider_released = pyqtSignal(int, int)  # (idx, new_value)

    def __init__(self):
        super().__init__()
        loadUi(os.path.join(os.path.dirname(__file__), "settings_window.ui"), self)

        # Map LED button → pattern
        self.led_button_patterns = {
            self.change_led_1_btn: "led 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0",
            self.change_led_2_btn: "led 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0",
            self.change_led_3_btn: "led 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0",
            self.change_led_4_btn: "led 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0",
        }

        for btn, p in self.led_button_patterns.items():
            btn.clicked.connect(lambda _, pattern=p: self.send_led_button.emit(pattern))

        # Map slider widgets
        self.slider_map = {
            1: self.intensity_led_1_slider,
            2: self.intensity_led_2_slider,
            3: self.intensity_led_3_slider,
            4: self.intensity_led_4_slider,
        }

        self.prev_values = {i: slider.value() for i, slider in self.slider_map.items()}

        # Use sliderReleased (emit once when user releases)
        for idx, slider in self.slider_map.items():
            slider.sliderReleased.connect(partial(self._emit_slider_value, idx, slider))

        # helper method
    def _emit_slider_value(self, idx, slider):
        """Emit (index, value) when slider is released."""
        # optional debug:
        # print(f"[DBG] slider {idx} released -> {slider.value()}")
        self.slider_released.emit(idx, slider.value())

