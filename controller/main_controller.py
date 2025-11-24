# controller/main_controller.py
from model import serial_model
from model.serial_model import SerialModel
from view.main_window import MainWindow
from view.settings_window import SettingsWindow
from PyQt6.QtCore import QCoreApplication
import time

class MainController:
    def __init__(self):
        self.main_view = MainWindow()
        self.settings_view = SettingsWindow()

        # Develop button events of main_window
        self.main_view.connect_btn.clicked.connect(self.connect_serial)
        self.main_view.setting_btn.clicked.connect(self.open_settings)

        # Develop button events of settings_window
        self.settings_view.send_led_signal.connect(self.send_led_pattern)
        self.settings_view.closeEvent = self.on_settings_close

        self.main_view.show()

    def open_settings(self):
        try:
            self.main_view.setEnabled(False)
            self.settings_view.show()
            self.serial_model.send_and_wait_ok("led 1 0 0 0 1 0 0 0 1 0 0 0 1 0 0 0 0\n")
            time.sleep(0.5) 
        except Exception as e:
            self.main_view.show_error(str(e))

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
            self.main_view.show_info(f"Connected successfully to {port} at {baud} baud.")
        except Exception as e:
            self.main_view.show_error(str(e))

    def send_led_pattern(self, pattern):
        try:
            self.serial_model.send_and_wait_ok(pattern)
            self.main_view.append_log("OK received")

        except Exception as e:
            self.main_view.show_error(str(e))
