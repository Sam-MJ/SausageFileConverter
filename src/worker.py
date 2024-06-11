from PySide6 import QtWidgets, QtCore, QtGui
from pathlib import Path
import concurrent.futures
import shutil
from pprint import pprint
import taglib
import traceback

import utils
import exceptions
from metadata_v2 import Metadata_Assembler


class Worker(QtCore.QObject):

    def __init__(self, ctrl) -> None:
        super().__init__(parent=None)
        self.ctrl = ctrl
        self.ctrl["files_scanned"] = 0
        self.ctrl["files_created"] = 0

    number_of_files = QtCore.Signal(int, str)
    progress = QtCore.Signal(int)
    processed = QtCore.Signal(bool)

    @QtCore.Slot(str)
    def all_inputs(
        self,
        inputfolder_input,
        outputfolder_input,
        silenceduration_input,
        maxduration_input,
        copybool,
        foldersinfolders,
        exclusion_list,
        append_tag,
    ):
        self.input_folder = Path(inputfolder_input)
        self.output_folder = Path(outputfolder_input)
        self.silence_duration = silenceduration_input
        self.max_duration = maxduration_input
        self.copybool = copybool
        self.foldersinfolders = foldersinfolders
        self.exclusion_list = exclusion_list
        self.append_tag = append_tag

        input_files = utils.get_files(self.input_folder, self.foldersinfolders)
        audio_files = input_files[0]
        self.ctrl["files_scanned"] = len(audio_files)
        tokenized = utils.file_tokenization(audio_files)
        files_with_variations = utils.find_files_with_variations(tokenized)

        # sort excluded files
        files_with_variations_post_exclude = utils.remove_files_with_exclude(
            files_with_variations=files_with_variations, exclude_list=exclusion_list
        )

        # sort durations
        correct_duration_list = self.remove_too_short_files(
            files_with_variations_post_exclude
        )

        # append
        if len(correct_duration_list) > 0:
            self.file_append_pool(correct_duration_list)

        # copy to out
        if copybool is True:
            files_without_variations = utils.find_files_without_variations(
                correct_duration_list, audio_files
            )
            non_audio_files = input_files[1]
            files_without_variations.extend(non_audio_files)
            print(files_without_variations)

            if len(files_without_variations) > 0:
                self.file_copy_pool(files_without_variations)

    def remove_too_short_files(self, files_with_variations: list) -> list:
        """Remove files that are too short from the files_with_variations list of lists"""
        correct_duration_list = []
        count = 0

        # if the max duration GUI box has been left empty, return the full list.
        if self.max_duration == 0:
            return files_with_variations

        # flatten list to get count to pass to progress bar
        files_with_vars = []
        for files in files_with_variations:
            files_with_vars.extend(files)
        self.number_of_files.emit(len(files_with_vars), "Analysing...")

        for variations in files_with_variations:
            # if cancel button pressed
            if self.ctrl["break"] is True:
                return files_with_variations
            variations_of_correct_size = []

            for file in variations:
                count += 1
                # read file length metadata and append to list if it's small enough
                with taglib.File(file) as f:
                    if f.length < self.max_duration:
                        variations_of_correct_size.append(file)

                # update progress bar
                self.progress.emit(count)

            if (
                len(variations_of_correct_size) > 1
            ):  # don't add empty list or list of one
                correct_duration_list.append(variations_of_correct_size)

        return correct_duration_list

    def copy_files_without_variations_to_out(self, file: Path) -> None:
        """copy any files that didn't have variations to their output folder."""
        # emit before copy leaves the last count not emmited.
        # this is important so it can be emmited by wait() instead, which calls after all tasks are done
        self.progress.emit(self.count)
        self.count += 1

        out_path = utils.create_output_path(file, self.input_folder, self.output_folder)
        # check if the file is a file or a folder
        if file.is_file():
            utils.create_parent_folders(out_path)
            shutil.copy(file, out_path.parent)
        elif file.is_dir():
            shutil.copytree(file, out_path)

        print(f"Copy: {file} to: {out_path}")

    def concatination_handler(self, single_variation_list: list):
        """Take a list of files to be appended together, create a new file from it.
        Read metadata from the first of the old files and write to the new one."""
        # sort variations
        original_file_name = single_variation_list[0]

        try:
            new_file_name = utils.file_append(
                single_variation_list,
                self.silence_duration,
                self.input_folder,
                self.output_folder,
                self.append_tag,
            )

            self.write_metadata(original_file_name, new_file_name)
        except (
            exceptions.SampleRateError,
            exceptions.BitDepthError,
            exceptions.InvalidRIFFFileException,
            exceptions.FormatChunkError,
            exceptions.InvalidWavFileException,
            exceptions.EmptyFileExeption,
            exceptions.InvalidSizeValue,
        ) as e:
            print(f"{e}: file: {original_file_name}")

        except Exception as e:
            print(f"Unexpected Error: {e}: file {original_file_name}")
            print(traceback.print_exc())

    def write_metadata(self, original_file_name: Path, new_file_name: Path) -> None:
        """Write the metadata from the first file in the list (of the un-appended files) to the new sausage file"""
        # write metadata chunks to new file
        md = Metadata_Assembler(
            original_filename=original_file_name, new_filename=new_file_name
        )
        md.assemble()

        # count is emmited up to n-1, then last count is emitted by wait()
        self.progress.emit(self.count)
        self.count += 1
        self.ctrl["files_created"] += 1

    def file_append_pool(self, files_with_correct_size_variations):
        """create multi-process pool to append files"""
        # Progress bar setup
        self.count = 0
        self.number_of_files.emit(
            len(files_with_correct_size_variations), "Appending..."
        )

        with concurrent.futures.ProcessPoolExecutor() as p_executor:  # using a context manager joins, so blocks
            futures = {
                p_executor.submit(self.concatination_handler(single_variation_list=lst))
                for lst in files_with_correct_size_variations
                if self.ctrl["break"] is False
            }

            # When all are done, send the last percent to the update bar
            concurrent.futures.wait(futures, return_when="ALL_COMPLETED")
            # self.processed.emit(True)
            self.progress.emit(len(files_with_correct_size_variations))

    def file_copy_pool(self, files_without_variations):
        """create multi-thread pool to copy files"""
        # Progress bar setup
        self.count = 0
        self.number_of_files.emit(len(files_without_variations), "Copying...")

        with concurrent.futures.ThreadPoolExecutor() as t_executor:

            futures = {
                t_executor.submit(self.copy_files_without_variations_to_out(file))
                for file in files_without_variations
                if self.ctrl["break"] is False
            }

            # When all are done, send the last percent to the update bar
            concurrent.futures.wait(futures, return_when="ALL_COMPLETED")
            self.progress.emit(len(files_without_variations))
