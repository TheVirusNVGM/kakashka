import sys
from PySide6 import QtWidgets
from ui.main_window import MainWindow


def main():
    app = QtWidgets.QApplication(sys.argv)
    with open("resources/dark_theme.qss") as f:
        app.setStyleSheet(f.read())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
