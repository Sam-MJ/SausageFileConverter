from PySide6 import QtWidgets, QtCore, QtGui
from pathlib import Path

from worker import Worker, ViewWorker
from telem import Telem
from file_tree import TreeModel, FilterProxyModel

import sys
import os


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle("SausageFileConverter")

        # Menu bars are complicated on Mac, just don't use them for now
        if sys.platform != "darwin":
            self.create_menus()

        self.create_main_frame()

    def create_menus(self):
        self.aboutAction = QtGui.QAction("About", self, triggered=self.on_about)
        # self.websiteAction = QtGui.QAction("Website", self, triggered=self.on_website)

        self.help_menu = self.menuBar()
        self.help_menu.setNativeMenuBar(True)
        self.help_menu.addMenu("Help").addAction(self.aboutAction)

        # self.help_menu.addAction(self.websiteAction)

    def create_main_frame(self):
        self.mainWidget = MainWidget(self)
        self.setCentralWidget(self.mainWidget)

    def on_website(self):
        pass

    def on_about(self):
        """Link to docs hosted on google drive"""
        docs_url = os.getenv("DOCS_URL")

        def openUrl(self):
            url = QtCore.QUrl(docs_url)
            if not QtGui.QDesktopServices.openUrl(url):
                QtWidgets.QMessageBox.warning(self, "Open Url", "Could not open url")

        openUrl(self)


class MainWidget(QtWidgets.QWidget):

    submit_signal = QtCore.Signal(
        str, str, float, float, bool, bool, list, str, list, list
    )
    # input folder, output folder, silence duration, maximum duration, copy files, folders in folder, view_filtered_list, append tag, audio_files, non_audio_files.

    # Send files and path to setup TreeModel
    send_dir_to_process_files = QtCore.Signal(Path)

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

    @QtCore.Slot(str, bool, str, str)
    def update_logger(self, function, success, in_path, out_path):
        row_position = self.logger.rowCount()
        self.logger.insertRow(row_position)
        self.logger.setItem(row_position, 0, QtWidgets.QTableWidgetItem(function))
        if success:
            self.logger.item(row_position, 0).setBackground(QtGui.QColor(174, 220, 174))
        else:
            self.logger.item(row_position, 0).setBackground(QtGui.QColor(197, 79, 77))

        self.logger.setItem(row_position, 1, QtWidgets.QTableWidgetItem(in_path))
        self.logger.setItem(row_position, 2, QtWidgets.QTableWidgetItem(out_path))

        self.logger.verticalScrollBar().setValue(
            self.logger.verticalScrollBar().maximum()
        )

    @QtCore.Slot(list)
    def receive_files_to_make_TreeModel(self, files_list):
        self.model = TreeModel(files_list, Path(self.inputfolder_input.text()))
        self.proxy_model.setSourceModel(self.model)
        self.tree_view.setModel(self.proxy_model)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.ctrl = {"break": False, "files_created": 0}

        self.model = TreeModel([], None)
        self.proxy_model = FilterProxyModel()

        # create widgets
        self.inputfolder_label = QtWidgets.QLabel("Input Folder:")
        self.outputfolder_label = QtWidgets.QLabel("Output Folder:")
        self.appendtag_label = QtWidgets.QLabel("Suffix to append to file name:")
        self.exclusionfield_label = QtWidgets.QLabel("Filter files:")
        self.silenceduration_label = QtWidgets.QLabel("Silence between clips (seconds)")
        self.maxduration_label = QtWidgets.QLabel("Maximum file length to append")

        self.tree_view = QtWidgets.QTreeView()
        self.tree_view.setModel(self.proxy_model)
        # fix scroll bars
        self.tree_view.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        tree_header = self.tree_view.header()
        tree_header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        tree_header.setDefaultSectionSize(tree_header.minimumSectionSize())
        tree_header.setStretchLastSection(False)

        self.tree_view.setExpandsOnDoubleClick(False)

        self.logger = QtWidgets.QTableWidget()
        self.logger.setColumnCount(3)
        self.logger.setHorizontalHeaderLabels(["Function", "In_path", "out_path"])
        self.logger.setColumnWidth(0, 100)
        # set other two to stretch
        header = self.logger.horizontalHeader()
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)

        self.inputfolder_input = QtWidgets.QLineEdit()
        self.outputfolder_input = QtWidgets.QLineEdit()
        self.exclusionfield_input = QtWidgets.QLineEdit()
        self.appendtag_input = QtWidgets.QLineEdit()
        self.silenceduration_input = QtWidgets.QLineEdit()
        self.maxduration_input = QtWidgets.QLineEdit()
        self.inputfolder_button = QtWidgets.QPushButton("Browse")
        self.outputfolder_button = QtWidgets.QPushButton("Browse")
        self.convert_button = QtWidgets.QPushButton("Sausage!")

        self.copyfiles_checkbox = QtWidgets.QCheckBox(
            "Copy unprocessed files to output folder", self
        )
        self.foldersinfolders_checkbox = QtWidgets.QCheckBox(
            "Process folders in folders", self
        )
        # default checked
        self.foldersinfolders_checkbox.setChecked(True)

        # add widgets to layouts
        layout = QtWidgets.QVBoxLayout()  # vertical layout

        # horizontal layout to place in vertical layout
        input_options_layout = QtWidgets.QGridLayout()
        input_options_layout.addWidget(self.inputfolder_label, 0, 0)
        input_options_layout.addWidget(self.inputfolder_input, 0, 1)
        input_options_layout.addWidget(self.inputfolder_button, 0, 2)
        input_options_layout.addWidget(self.foldersinfolders_checkbox, 1, 0)

        # exclusion field
        filter_files_layout = QtWidgets.QGridLayout()
        filter_files_layout.addWidget(self.exclusionfield_label, 0, 0)
        filter_files_layout.addWidget(self.exclusionfield_input, 0, 1)

        # output
        output_directory_layout = QtWidgets.QGridLayout()
        output_directory_layout.addWidget(self.outputfolder_input, 3, 1)
        output_directory_layout.addWidget(self.outputfolder_button, 3, 2)
        output_directory_layout.addWidget(self.outputfolder_label, 3, 0)

        side_bar_layout = QtWidgets.QGridLayout()
        side_bar_layout.addWidget(self.silenceduration_label, 0, 0)
        side_bar_layout.addWidget(self.silenceduration_input, 0, 1)
        side_bar_layout.addWidget(self.maxduration_label, 0, 2)
        side_bar_layout.addWidget(self.maxduration_input, 0, 3)
        side_bar_layout.addWidget(self.appendtag_label, 0, 4)
        side_bar_layout.addWidget(self.appendtag_input, 0, 5)
        # checkboxes
        side_bar_layout.addWidget(self.copyfiles_checkbox, 3, 0, 1, 2)

        layout.addLayout(input_options_layout)
        layout.addWidget(self.tree_view)
        layout.addLayout(filter_files_layout)
        layout.addLayout(side_bar_layout)
        layout.addLayout(output_directory_layout)
        layout.addWidget(self.convert_button)
        layout.addWidget(self.logger)

        self.setLayout(layout)
        # Set placeholder text
        self.silenceduration_input.setPlaceholderText("0.5")
        self.maxduration_input.setPlaceholderText("infinite")
        self.outputfolder_input.setPlaceholderText("Default: <input file path>_sausage")
        self.exclusionfield_input.setPlaceholderText(
            "Insert keywords separated with commas"
        )
        self.appendtag_input.setPlaceholderText("e.g. <file name>_sausage")

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

        self.view_worker = ViewWorker(self.ctrl)
        self.view_thread = QtCore.QThread()

        # move to thread and start
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.start()

        self.telem.moveToThread(self.telem_thread)
        self.telem_thread.start()

        self.view_worker.moveToThread(self.view_thread)
        self.view_thread.start()

        # setup signal and slot
        self.submit_signal.connect(self.worker.all_inputs)
        self.worker.number_of_files.connect(self.number_of_files)
        self.worker.progress.connect(self.progress_int)
        self.worker.logger.connect(self.update_logger)
        # self.worker.processed.connect(self.telem.on_process)
        self.worker.progress.connect(self.telem.on_progress)

        self.send_dir_to_process_files.connect(
            self.view_worker.get_files_and_find_variations
        )
        self.view_worker.return_list_of_files_for_TreeModel.connect(
            self.receive_files_to_make_TreeModel
        )

        # add Signals to Buttons
        self.inputfolder_button.clicked.connect(self.select_in_folder)
        self.outputfolder_button.clicked.connect(self.select_out_folder)
        self.exclusionfield_input.textChanged.connect(self.proxy_model.setFilterText)
        self.tree_view.doubleClicked.connect(self.add_item_to_exclusionfield)

        self.convert_button.clicked.connect(self.process)

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

            # long running task so send to ViewWorker to get files, process them and return as a list.
            self.send_dir_to_process_files.emit(Path(folder))

        if not self.outputfolder_input.text():
            self.outputfolder_input.setPlaceholderText(
                self.inputfolder_input.text() + "_sausage"
            )

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

    def add_item_to_exclusionfield(self, item: QtCore.QModelIndex):
        item_name = self.proxy_model.itemData(item)
        self.exclusionfield_input.insert(item_name[0] + ", ")

    def collect_all_data(self, parent_index) -> list:
        """collect filtered file paths from proxy_model"""
        data = []

        model = self.proxy_model

        for row in range(model.rowCount(parent_index)):
            child_index = model.index(row, 0, parent_index)  # Assuming a single column
            item_data = model.data(child_index, QtCore.Qt.ItemDataRole.UserRole)
            data.append(item_data)
            # Recurse for child items
            data.extend(self.collect_all_data(child_index))
        return data

    def process(self):
        """
        On 'Sausage' button press, validate file path inputs,
        silence duration and maximum file duration before sending to worker thread
        """

        self.ctrl["break"] = False

        def validate(self) -> bool:
            """Validate that input folder paths exist and that the output folder either exists or is set to the same as the input folder."""
            if not self.inputfolder_input.text():
                QtWidgets.QMessageBox.information(
                    self, "Error", "Set an Input file path"
                )
                return False

            if not self.outputfolder_input.text():
                self.outputfolder_input = self.inputfolder_input

            # if there's an input or output path, check they exist. input path is already checked above.  output path is allowed to not exist!
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

            # get files used in view from proxy model to pass to worker
            root_index = QtCore.QModelIndex()
            view_filtered_list = self.collect_all_data(root_index)

            append_tag = self.appendtag_input.text()
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
            self.submit_signal.emit(
                i,
                o,
                sd,
                md,
                copybool,
                foldersinfolders,
                view_filtered_list,
                append_tag,
                self.audio_files,
                self.non_audio_files,
            )
