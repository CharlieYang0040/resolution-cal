import sys
# from PyQt6.QtWidgets import QApplication # PyQt6 -> PySide6
from PySide6.QtWidgets import QApplication # PyQt6 -> PySide6
from ui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 