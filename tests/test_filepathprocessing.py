from pathlib import Path

from src import utils

from pprint import pprint


def create_temp(tmp_path):

    file_names = (
        "abc_01.wav",
        "abc_02.wav",
        "mydir/01monty.wav",
        "mydir/02monty.wav",
        "podcastwith10views.flac",
    )

    for file in file_names:
        # create a file path with temp directory
        file_path = tmp_path / file
        # create parent directory
        file_path.parent.mkdir(parents=True, exist_ok=True)
        # create file from file path
        file_path.touch()

    emptydir = tmp_path / "mydir/empty"
    emptydir.mkdir(parents=True)


def test_get_files_folders_in_folders_true(tmp_path):
    create_temp(tmp_path)
    foldersinfolders = True
    audio_files, non_audio_files = utils.get_files(tmp_path, foldersinfolders)
    assert audio_files == [
        Path(f"{tmp_path}/abc_01.wav"),
        Path(f"{tmp_path}/abc_02.wav"),
        Path(f"{tmp_path}/mydir/01monty.wav"),
        Path(f"{tmp_path}/mydir/02monty.wav"),
    ]

    assert Path(f"{tmp_path}/mydir/") not in non_audio_files


def test_get_files_folders_in_folders_false(tmp_path):
    create_temp(tmp_path)
    foldersinfolders = False
    audio_files, non_audio_files = utils.get_files(tmp_path, foldersinfolders)
    assert audio_files == [
        Path(f"{tmp_path}/abc_01.wav"),
        Path(f"{tmp_path}/abc_02.wav"),
    ]

    assert [
        Path(f"{tmp_path}/mydir/01monty.wav"),
        Path(f"{tmp_path}/mydir/02monty.wav"),
    ] not in audio_files

    assert Path(f"{tmp_path}/mydir/") in non_audio_files


def test_file_tokenization(tmp_path):
    create_temp(tmp_path)
    foldersinfolders = True
    audio_files, non_audio_files = utils.get_files(tmp_path, foldersinfolders)
    tokens = utils.file_tokenization(audio_files)
    assert tokens == {
        Path(f"{tmp_path}/abc_01.wav"): [
            "abc",
            "01",
        ],
        Path(f"{tmp_path}/abc_02.wav"): [
            "abc",
            "02",
        ],
        Path(f"{tmp_path}/mydir/01monty.wav"): ["01", "monty"],
        Path(f"{tmp_path}/mydir/02monty.wav"): ["02", "monty"],
    }


def test_files_with_variations():
    data = {
        Path(
            "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/abc - Copy.wav"
        ): ["abc", "Copy"],
        Path(
            "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/abc_01.wav"
        ): ["abc", "01"],
        Path(
            "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/abc_02.wav"
        ): ["abc", "02"],
        Path(
            "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/anotherfolder/abc - Copy.wav"
        ): ["abc", "Copy"],
        Path(
            "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/anotherfolder/digital activation sequence beep_01 - Copy.wav"
        ): ["digital", "activation", "sequence", "beep", "Copy", "01"],
        Path(
            "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/anotherfolder/digital activation sequence beep_01.wav"
        ): ["digital", "activation", "sequence", "beep", "01"],
        Path(
            "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/anotherfolder/digital activation sequence beep_02.wav"
        ): ["digital", "activation", "sequence", "beep", "02"],
        Path(
            "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/anotherfolder/yet_another_folder/01this_is a test.wav"
        ): ["01", "this", "is", "a", "test"],
        Path(
            "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/anotherfolder/yet_another_folder/02this_is a test.wav"
        ): ["02", "this", "is", "a", "test"],
        Path(
            "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/anotherfolder/yet_another_folder/abc - Copy.wav"
        ): ["abc", "Copy"],
        Path(
            "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/anotherfolder/yet_another_folder/digital activation sequence beep_01.wav"
        ): ["digital", "activation", "sequence", "beep", "01"],
        Path(
            "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/andrewscott_01_01.wav"
        ): ["andrewscott", "01", "01"],
        Path(
            "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/andrewscott_01_02.wav"
        ): ["andrewscott", "01", "02"],
        Path(
            "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/andrewscott_02_01.wav"
        ): ["andrewscott", "02", "01"],
        Path(
            "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/andrewscott_02_02.wav"
        ): ["andrewscott", "02", "02"],
        Path(
            "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/andrewscott_02_03.wav"
        ): ["andrewscott", "02", "03"],
    }

    expected_output = [
        [
            Path(
                "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/abc_02.wav"
            ),
            Path(
                "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/abc_01.wav"
            ),
        ],
        [
            Path(
                "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/anotherfolder/digital activation sequence beep_02.wav"
            ),
            Path(
                "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/anotherfolder/digital activation sequence beep_01.wav"
            ),
        ],
        [
            Path(
                "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/anotherfolder/yet_another_folder/02this_is a test.wav"
            ),
            Path(
                "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/anotherfolder/yet_another_folder/01this_is a test.wav"
            ),
        ],
        [
            Path(
                "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/andrewscott_01_02.wav"
            ),
            Path(
                "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/andrewscott_01_01.wav"
            ),
        ],
        [
            Path(
                "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/andrewscott_02_02.wav"
            ),
            Path(
                "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/andrewscott_02_01.wav"
            ),
            Path(
                "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/andrewscott_02_03.wav"
            ),
        ],
    ]

    output = utils.find_files_with_variations(data)
    pprint(output)

    assert expected_output == output


if __name__ == "__main__":
    test_files_with_variations()
