from PySide6 import QtWidgets, QtCore, QtGui
from pathlib import Path
from worker import Worker
from telem import Telem


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle("SausageFileConverter")
        self.create_menus()
        self.create_main_frame()

    def create_menus(self):
        self.aboutAction = QtGui.QAction("About", self, triggered=self.on_about)
        # self.websiteAction = QtGui.QAction("Website", self, triggered=self.on_website)
        self.help_menu = self.menuBar().addMenu("Help")
        self.help_menu.addAction(self.aboutAction)
        # self.help_menu.addAction(self.websiteAction)

    def create_main_frame(self):
        self.mainWidget = MainWidget(self)
        self.setCentralWidget(self.mainWidget)

    def on_website(self):
        pass

    def on_about(self):
        def openUrl(self):
            url = QtCore.QUrl(
                "https://drive.google.com/drive/folders/1xd2OL913scQhadmyo6mU79cbZ2ikDN5x?usp=sharing"
            )
            if not QtGui.QDesktopServices.openUrl(url):
                QtWidgets.QMessageBox.warning(self, "Open Url", "Could not open url")

        openUrl(self)


class MainWidget(QtWidgets.QWidget):

    submit_signal = QtCore.Signal(str, str, float, float, bool, bool)

    # progress bar input slots and settings.
    @QtCore.Slot(int, str)
    def number_of_files(self, filenum, progress_text):
        self.progress = QtWidgets.QProgressDialog(
            cancelButtonText="Cancel", minimum=0, maximum=filenum
        )
        self.progress.setLabelText(progress_text)
        self.progress.setWindowTitle("Processing...")
        self.progress.setWindowModality(QtCore.Qt.WindowModal)
        self.progress.setMinimumDuration(0)
        self.progress.show()
        self.progress.canceled.connect(self.cancel)

    @QtCore.Slot(int)
    def progress_int(self, prog_int):
        self.progress.setValue(prog_int)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.ctrl = {"break": False, "files_created": 0}

        # create widgets
        self.inputfolder_label = QtWidgets.QLabel("Input Folder")
        self.outputfolder_label = QtWidgets.QLabel("Output Folder")
        self.silenceduration_label = QtWidgets.QLabel("Silence between clips (seconds)")
        self.maxduration_label = QtWidgets.QLabel(
            "Maximum file length to append (seconds)"
        )

        self.inputfolder_input = QtWidgets.QLineEdit()
        self.outputfolder_input = QtWidgets.QLineEdit()
        self.silenceduration_input = QtWidgets.QLineEdit()
        self.maxduration_input = QtWidgets.QLineEdit()

        self.inputfolder_button = QtWidgets.QPushButton("In Browse")
        self.outputfolder_button = QtWidgets.QPushButton("Out Browse")
        self.convert_button = QtWidgets.QPushButton("Sausage!")

        self.copyfiles_checkbox = QtWidgets.QCheckBox(
            "Copy unprocessed files to output folder", self
        )
        self.foldersinfolders_checkbox = QtWidgets.QCheckBox(
            "Process folders in folders", self
        )
        # toolbar
        """ self.toolbar = QtWidgets.QToolBar()
        self.toolbar.add """

        # add widgets to layouts
        layout = QtWidgets.QVBoxLayout()  # vertical layout

        # horizontal layout to place in vertical layout
        input_layout = QtWidgets.QHBoxLayout()
        input_layout.addWidget(self.inputfolder_label)
        input_layout.addWidget(self.inputfolder_input)
        input_layout.addWidget(self.inputfolder_button)

        output_layout = QtWidgets.QHBoxLayout()
        output_layout.addWidget(self.outputfolder_label)
        output_layout.addWidget(self.outputfolder_input)
        output_layout.addWidget(self.outputfolder_button)

        silence_and_maxduration_layout = QtWidgets.QHBoxLayout()
        silence_and_maxduration_layout.addWidget(self.silenceduration_label)
        silence_and_maxduration_layout.addWidget(self.silenceduration_input)
        silence_and_maxduration_layout.addWidget(self.maxduration_label)
        silence_and_maxduration_layout.addWidget(self.maxduration_input)

        checkbox_layout = QtWidgets.QHBoxLayout()
        checkbox_layout.addWidget(self.copyfiles_checkbox)
        checkbox_layout.addWidget(self.foldersinfolders_checkbox)

        layout.addLayout(input_layout)
        layout.addLayout(output_layout)
        layout.addLayout(silence_and_maxduration_layout)
        layout.addLayout(checkbox_layout)
        layout.addWidget(self.convert_button)

        self.setLayout(layout)
        # Set placeholder text
        self.silenceduration_input.setPlaceholderText("0.5")
        self.maxduration_input.setPlaceholderText("infinite")

        # Set Validators
        v = QtGui.QDoubleValidator()
        v.setNotation(QtGui.QDoubleValidator.StandardNotation)
        v.setBottom(0)

        self.silenceduration_input.setValidator(v)
        self.maxduration_input.setValidator(v)

        # Create Worker/Worker thread for long running task
        self.worker = Worker(self.ctrl)
        self.worker_thread = QtCore.QThread()

        self.telem = Telem(self.ctrl)
        self.telem_thread = QtCore.QThread()

        # move to thread and start
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.start()

        self.telem.moveToThread(self.telem_thread)
        self.telem_thread.start()

        # setup signal and slot
        self.submit_signal.connect(self.worker.all_inputs)
        self.submit_signal.connect(self.telem.fetch)
        self.worker.number_of_files.connect(self.number_of_files)
        self.worker.progress.connect(self.progress_int)
        self.worker.processed.connect(self.telem.update_or_create)
        # self.worker.processed.connect() #return futures

        # add Signals to Buttons
        self.inputfolder_button.clicked.connect(self.select_in_folder)
        self.outputfolder_button.clicked.connect(self.select_out_folder)

        self.convert_button.clicked.connect(self.process)

        # Start eventloop... I think
        # self.show()

    def cancel(self):
        self.ctrl["break"] = True

    def select_in_folder(self):
        """Input Folder selection browser"""
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select Input Directory",
            options=QtWidgets.QFileDialog.ShowDirsOnly
            | QtWidgets.QFileDialog.DontResolveSymlinks,
        )

        if folder:
            self.inputfolder_input.setText(folder)

    def select_out_folder(self):
        """Output Folder selection browser"""
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            options=QtWidgets.QFileDialog.ShowDirsOnly
            | QtWidgets.QFileDialog.DontResolveSymlinks,
        )

        if folder:
            self.outputfolder_input.setText(folder)

    def process(self):
        """
        On 'Sausage' button press, validate file path inputs,
        silence duration and maximum file duration before sending to worker thread
        """

        self.ctrl["break"] = False

        def validate(self) -> bool:
            """Validate that both folder paths exist"""
            if not self.inputfolder_input.text() or not self.outputfolder_input.text():
                QtWidgets.QMessageBox.information(
                    self, "Error", "Set an Input and Output file path"
                )
                return False

            if (
                not Path(self.inputfolder_input.text()).exists()
                or not Path(self.outputfolder_input.text()).exists()
            ):
                QtWidgets.QMessageBox.information(
                    self, "Error", "Input or Output file path do not exist"
                )
                return False

            return True

        if validate(self):
            # pass to worker using Signal
            i = self.inputfolder_input.text()
            o = self.outputfolder_input.text()
            # convert inputs to floats to pass them over signal, if they don't exist, create default values.
            if self.silenceduration_input.text():
                sd = float(self.silenceduration_input.text())
            else:
                sd = 0.5

            if self.maxduration_input.text():
                md = float(self.maxduration_input.text())
            else:
                md = 0

            copybool = self.copyfiles_checkbox.isChecked()
            foldersinfolders = self.foldersinfolders_checkbox.isChecked()
            # send to Worker object
            self.submit_signal.emit(i, o, sd, md, copybool, foldersinfolders)
