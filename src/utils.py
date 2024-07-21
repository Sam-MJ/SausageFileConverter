from pathlib import Path
import re
import soundfile
import numpy
import math
import natsort
import soxr
from dataclasses import dataclass

import exceptions

# from src import exceptions

from pprint import pprint


def get_files(in_folder_path: Path, foldersinfolders: bool) -> tuple[list, list]:
    """Get files with audio file suffixes from folder directory"""
    audio_file_names = []
    non_audio_file_names = []

    if foldersinfolders:
        file_paths = in_folder_path.rglob("*")  # .iterdir() - only one folder
    else:
        file_paths = in_folder_path.iterdir()

    # wav only for now, change == types to 'in types'
    """ types = (
        ".wav",
        ".flac",
        ".mp3",
        ".ogg",
        ".opus",
    ) """

    types = ".wav"

    for file in file_paths:
        if foldersinfolders:
            # if True, you cannot have a folder in non_audio_file_names
            if file.is_file():
                if file.suffix.lower() == types and file.name[0:2] != "._":
                    # On windows, MAC OSX has hidden temp Wav files that start with ._ They don't have any useable content.
                    audio_file_names.append(file)
                else:
                    non_audio_file_names.append(file)
        else:
            if (
                file.is_file()
                and file.suffix.lower() == types
                and file.name[0:2] != "._"
            ):
                # On windows, MAC OSX has hidden temp Wav files that start with ._ They don't have any useable content.
                audio_file_names.append(file)
            else:
                # if foldersinfolders is false you want folder paths to be put here so they can be copied over.
                # that's why is_file is inline in this branch and not in the top one.
                non_audio_file_names.append(file)

    audio_file_names = natsort.natsorted(audio_file_names)

    return (audio_file_names, non_audio_file_names)


def file_tokenization(file_names: list) -> dict:
    """Split file name into individual words and remove digits, punctuation etc"""
    path_and_tokens = {}  # path and tokens value with numbers removed

    for file_path in file_names:
        name = file_path.stem

        tokens = re.findall(r"[a-zA-Z]+|\d+", name)  # words and digits
        # tokens = re.findall(r"[a-zA-Z]+", name)  # just words
        path_and_tokens[file_path] = tokens

    return path_and_tokens


# files to process


def find_files_with_variations(path_and_tokens_by_name: dict) -> list:
    """Find which files have variations and return the file paths in a list of lists"""
    # convert dict into K,V list of lists.
    file_pairs = list(path_and_tokens_by_name.items())

    def word_match(file_pair1: list, file_pair2: list):
        """File path and tokens pair.  See if word tokens in file 1 match those in file 2"""

        # if files aren't in the same folder
        # this stops a bug where you have variations from multiple folder levels being appended together
        if file_pair1[0].parent != file_pair2[0].parent:
            return False

        word1_tokens = file_pair1[1]
        word2_tokens = file_pair2[1]
        if len(word1_tokens) != len(word2_tokens):
            return False

        """
        Vertical sliding window
        word1_token1,[word1_token2], word1_token3
        word2_token1,[word2_token2], word2_token3
        are tokens in [] the same?
        """
        diff_index = 0
        for i in range(len(word1_tokens)):
            if word1_tokens[i] != word2_tokens[i]:
                # if they aren't both digits, return False
                if not (word1_tokens[i].isdigit() and word2_tokens[i].isdigit()):
                    return False

                # if both are the same or within 1 of eachother
                if word1_tokens[i] == word2_tokens[i] or math.isclose(
                    int(word1_tokens[i]), int(word2_tokens[i]), rel_tol=1
                ):
                    # if this is the first difference, set the index where differences are allowed.
                    if diff_index == 0:
                        diff_index = i

                    # if the difference is in the allowed index, continue
                    if diff_index == i:
                        continue

                    # if it's in a non-valid index, reset and return false
                    diff_index = 0
                    return False
        return True

    files_with_variations = []
    matched_files = []
    for y in range(1, len(file_pairs)):

        current_file = file_pairs[y]
        previous_file = file_pairs[y - 1]
        current_file_path = current_file[0]
        previous_file_path = previous_file[0]

        if word_match(current_file, previous_file):
            if previous_file_path not in matched_files:
                matched_files.append(previous_file_path)

            if current_file_path not in matched_files:
                matched_files.append(current_file_path)

        else:
            if len(matched_files) > 0:
                files_with_variations.append(matched_files)
                matched_files = []

    if len(matched_files) > 0:
        files_with_variations.append(matched_files)

    return files_with_variations


def remove_files_with_exclude(files_with_variations: list, exclude_list: list):

    files_with_variations_post_exclude = []

    if len(exclude_list) == 0:
        files_with_variations_post_exclude = files_with_variations
        return files_with_variations_post_exclude

    for item in exclude_list:
        if item == "":
            exclude_list.pop()

    for variation in files_with_variations:
        remove = False

        for phrase in exclude_list:
            if phrase in variation[0].stem:
                remove = True

        if remove == False:
            files_with_variations_post_exclude.append(variation)

    return files_with_variations_post_exclude


# files to copy


def find_files_without_variations(correct_duration_list: list, file_names: list):
    """Find files without variations by taking list of list of correct_duration_list and comparing them with original file list."""

    files_without_vars = []
    files_with_vars = []  # flat list

    # flatten files_with_variations
    for files in correct_duration_list:
        files_with_vars.extend(files)

    for file in file_names:
        if file not in files_with_vars:
            files_without_vars.append(file)

    return files_without_vars


def create_output_path(
    input_file: Path, input_folder: Path, output_folder: Path
) -> Path:
    """create output path by taking filename relative to input and joining it to the output folder path"""
    rel = input_file.relative_to(input_folder)
    file_output = output_folder.joinpath(rel)

    return file_output


def create_parent_folders(file_path: Path):
    """check if a path needs folders created and if so, create them"""
    parent_folders = file_path.parent
    # if the directories don't exist, create them
    Path(parent_folders).mkdir(parents=True, exist_ok=True)


def add_end_tag_to_filename(name_path: Path, tag: str):
    """Add a given tag to the end of the file name"""
    file_name = name_path.stem
    extension = name_path.suffix
    new_name = file_name + tag + extension
    parts = name_path.parent

    return parts.joinpath(new_name)


def create_default_file_path(input_path: Path):
    input_path.name

    suffix = "_sausage"
    new_name = input_path.name + suffix

    return input_path.parent.joinpath(new_name)


def file_append(
    single_variation_list: list,
    silence_duration: int,
    input_folder: Path,
    output_folder: Path,
    append_tag: str,
) -> str:
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
            """ raise exceptions.ChannelCountError(
                "Variations are not of the same channel count"
            ) """

        if block.subtype != subtype:
            raise exceptions.BitDepthError("Variations are not of the same bit depth")

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
                "variations have different channel counts and are not mono or stereo"
            )

    # create the output path
    file_name = single_variation_list[0]
    new_filename = create_output_path(file_name, input_folder, output_folder)
    new_filename = add_end_tag_to_filename(new_filename, tag=append_tag)

    # check if it requires new parent folders
    create_parent_folders(new_filename)

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
    soundfile.write(new_filename, data, highest_sample_rate, subtype=subtype)

    print("Write: ", new_filename)
    return new_filename
