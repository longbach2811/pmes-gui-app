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
        self.serial_model = None
        self.main_view.connect_btn.clicked.connect(self.connect_serial)
        self.main_view.setting_btn.clicked.connect(self.open_settings)
        self.main_view.analyze_comminution_btn.clicked.connect(self.start_comminution_analysis)
        self.main_view.analyze_mixing_btn.clicked.connect(self.start_mixing_analysis)

        # Develop button events of settings_window
        self.settings_view.send_led_signal.connect(self.send_led_pattern)
        self.settings_view.closeEvent = self.on_settings_close

        self.main_view.show()
    
    def start_comminution_analysis(self):
        if self.serial_model is None:
            self.main_view.show_warning("Please connect to serial port first.")
            return
        
        self.main_view.append_log("Starting comminution analysis...")
        
        self.main_view.setEnabled(False)

        # Move motor to position to capture image
        try:
            self.serial_model.send_and_wait_ok("motor 0\n")
            time.sleep(1)
        except Exception as e:
            self.main_view.show_error(str(e))
        
        # Turn on 5 LED for comminution analysis
        try:
            self.serial_model.send_and_wait_ok("led 1 0 0 0 1 0 0 0 1 0 0 0 1 0 0 0 1\n")
        except Exception as e:
            self.main_view.show_error(str(e))

        time.sleep(1)
        # //////////////////////////////////
        # PUT CODE TO CAPTURE THE IMAGE HERE
        # //////////////////////////////////

        # Turn off 5 LED for comminution analysis
        try:
            self.serial_model.send_and_wait_ok("led 1 0 0 0 1 0 0 0 1 0 0 0 1 0 0 0 1\n")
        except Exception as e:
            self.main_view.show_error(str(e))
        time.sleep(1)
        
        self.main_view.setEnabled(True)

        # //////////////////////////////////
        # PUT CODE TO PROCESS THE IMAGE HERE
        # //////////////////////////////////
    
    def start_mixing_analysis(self):
        if self.serial_model is None:
            self.main_view.show_warning("Please connect to serial port first.")
            return
        
        self.main_view.append_log("Starting mixing analysis...")

        self.main_view.setEnabled(False)

        # Move motor to position to capture image
        try:
            self.serial_model.send_and_wait_ok("motor 80\n")
            time.sleep(1)
        except Exception as e:
            self.main_view.show_error(str(e))

        

        # Turn on the led region 1 for mixing analysis
        try:
            self.serial_model.send_and_wait_ok("led 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n")
        except Exception as e:
            self.main_view.show_error(str(e))

        time.sleep(1)
        # //////////////////////////////////
        # PUT CODE TO CAPTURE THE IMAGE 1 HERE
        # ///////////////////////////////// 

        # Turn off the led region 1 for mixing analysis
        try:
            self.serial_model.send_and_wait_ok("led 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n")
        except Exception as e:
            self.main_view.show_error(str(e))

        time.sleep(1)

        # turn on the led region 2 for mixing analysis
        try:
            self.serial_model.send_and_wait_ok("led 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0\n")
        except Exception as e:
            self.main_view.show_error(str(e))

        time.sleep(1)

        # //////////////////////////////////
        # PUT CODE TO CAPTURE THE IMAGE 2 HERE
        time.sleep(5)
        # //////////////////////////////////

        # Turn off the led region 2 for mixing analysis
        try:
            self.serial_model.send_and_wait_ok("led 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0\n")
        except Exception as e:
            self.main_view.show_error(str(e))

        time.sleep(1)

        # Turn on the led region 3 for mixing analysis
        try:
            self.serial_model.send_and_wait_ok("led 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0\n")
        except Exception as e:
            self.main_view.show_error(str(e))

        time.sleep(1)

        # //////////////////////////////////
        # PUT CODE TO CAPTURE THE IMAGE 3 HERE
        # //////////////////////////////////

        # Turn off the led region 3 for mixing analysis
        try:
            self.serial_model.send_and_wait_ok("led 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0\n")
        except Exception as e:
            self.main_view.show_error(str(e))

        time.sleep(1)

        # Turn on the led region 4 for mixing analysis
        try:
            self.serial_model.send_and_wait_ok("led 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0\n")
        except Exception as e:
            self.main_view.show_error(str(e))

        time.sleep(1)

        # //////////////////////////////////
        # PUT CODE TO CAPTURE THE IMAGE 4 HERE
        # //////////////////////////////////

        # Turn off the led region 4 for mixing analysis
        try:
            self.serial_model.send_and_wait_ok("led 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0\n")
        except Exception as e:
            self.main_view.show_error(str(e))

        time.sleep(1)

        self.main_view.setEnabled(True)

        # //////////////////////////////////
        # PUT CODE TO PROCESS THE IMAGES HERE
        # //////////////////////////////////


    def open_settings(self):
        if self.serial_model is None:
            self.main_view.show_warning("Please connect to serial port first.")
            return
        
        try:
            self.main_view.setEnabled(False)
            self.settings_view.show()
            self.serial_model.send_and_wait_ok("led 1 0 0 0 1 0 0 0 1 0 0 0 1 0 0 0 0\n")
            time.sleep(1) 
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
