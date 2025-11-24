# controller/main_controller.py
from model.serial_model import SerialModel
from view.main_window import MainWindow
from view.settings_window import SettingsWindow
from PyQt6.QtCore import QCoreApplication
import time

class MainController:
    def __init__(self):
        self.main_view = MainWindow()
        self.settings_view = SettingsWindow()

        # mở settings window
        self.main_view.setting_btn.clicked.connect(self.settings_view.show)

        # kết nối signal LED
        self.settings_view.send_led_signal.connect(self.send_led_pattern)

        self.main_view.show()

    def send_led_pattern(self, pattern):
        port = self.main_view.get_port()
        baud = self.main_view.get_baudrate()

        try:
            serial_model = SerialModel(port, baud)
            serial_model.send_and_wait_ok(pattern)
            self.main_view.append_log("OK received")

        except Exception as e:
            self.main_view.show_error(str(e))
