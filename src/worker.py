from PySide6 import QtWidgets, QtCore, QtGui
from pathlib import Path
import concurrent.futures
import shutil
from pprint import pprint

import numpy
import soxr
import soundfile
from dataclasses import dataclass

import utils
import exceptions
from metadata_v2 import Metadata_Assembler
from file_tree import TreeModel

import mdutils
import datetime
import sys
import os
import subprocess
import platformdirs


class ViewWorker(QtCore.QObject):
    return_list_of_files_for_TreeModel = QtCore.Signal(
        list, list, list
    )  # flattened list of variations, audio files, non audio files

    @QtCore.Slot(list, Path)
    def get_files_and_find_variations(self, root_directory):
        """long running task from mainwindow widget. get files, tokenize and return a flat file of all the variations to be put into the tree view"""
        self.audio_files, self.non_audio_files = utils.get_files(Path(root_directory))
        self.ctrl["files_scanned"] = len(self.audio_files)

        tokenized_files = utils.split_paths_to_tokens(self.audio_files)

        files_with_variations = utils.find_files_with_variations(tokenized_files)

        # flatten to put into Tree Model
        flat_list_of_variations = []
        for listoflist in files_with_variations:
            for lst in listoflist:
                flat_list_of_variations.append(lst)

        self.return_list_of_files_for_TreeModel.emit(
            flat_list_of_variations, self.audio_files, self.non_audio_files
        )

    def __init__(self, ctrl) -> None:
        super().__init__(parent=None)
        self.ctrl = ctrl
        self.ctrl["files_scanned"] = 0

    def show_loading_message(self):
        self.msg.show()

    def close_loading_message(self):
        self.msg.close()


class ReportObject:

    def __init__(self, single_variation_list):
        self.single_variation_list: list[Path] = single_variation_list
        self.original_file_name: Path = self.single_variation_list[0]
        self.sample_rates: list[int] = []
        self.channels_list: list[int] = []
        self.error = None
        self.new_file_name_path: Path = None


class Worker(QtCore.QObject):

    def __init__(self, ctrl) -> None:
        super().__init__(parent=None)
        self.ctrl = ctrl
        self.ctrl["files_scanned"] = 0
        self.ctrl["files_created"] = 0

        self.create_report_path()
        self.report = None
        self.errored_files: list[ReportObject] = []

    number_of_files = QtCore.Signal(int, str)
    progress = QtCore.Signal(int)
    logger = QtCore.Signal(str, bool, str, str)

    @QtCore.Slot(str)
    def all_inputs(
        self,
        inputfolder_input,
        outputfolder_input,
        silenceduration_input,
        maxduration_input,
        copybool,
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
        self.view_filtered_list = view_filtered_list
        self.append_tag = append_tag
        self.audio_files = audio_files
        self.non_audio_files = non_audio_files

        # if there was no output folder given, it is set to the same as the input folder, this is then appended with _sausage
        if self.input_folder == self.output_folder:
            self.output_folder = utils.create_default_file_path(self.output_folder)

        # create a new report each time a folder is selected
        self.create_md_report()

        tokenized = utils.split_paths_to_tokens(view_filtered_list)
        files_with_variations = utils.find_files_with_variations(tokenized)

        # sort durations
        correct_duration_list = self.remove_too_long_files(
            files_with_variations, self.max_duration
        )

        # sort files to be copied, this is done before appending so that failed files can be added to it.
        if copybool is True:
            self.files_without_variations = utils.find_files_without_variations(
                correct_duration_list, audio_files
            )

            self.files_without_variations.extend(self.non_audio_files)

        # append
        if len(correct_duration_list) > 0:
            self.file_append_pool(correct_duration_list)

        # copy to out
        if copybool is True:
            if len(self.files_without_variations) > 0:
                self.file_copy_pool(self.files_without_variations)

    def create_report_path(self):
        """If a reports folder hasn't been created in appdata, create one"""
        appname = "SausageFileConverter"
        appauthor = "SoundSpruce"

        path = platformdirs.user_data_path(appname, appauthor, ensure_exists=False)
        Path(path).mkdir(parents=True, exist_ok=True)

        self.report_path = path

    def create_md_report(self):
        """Initialise the creation of a markdown report and empty list of files with errors"""
        self.report = mdutils.MdUtils(
            file_name=f'{self.report_path}/SausageFileConverterReport_{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}',
            title="Sausage File Converter Report",
        )

        self.errored_files: list[ReportObject] = []

    def add_converted_files_to_report(self, reportobj: ReportObject):
        """Add the name and length of the output file and a list of the files that went into it."""
        bullet_points = []
        channel_max = max(reportobj.channels_list)
        sample_rate_max = max(reportobj.sample_rates)

        # convert the list of file paths to strings containing the original name, channel count, samplerate and if they have been converted.
        for i in range(len(reportobj.single_variation_list)):
            original_file_name = str(reportobj.single_variation_list[i])
            channel = str(reportobj.channels_list[i])
            sample_rate = str(reportobj.sample_rates[i])

            if int(channel) < channel_max:
                channel += f" -> Converted to: {channel_max}"

            if int(sample_rate) < sample_rate_max:
                sample_rate += f" -> Converted to: {sample_rate_max}"

            bullet_points.append(
                f"{original_file_name} - Channels: {channel} - Sample Rate: {sample_rate}"
            )

        with soundfile.SoundFile(reportobj.new_file_name_path, "r") as s:
            length = s.frames / s.samplerate
            new_length = datetime.timedelta(seconds=int(length))

        self.report.new_list(
            [
                f"{str(reportobj.new_file_name_path)}, Length: {new_length}",
                bullet_points,
            ]
        )

    def add_copied_files_to_report(self, files_without_variations):

        self.report.new_header(level=1, title="Copied files")
        path_to_str = [str(p) for p in files_without_variations]

        self.report.new_list([path_to_str])

    def add_errors_to_report(self):

        self.report.new_header(level=1, title="Files that caused Errors")

        obj_to_str = [
            f"{e.original_file_name}: {str(e.error)}" for e in self.errored_files
        ]
        self.report.new_list(obj_to_str)

    def show_reports_folder(self):
        """
        Operating systems need different commands to launch an explorer/finder, find what the platform is and then use the appropriate one.
        """
        try:
            # if MacOS
            if sys.platform.startswith("darwin"):
                subprocess.call(("open", self.report_path))
            # if non-posix, i.e. Windows
            elif os.name == "nt":
                os.startfile(self.report_path)
            # if Linux
            elif os.name == "posix":
                subprocess.call(("xdg-open", self.report_path))
        except Exception as e:
            print(f"Failed to open folder: {e}")

    def remove_too_long_files(
        self, files_with_variations: list[list[Path]], max_duration
    ) -> list:
        """Remove files that are too long from the files_with_variations list of lists"""
        correct_duration_list = []
        count = 0

        # if the max duration GUI box has been left empty, return the full list.
        if max_duration == 0:
            return files_with_variations

        # flatten list to get count to pass to progress bar
        files_with_vars = []
        for files in files_with_variations:
            files_with_vars.extend(files)
        self.number_of_files.emit(len(files_with_vars), "Analysing...")

        for variations in files_with_variations:
            variations_of_correct_size = []
            for file in variations:

                # if cancel button pressed
                if self.ctrl["break"] is True:
                    self.progress.emit(len(files_with_vars))
                    return files_with_variations

                count += 1
                # read file length metadata and append to list if it's small enough
                try:
                    with soundfile.SoundFile(file, "r") as s:
                        length = s.frames / s.samplerate
                        if length < max_duration:
                            variations_of_correct_size.append(file)
                except soundfile.LibsndfileError:
                    pass

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

        reportobj = ReportObject(single_variation_list)

        try:
            reportobj.new_file_name_path = self.file_append(
                reportobj,
                self.silence_duration,
                self.input_folder,
                self.output_folder,
                self.append_tag,
            )
            self.write_metadata(
                reportobj.original_file_name, reportobj.new_file_name_path
            )

        # if writing file error
        except (
            soundfile.LibsndfileError,
            exceptions.ChannelCountError,
            exceptions.BitDepthError,
        ) as e:
            # terminal out
            print(f"{e}: file: {reportobj.original_file_name}")
            # GUI out
            self.logger.emit("Write", False, str(reportobj.original_file_name), str(e))
            # Report out
            reportobj.error = e
            self.errored_files.append(reportobj)

            if self.copybool:
                self.files_without_variations.extend(single_variation_list)

        # if write metadata file error
        except (
            exceptions.InvalidRIFFFileException,
            exceptions.FormatChunkError,
            exceptions.InvalidWavFileException,
            exceptions.EmptyFileExeption,
            exceptions.InvalidSizeValue,
            exceptions.FormatChunkError,
            exceptions.SubchunkIDParsingError,
        ) as e:
            # terminal out
            print(f"{e}: file: {reportobj.original_file_name}")
            # GUI out
            self.logger.emit("Write", False, str(reportobj.original_file_name), str(e))
            # Report out
            reportobj.error = e
            self.errored_files.append(reportobj)

            if self.copybool:
                self.files_without_variations.extend(single_variation_list)
            # delete file that was created by successful file write
            Path.unlink(reportobj.new_file_name_path)

        except Exception as e:
            # terminal out
            print(f"Unexpected Error: {e}: file {reportobj.original_file_name}")
            # GUI out
            self.logger.emit("Write", False, str(reportobj.original_file_name), e)
            # Report out
            reportobj.error = e
            self.errored_files.append(reportobj)

            if self.copybool:
                self.files_without_variations.extend(single_variation_list)

        else:
            print("Write: ", str(reportobj.new_file_name_path))
            self.logger.emit(
                "Write",
                True,
                str(reportobj.original_file_name),
                str(reportobj.new_file_name_path),
            )

            self.add_converted_files_to_report(reportobj)

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

    def file_append_pool(self, files_with_correct_size_variations: list[list[Path]]):
        """create multi-process pool to append files"""
        # Progress bar setup, min = count = 0, max = number of files
        self.count = 0
        self.number_of_files.emit(
            len(files_with_correct_size_variations), "Appending..."
        )
        self.report.new_header(level=1, title="Converted Files")

        with concurrent.futures.ProcessPoolExecutor() as p_executor:  # using a context manager joins, so blocks
            futures = {
                p_executor.submit(self.concatination_handler(single_variation_list=lst))
                for lst in files_with_correct_size_variations
                if self.ctrl["break"] is False
            }

            # When all are done, send the last percent to the update bar
            concurrent.futures.wait(futures, return_when="ALL_COMPLETED")
            self.progress.emit(len(files_with_correct_size_variations))

        # if there is no copying stage, all processing is finished and the report can be generated.
        # if not it will finish after copying stage.
        if not self.copybool:
            if self.errored_files:
                self.add_errors_to_report()

            self.report.create_md_file()

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

        if self.errored_files:
            self.add_errors_to_report()
        self.add_copied_files_to_report(files_without_variations)
        self.report.create_md_file()

    def file_append(
        self,
        reportobj: ReportObject,
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

        for file in reportobj.single_variation_list:
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

                reportobj.sample_rates.append(s.samplerate)
                # if there's only one channel it will be an empty array, if it's 2 or more it's (channel_count,)
                if len(data.shape[1:]) == 0:
                    reportobj.channels_list.append(1)
                else:
                    reportobj.channels_list.append(data.shape[1:][0])

        # check if blocks have the same sample rate and channel count, if not take the highest.
        for block in list_of_sound_objects:
            highest_sample_rate = list_of_sound_objects[0].samplerate
            highest_channel_count = list_of_sound_objects[0].channels
            subtype = list_of_sound_objects[0].subtype

            if block.samplerate > highest_sample_rate:
                highest_sample_rate = block.samplerate

            # print(block.channels)
            if block.channels > highest_channel_count:
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
                # In the future it may be good to support more channel conversions

        # create the output path

        file_name_path = utils.clean_output_name(reportobj.single_variation_list)

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

        return new_filename_path
