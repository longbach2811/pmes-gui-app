# view/main_window.py
from PyQt6 import QtWidgets
from PyQt6.uic import loadUi
import os

class MainWindow(QtWidgets.QMainWindow):
    """Main Window"""

    def __init__(self):
        super().__init__()
        loadUi(os.path.join(os.path.dirname(__file__), "main_window.ui"), self)

    def get_port(self) -> str:
        return self.port_cb.currentText()  # QComboBox COM

    def get_baudrate(self) -> int:
        return int(self.baudrate_cb.currentText())

    def append_log(self, text: str):
        te = getattr(self, 'log_te', None) or self.findChild(QtWidgets.QTextEdit, 'log_te')
        if te:
            te.append(text)
        else:
            print(text)

    def show_error(self, msg: str):
        QtWidgets.QMessageBox.critical(self, "Error", msg)
