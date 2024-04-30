import multiprocessing
from PySide6 import QtWidgets
import sys

from mainwindow import MainWindow
from telem import Telem


if __name__ == "__main__":
    multiprocessing.freeze_support()

    app = QtWidgets.QApplication(sys.argv)

    w = MainWindow(windowTitle="Sausage File Converter")

    app.exec()
    print("Closing...")
    # when app closes, send updates to server before closing properly
    t = Telem()
    try:
        t.files_created = w.ctrl["files_created"]
        t.files_scanned = w.ctrl["files_scanned"]
        t.update_or_create()
    except KeyError:
        pass


# TODO about window! / Licence

# Extra features
# TODO Add markers at the start of each file
# TODO Auto create output folder
