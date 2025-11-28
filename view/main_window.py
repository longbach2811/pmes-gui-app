# view/main_window.py
from PyQt6 import QtWidgets
from PyQt6.uic import loadUi
from PyQt6 import QtGui, QtCore
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

    def visualize_image(self, image, q_label):
        if image is None:
            return

        if len(image.shape) == 2:
            h, w = image.shape
            q_img = QtGui.QImage(
                image.data,
                w,
                h,
                w,
                QtGui.QImage.Format.Format_Grayscale8
            )

        elif len(image.shape) == 3:
            # Convert BGR → RGB
            rgb = image[:, :, ::-1] 
            h, w, ch = rgb.shape
            bytes_per_line = ch * w

            q_img = QtGui.QImage(
                rgb.data,
                w,
                h,
                bytes_per_line,
                QtGui.QImage.Format.Format_RGB888
            )

        else:
            self.show_error("Unsupported image format:", image.shape)
            return

        pixmap = QtGui.QPixmap.fromImage(q_img)

        pixmap = pixmap.scaled(
            q_label.width(),
            q_label.height(),
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation
        )

        q_label.setPixmap(pixmap)

    def show_error(self, msg: str):
        QtWidgets.QMessageBox.critical(self, "Error", msg)

    def show_info(self, msg: str):
        QtWidgets.QMessageBox.information(self, "Info", msg)

    def show_warning(self, msg: str):
        QtWidgets.QMessageBox.warning(self, "Warning", msg)

