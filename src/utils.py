from pathlib import Path
import re
import soundfile
import numpy
import math

import exceptions


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

            if current_file_path not in matched_files:
                matched_files.append(current_file_path)

            if previous_file_path not in matched_files:
                matched_files.append(previous_file_path)
        else:
            if len(matched_files) > 0:
                files_with_variations.append(matched_files)
                matched_files = []

    if len(matched_files) > 0:
        files_with_variations.append(matched_files)

    return files_with_variations


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


def file_append(
    single_variation_list: list,
    silence_duration: int,
    input_folder: Path,
    output_folder: Path,
) -> str:
    """
    Take a list of one set of files with variations i.e impact_01.wav, impact_02.wav, impact_03.wav and append them together.
    return the new file name and export the new file to its output folder.
    """

    # append file to combined
    list_of_sound_objects = []
    samplerates = []
    subtypes = []
    for file in single_variation_list:
        s = soundfile.SoundFile(file, "r")
        samplerates.append(s.samplerate)
        subtypes.append(s.subtype)

        sound_data = s.read()
        s.close()

        list_of_sound_objects.append(sound_data)

    # check sample rate and bit depth are all the same over all variations
    if not samplerates.count(samplerates[0]) == len(samplerates):
        raise exceptions.SampleRateError("Variations are not of the same sample rate")

    if not subtypes.count(subtypes[0]) == len(subtypes):
        raise exceptions.BitDepthError("Variations are not of the same bit depth")

    samplerate = samplerates[0]
    subtype = subtypes[0]

    first_file = list_of_sound_objects[0]
    channels = first_file.shape[1:]
    dtype = first_file.dtype

    # create silence block
    silence_samples_number = samplerate * silence_duration
    shape = (int(silence_samples_number),) + channels
    silence_block = numpy.zeros((shape), dtype)

    # insert into list of files, alternating indexes, i.e 1,3,5,7
    for i in range(1, len(list_of_sound_objects) * 2 - 1, 2):
        list_of_sound_objects.insert(i, silence_block)

    # create the output path
    file_name = single_variation_list[0]
    new_filename = create_output_path(file_name, input_folder, output_folder)

    # check if it requires new parent folders
    create_parent_folders(new_filename)

    # write file
    data = numpy.concatenate(list_of_sound_objects)
    soundfile.write(new_filename, data, samplerate, subtype=subtype)

    print("Write: ", new_filename)
    return new_filename


# helper function to perform sort
def num_sort(test_string: Path):
    return list(map(int, re.findall(r"\d+", test_string.name)))[0]
