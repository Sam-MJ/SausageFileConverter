from PySide6 import QtWidgets, QtCore, QtGui
from pathlib import Path
import concurrent.futures
import shutil
from pprint import pprint
import taglib
import traceback

import numpy
import soxr
import soundfile
from dataclasses import dataclass

import utils
import exceptions
from metadata_v2 import Metadata_Assembler
from file_tree import TreeModel


class ViewWorker(QtCore.QObject):
    return_list_of_files_for_TreeModel = QtCore.Signal(list)

    @QtCore.Slot(list, Path)
    def get_files_and_find_variations(self, root_directory):
        """long running task from mainwindow widget. get files, tokenize and return a flat file of all the variations to be put into the tree view"""
        self.audio_files, self.non_audio_files = utils.get_files(Path(root_directory))
        self.ctrl["files_scanned"] = len(self.audio_files)

        tokenized_files = utils.file_tokenization(self.audio_files)

        files_with_variations = utils.find_files_with_variations(tokenized_files)

        # flatten to put into Tree Model
        flat = []
        for listoflist in files_with_variations:
            for lst in listoflist:
                flat.append(lst)

        self.return_list_of_files_for_TreeModel.emit(flat)

    def __init__(self, ctrl) -> None:
        super().__init__(parent=None)
        self.ctrl = ctrl
        self.ctrl["files_scanned"] = 0


class Worker(QtCore.QObject):

    def __init__(self, ctrl) -> None:
        super().__init__(parent=None)
        self.ctrl = ctrl
        self.ctrl["files_scanned"] = 0
        self.ctrl["files_created"] = 0

    number_of_files = QtCore.Signal(int, str)
    progress = QtCore.Signal(int)
    processed = QtCore.Signal(bool)
    logger = QtCore.Signal(str, bool, str, str)

    @QtCore.Slot(str)
    def all_inputs(
        self,
        inputfolder_input,
        outputfolder_input,
        silenceduration_input,
        maxduration_input,
        copybool,
        foldersinfolders,
        view_filtered_list,
        append_tag,
        audio_files,
        non_audio_files,
    ):
        self.input_folder = Path(inputfolder_input)
        self.output_folder = Path(outputfolder_input)
        self.silence_duration = silenceduration_input
        self.max_duration = maxduration_input
        self.copybool = copybool
        self.foldersinfolders = foldersinfolders
        self.view_filtered_list = view_filtered_list
        self.append_tag = append_tag
        self.audio_files = audio_files
        self.non_audio_files = non_audio_files

        # if there was no output folder given, it is set to the same as the input folder, this is then appended with _sausage
        if self.input_folder == self.output_folder:
            self.output_folder = utils.create_default_file_path(self.output_folder)

        tokenized = utils.file_tokenization(view_filtered_list)
        files_with_variations = utils.find_files_with_variations(tokenized)

        # sort durations
        correct_duration_list = self.remove_too_short_files(files_with_variations)

        # append
        if len(correct_duration_list) > 0:
            self.file_append_pool(correct_duration_list)

        # copy to out
        if copybool is True:
            files_without_variations = utils.find_files_without_variations(
                correct_duration_list, audio_files
            )

            files_without_variations.extend(self.non_audio_files)

            if len(files_without_variations) > 0:
                self.file_copy_pool(files_without_variations)

    def remove_too_short_files(self, files_with_variations: list[list[Path]]) -> list:
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
            # if folder already exists, don't copy it.
            if not out_path.exists():
                shutil.copytree(file, out_path)

        print(f"Copy: {file} to: {out_path}")
        self.logger.emit("Copy", True, str(file), str(out_path))

    def concatination_handler(self, single_variation_list: list[Path]):
        """Take a list of files to be appended together, create a new file from it.
        Read metadata from the first of the old files and write to the new one."""
        # sort variations
        original_file_name = single_variation_list[0]

        try:
            new_file_name = self.file_append(
                single_variation_list,
                self.silence_duration,
                self.input_folder,
                self.output_folder,
                self.append_tag,
            )

            self.write_metadata(original_file_name, new_file_name)
        except (
            soundfile.LibsndfileError,
            exceptions.ChannelCountError,
            exceptions.BitDepthError,
            exceptions.InvalidRIFFFileException,
            exceptions.FormatChunkError,
            exceptions.InvalidWavFileException,
            exceptions.EmptyFileExeption,
            exceptions.InvalidSizeValue,
            exceptions.FormatChunkError,
            exceptions.SubchunkIDParsingError,
        ) as e:
            print(f"{e}: file: {original_file_name}")
            self.logger.emit("Write", False, str(original_file_name), str(e))

        except Exception as e:
            print(f"Unexpected Error: {e}: file {original_file_name}")
            print(traceback.print_exc())
            self.logger.emit("Write", False, str(original_file_name), e)

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

    def file_append(
        self,
        single_variation_list: list,
        silence_duration: float,
        input_folder: Path,
        output_folder: Path,
        append_tag: str,
    ) -> Path:
        """
        Take a list of one set of files with variations i.e impact_01.wav, impact_02.wav, impact_03.wav and append them together.
        return the new file name and export the new file to its output folder.
        """

        @dataclass
        class audio_object:
            samplerate: int
            audio_data: numpy.ndarray
            subtype: str
            channels: str
            dtype: str

        # append file to combined
        list_of_sound_objects = []
        dtype = "float64"  # default dtype soundfile uses to read.

        for file in single_variation_list:
            with soundfile.SoundFile(file, "r") as s:
                data = s.read()
                list_of_sound_objects.append(
                    audio_object(
                        samplerate=s.samplerate,
                        audio_data=data,
                        subtype=s.subtype,
                        channels=data.shape[1:],
                        dtype=data.dtype,
                    )
                )

        # check if blocks have the same sample rate and channel count, if not take the highest.
        for block in list_of_sound_objects:
            highest_sample_rate = list_of_sound_objects[0].samplerate
            highest_channel_count = list_of_sound_objects[0].channels
            subtype = list_of_sound_objects[0].subtype

            if block.samplerate > highest_sample_rate:
                highest_sample_rate = block.samplerate

            # print(block.channels)
            if block.channels > highest_channel_count:
                # TODO automatically take highest channel count and convert the rest
                highest_channel_count = block.channels

            if block.subtype != subtype:
                raise exceptions.BitDepthError(
                    "Error: Variations are not of the same bit depth"
                )

        for block in list_of_sound_objects:
            # resample any blocks that are below the highest sample rate to the highest sample rate
            if block.samplerate == highest_sample_rate:
                continue
            block.audio_data = soxr.resample(
                block.audio_data, block.samplerate, highest_sample_rate, quality="VHQ"
            )

        for block in list_of_sound_objects:
            # add channels to any below highest channel count
            if block.channels == highest_channel_count:
                continue

            if not block.channels and highest_channel_count[0] == 2:
                # if mono to stereo
                """multichannel audio data:
                first convert 1d array [1,2,3] to:
                [[1]
                [2]
                [3]]
                then horizonally stack to get
                [[1, 1],
                [2, 2],
                [3, 3]]
                """
                block.audio_data = numpy.hstack(
                    (block.audio_data.reshape(-1, 1), block.audio_data.reshape(-1, 1))
                )
            else:
                raise exceptions.ChannelCountError(
                    "Error: Variations have different channel counts that are not mono or stereo"
                )

        # create the output path
        file_name_path = single_variation_list[0]
        new_filename_path = utils.create_output_path(
            file_name_path, input_folder, output_folder
        )
        new_filename_path = utils.add_end_tag_to_filename(
            new_filename_path, tag=append_tag
        )

        # check if it requires new parent folders
        utils.create_parent_folders(new_filename_path)

        # get audio data from objects
        audio_chunks = [audio.audio_data for audio in list_of_sound_objects]

        # create silence block
        silence_samples_number = highest_sample_rate * silence_duration
        shape = (int(silence_samples_number),) + highest_channel_count
        silence_block = numpy.zeros((shape), dtype)

        # insert into list of files, alternating indexes, i.e 1,3,5,7
        for i in range(1, len(audio_chunks) * 2 - 1, 2):
            audio_chunks.insert(i, silence_block)

        data = numpy.concatenate(audio_chunks)
        soundfile.write(new_filename_path, data, highest_sample_rate, subtype=subtype)

        print("Write: ", str(new_filename_path))
        self.logger.emit("Write", True, str(file_name_path), str(new_filename_path))

        return new_filename_path
