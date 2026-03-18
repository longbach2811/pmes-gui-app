# view/main_window.py
from PyQt6 import QtWidgets
from PyQt6.uic import loadUi
from PyQt6 import QtGui, QtCore
from matplotlib.backends.backend_agg import FigureCanvasAgg
import numpy as np
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
    
    def get_comminution_chewing_cycles(self) -> int:
        if int(self.cycles_b.text()) <= 0:
            raise ValueError("Please enter a valid number of chewing cycles")
        return str(self.cycles_b.text()) 
    
    def get_mixing_chewing_cycles_side_1(self) -> int:
        if int(self.cycles_b_2.text()) <= 0:
            raise ValueError("Please enter a valid number of chewing cycles for side 1")
        return str(self.cycles_b_2.text())

    def get_mixing_chewing_cycles_side_2(self) -> int:
        if int(self.cycles_b_3.text()) <= 0:
            raise ValueError("Please enter a valid number of chewing cycles for side 2")
        return str(self.cycles_b_3.text())
        
    def get_name(self)->str:
        name = self.name_box.text().strip()
        if not name: 
            raise ValueError("Please enter name")
        return name
    
    def get_gender(self)->str:
        return self.gender_cb.currentText() 
    
    def get_age(self)->str:
        age = self.age_sb.value() 
        if age <= 0:
            raise ValueError("Please enter a valid age")
        return str(age)  

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

    def visualize_figure(self, fig, q_label, dpi=500):
        """
        Render matplotlib normally, then scale to QLabel.
        """

        # --- Make figure high-res ---
        fig.set_dpi(dpi)

        fig.tight_layout(pad=0.6)

        canvas = FigureCanvasAgg(fig)
        canvas.draw()

        buf = np.asarray(canvas.buffer_rgba())
        h, w, _ = buf.shape

        q_img = QtGui.QImage(
            buf.data,
            w,
            h,
            4 * w,
            QtGui.QImage.Format.Format_RGBA8888
        )

        pixmap = QtGui.QPixmap.fromImage(q_img)

        # --- Scale to QLabel ---
        pixmap = pixmap.scaled(
            q_label.width(),
            q_label.height(),
            QtCore.Qt.AspectRatioMode.IgnoreAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation
        )

        q_label.setPixmap(pixmap)
        
    def update_particle_size_stats_ranges(
        self,
        particle_sizes,
        list_widget: QtWidgets.QListWidget,
        bin_size=0.01
    ):
        particle_sizes = np.asarray(particle_sizes)

        if particle_sizes.size == 0:
            list_widget.clear()
            list_widget.addItem("No particle sizes provided.")
            return

        min_val = np.floor(particle_sizes.min() / bin_size) * bin_size
        max_val = np.ceil(particle_sizes.max() / bin_size) * bin_size

        bins = np.arange(min_val, max_val + bin_size, bin_size)
        hist, bin_edges = np.histogram(particle_sizes, bins=bins)

        list_widget.clear()
        list_widget.addItem(f"Total {particle_sizes.size} particles per {bin_size:.2f} mm range:")

        for i in range(len(hist)):
            if hist[i] == 0:
                continue 

            list_widget.addItem(
                f"{bin_edges[i]:.2f}–{bin_edges[i+1]:.2f} mm: {hist[i]} particles"
            )

    
    def open_file_dialog(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select a file",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.tiff)"
        )
        return file_path

    def show_error(self, msg: str):
        QtWidgets.QMessageBox.critical(self, "Error", msg)

    def show_info(self, msg: str):
        QtWidgets.QMessageBox.information(self, "Info", msg)

    def show_warning(self, msg: str):
        QtWidgets.QMessageBox.warning(self, "Warning", msg)

    def show_confirmation_dialog(self, msg: str) -> bool:
        """Shows a confirmation dialog with Save and Cancel buttons. Returns True if Save is clicked."""
        reply = QtWidgets.QMessageBox.question(self, 'Xác nhận lưu', msg,
                                               QtWidgets.QMessageBox.StandardButton.Save | QtWidgets.QMessageBox.StandardButton.Cancel,
                                               QtWidgets.QMessageBox.StandardButton.Cancel)
        return reply == QtWidgets.QMessageBox.StandardButton.Save

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
