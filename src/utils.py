from pathlib import Path
import re
import math
import natsort

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


def file_tokenization(file_names: list[Path]) -> dict:
    """Split file name into individual words and remove digits, punctuation etc"""
    path_and_tokens = {}  # path and tokens value with numbers removed

    for file_path in file_names:
        # when view filtered files go through this, there can be directories.
        if file_path.is_dir():
            continue

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
