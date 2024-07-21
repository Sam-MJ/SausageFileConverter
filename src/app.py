import multiprocessing
from PySide6 import QtWidgets
import sys

from mainwindow import MainWindow

if __name__ == "__main__":
    multiprocessing.freeze_support()

    app = QtWidgets.QApplication(sys.argv)

    w = MainWindow()
    w.show()

    app.exec()
    print("Closing...")
