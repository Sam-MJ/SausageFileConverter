import multiprocessing
from PySide6 import QtWidgets
import sys

from mainwindow import MainWindow

if __name__ == "__main__":
    multiprocessing.freeze_support()

    app = QtWidgets.QApplication(sys.argv)

    w = MainWindow(windowTitle="Sausage File Converter")

    app.exec()
    print("Closing...")
    # when app closes, send updates to server before closing properly

# TODO about window! / Licence

# Extra features
# TODO Add markers at the start of each file
# TODO Auto create output folder
