# view/settings_window.py
from PyQt6 import QtWidgets
from PyQt6.uic import loadUi
from PyQt6.QtCore import pyqtSignal
import os

class SettingsWindow(QtWidgets.QMainWindow):
    """Settings view chỉ emit signal"""
    send_led_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        loadUi(os.path.join(os.path.dirname(__file__), "settings_window.ui"), self)

        # Connect nút LED → emit pattern
        self.change_led_1_btn.clicked.connect(
            lambda: self.send_led_signal.emit("led 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0")
        )
        self.change_led_2_btn.clicked.connect(
            lambda: self.send_led_signal.emit("led 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0")
        )
        self.change_led_3_btn.clicked.connect(
            lambda: self.send_led_signal.emit("led 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0")
        )
        self.change_led_4_btn.clicked.connect(
            lambda: self.send_led_signal.emit("led 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0")
        )
