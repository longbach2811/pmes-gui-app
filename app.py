# app.py
import sys
from PyQt6.QtWidgets import QApplication
from controller.main_controller import MainController
from configs.load_config import load_config

def main():
    app = QApplication(sys.argv)
    config = load_config(path="configs/config.yaml")
    controller = MainController(config)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
