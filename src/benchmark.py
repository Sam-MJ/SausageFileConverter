from pathlib import Path
import natsort
import re
import math
import string

from time import perf_counter


def timer(func):
    def f(*args, **kwargs):
        before = perf_counter()
        return_value = func(*args, **kwargs)
        after = perf_counter()
        print(f"{func.__name__}: time elapsed: {after-before}")
        return return_value

    return f


@timer
def get_files(in_folder_path: Path) -> tuple[list, list]:
    """Get files with audio file suffixes from folder directory"""
    audio_file_names = []
    non_audio_file_names = []

    file_paths = in_folder_path.rglob("*")

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

        if file.is_dir():
            continue

        if file.suffix.lower() == types and file.name[0:2] != "._":
            # On windows, MAC OSX has hidden temp Wav files that start with ._ They don't have any useable content.
            audio_file_names.append(file)
        else:
            non_audio_file_names.append(file)

    audio_file_names = natsort.natsorted(audio_file_names)

    return (audio_file_names, non_audio_file_names)


@timer
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


@timer
def find_files_with_variations(path_and_tokens_by_name: dict) -> list[list]:
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


in_folder = Path(r"A:/AUDIO STUFF")
af, nf = get_files(in_folder)
tok = file_tokenization(af)
var = find_files_with_variations(tok)
