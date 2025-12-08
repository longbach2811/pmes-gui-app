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

        self.settings = QtCore.QSettings("pmes-app", "pmes-gui")

        self.load_settings()

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
            """
            Displays a NumPy array (image) in a QLabel (q_label).
            Handles 8-bit grayscale and 24-bit BGR (converts to RGB).
            """
            if image is None:
                return

            # Ensure the image array is C-contiguous. 
            # QImage needs a contiguous memory buffer.
            if not image.flags['C_CONTIGUOUS']:
                image = image.copy(order='C')

            q_img = None

            if len(image.shape) == 2:
                # Grayscale image (H, W)
                h, w = image.shape
                data = image.data

                q_img = QtGui.QImage(
                    data.tobytes(), # Convert memoryview to bytes
                    w,
                    h,
                    w, # bytesPerLine = width (1 byte per pixel)
                    QtGui.QImage.Format.Format_Grayscale8
                )

            elif len(image.shape) == 3:
                # Color image (H, W, CH). Assuming BGR input from common libraries like OpenCV.
                # Convert BGR (NumPy default) to RGB (QImage default)
                rgb = image[:, :, ::-1] 
                
                # The slicing operation (::-1) makes the array non-contiguous. 
                # Must copy the data into a C-contiguous buffer before passing to QImage.
                rgb_contiguous = rgb.copy(order='C') 

                h, w, ch = rgb_contiguous.shape
                bytes_per_line = ch * w

                q_img = QtGui.QImage(
                    rgb_contiguous.data.tobytes(), # Convert memoryview to bytes
                    w,
                    h,
                    bytes_per_line,
                    QtGui.QImage.Format.Format_RGB888
                )

            else:
                self.show_error(f"Unsupported image format: {image.shape}")
                return

            if q_img:
                # Convert QImage to QPixmap for display
                pixmap = QtGui.QPixmap.fromImage(q_img)

                # Scale the pixmap to fit the QLabel while maintaining aspect ratio
                pixmap = pixmap.scaled(
                    q_label.width(),
                    q_label.height(),
                    QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                    QtCore.Qt.TransformationMode.SmoothTransformation
                )

                # Display the scaled image
                q_label.setPixmap(pixmap)

    def show_error(self, msg: str):
        QtWidgets.QMessageBox.critical(self, "Error", msg)

    def show_info(self, msg: str):
        QtWidgets.QMessageBox.information(self, "Info", msg)

    def show_warning(self, msg: str):
        QtWidgets.QMessageBox.warning(self, "Warning", msg)

    def save_settings(self):
        self.settings.setValue("serial/port", self.port_cb.currentText())
        self.settings.setValue("serial/baud", self.baudrate_cb.currentText())
    
    def load_settings(self):
        port = self.settings.value("serial/port", "")
        baudrate = self.settings.value("serial/baud", "115200")
        index = self.port_cb.findText(port)
        if index != -1:
            self.port_cb.setCurrentIndex(index)

        index = self.baudrate_cb.findText(baudrate)
        if index != -1:
            self.baudrate_cb.setCurrentIndex(index)

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)
