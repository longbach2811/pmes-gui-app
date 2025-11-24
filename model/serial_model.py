# model/serial_model.py
import serial, time
from PyQt6.QtCore import QCoreApplication

class SerialModel:
    def __init__(self, port="COM9", baudrate=115200):
        self.serial = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2)
        self.serial.reset_input_buffer()

    def send_and_wait_ok(self, message: str):

        self.serial.write((message + "\n").encode())
        print(f"[DEBUG] Sent: {message!r}")

        while True:
            QCoreApplication.processEvents()

            line = self.serial.readline().decode(errors='ignore').strip()
            if line != "":
                if line == "OK":
                    return True
                elif line.startswith("ERR"):
                    raise RuntimeError(line)
                else:
                    continue

            time.sleep(0.01)
