from pathlib import Path

from src import utils
from src import worker
from pprint import pprint


def create_temp(tmp_path):

    file_names = (
        "abc_01.wav",
        "abc_02.wav",
        "abc_5.wav",
        "abc_11.wav",
        "abc_3.wav",
        "mydir/01monty.wav",
        "mydir/02monty.wav",
        "mydir/monty_1m_01.wav",
        "mydir/monty_1m_02.wav",
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
    audio_files, non_audio_files = utils.get_files(tmp_path)
    assert audio_files == [
        Path(f"{tmp_path}/abc_01.wav"),
        Path(f"{tmp_path}/abc_02.wav"),
        Path(f"{tmp_path}/abc_3.wav"),
        Path(f"{tmp_path}/abc_5.wav"),
        Path(f"{tmp_path}/abc_11.wav"),
        Path(f"{tmp_path}/mydir/01monty.wav"),
        Path(f"{tmp_path}/mydir/02monty.wav"),
        Path(f"{tmp_path}/mydir/monty_1m_01.wav"),
        Path(f"{tmp_path}/mydir/monty_1m_02.wav"),
    ]


def test_file_tokenization(tmp_path):
    create_temp(tmp_path)
    audio_files, non_audio_files = utils.get_files(tmp_path)
    tokens = utils.split_paths_to_tokens(audio_files)
    assert tokens == {
        Path(f"{tmp_path}/abc_01.wav"): [
            "abc",
            "01",
        ],
        Path(f"{tmp_path}/abc_02.wav"): [
            "abc",
            "02",
        ],
        Path(f"{tmp_path}/abc_3.wav"): ["abc", "3"],
        Path(f"{tmp_path}/abc_5.wav"): ["abc", "5"],
        Path(f"{tmp_path}/abc_11.wav"): ["abc", "11"],
        # new regex breaks this, but it's less likely to have a variation like that than a distance.
        Path(f"{tmp_path}/mydir/01monty.wav"): ["01", "monty"],
        Path(f"{tmp_path}/mydir/02monty.wav"): ["02", "monty"],
        Path(f"{tmp_path}/mydir/monty_1m_01.wav"): ["monty", "1m", "01"],
        Path(f"{tmp_path}/mydir/monty_1m_02.wav"): ["monty", "1m", "02"],
    }

    # distance tokens
    data3 = {
        Path("A:/made_up/gunshot 5m 1"): ["gunshot", "5m", "1"],
        Path("A:/made_up/gunshot 5m 2"): ["gunshot", "5m", "2"],
        Path("A:/made_up/gunshot 10m 1"): ["gunshot", "10m", "1"],
        Path("A:/made_up/gunshot 10m 2"): ["gunshot", "10m", "2"],
    }
    tokens = utils.split_paths_to_tokens(data3)
    assert tokens == {
        Path("A:/made_up/gunshot 5m 1"): ["gunshot", "5m", "1"],
        Path("A:/made_up/gunshot 5m 2"): ["gunshot", "5m", "2"],
        Path("A:/made_up/gunshot 10m 1"): ["gunshot", "10m", "1"],
        Path("A:/made_up/gunshot 10m 2"): ["gunshot", "10m", "2"],
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
                "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/abc_01.wav"
            ),
            Path(
                "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/abc_02.wav"
            ),
        ],
        [
            Path(
                "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/anotherfolder/digital activation sequence beep_01.wav"
            ),
            Path(
                "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/anotherfolder/digital activation sequence beep_02.wav"
            ),
        ],
        [
            Path(
                "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/anotherfolder/yet_another_folder/01this_is a test.wav"
            ),
            Path(
                "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/anotherfolder/yet_another_folder/02this_is a test.wav"
            ),
        ],
        [
            Path(
                "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/andrewscott_01_01.wav"
            ),
            Path(
                "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/andrewscott_01_02.wav"
            ),
        ],
        [
            Path(
                "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/andrewscott_02_01.wav"
            ),
            Path(
                "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/andrewscott_02_02.wav"
            ),
            Path(
                "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/andrewscott_02_03.wav"
            ),
        ],
    ]

    output = utils.find_files_with_variations(data)

    assert expected_output == output

    data = {
        Path("D:/andrewscott_01_1.wav"): ["andrewscott", "01", "1"],
        Path("D:/andrewscott_01_2.wav"): ["andrewscott", "01", "2"],
        Path("D:/andrewscott_01_3.wav"): ["andrewscott", "01", "3"],
        Path("D:/andrewscott_02_1.wav"): ["andrewscott", "02", "1"],
        Path("D:/andrewscott_02_2.wav"): ["andrewscott", "02", "2"],
        Path("D:/andrewscott_06_1.wav"): ["andrewscott", "06", "1"],
        Path("D:/andrewscott_06_4.wav"): ["andrewscott", "06", "4"],
    }

    output = utils.find_files_with_variations(data)

    expected_output = [
        [
            Path("D:/andrewscott_01_1.wav"),
            Path("D:/andrewscott_01_2.wav"),
            Path("D:/andrewscott_01_3.wav"),
        ],
        [Path("D:/andrewscott_02_1.wav"), Path("D:/andrewscott_02_2.wav")],
        [Path("D:/andrewscott_06_1.wav"), Path("D:/andrewscott_06_4.wav")],
    ]

    assert output == expected_output

    print(output)
    ## test two to remove files that are a digit and a distance i.e. M or ft ##

    data2 = {
        Path("A:/made_up/waterfall 5m"): ["waterfall", "5m"],
        Path("A:/made_up/waterfall 15m"): ["waterfall", "15m"],
        Path("A:/made_up/waterfall 25m"): ["waterfall", "25m"],
    }
    output2 = utils.find_files_with_variations(data2)
    assert output2 == []

    data3 = {
        Path("A:/made_up/waterfall 5m 1"): ["waterfall", "5m", "1"],
        Path("A:/made_up/waterfall 5m 3"): ["waterfall", "5m", "3"],
        Path("A:/made_up/waterfall 5m 4"): ["waterfall", "5m", "4"],
    }
    output3 = utils.find_files_with_variations(data3)
    expected_output = [
        [
            Path("A:/made_up/waterfall 5m 1"),
            Path("A:/made_up/waterfall 5m 3"),
            Path("A:/made_up/waterfall 5m 4"),
        ]
    ]
    assert output3 == expected_output

    data3 = {
        Path("A:/made_up/waterfall 5m 1"): ["waterfall", "5m", "1", "02"],
        Path("A:/made_up/waterfall 15m 3"): ["waterfall", "150m", "3", "04"],
        Path("A:/made_up/waterfall 25m 4"): ["waterfall", "25000m", "4", "05"],
    }
    output3 = utils.find_files_with_variations(data3)
    assert output3 == []

    data3 = {
        Path("A:/made_up/gunshot 5m 1"): ["gunshot", "5m", "1"],
        Path("A:/made_up/gunshot 5m 2"): ["gunshot", "5m", "2"],
        Path("A:/made_up/gunshot 10m 1"): ["gunshot", "10m", "1"],
        Path("A:/made_up/gunshot 10m 2"): ["gunshot", "10m", "2"],
    }
    output3 = utils.find_files_with_variations(data3)
    expected_output = [
        [Path("A:/made_up/gunshot 5m 1"), Path("A:/made_up/gunshot 5m 2")],
        [
            Path("A:/made_up/gunshot 10m 1"),
            Path("A:/made_up/gunshot 10m 2"),
        ],
    ]
    assert output3 == expected_output


def test_add_file_tag():
    file = Path(
        "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/andrewscott_02_02.wav"
    )
    tag = "_sausage"

    out = utils.add_end_tag_to_filename(file, tag=tag)

    assert out == Path(
        "D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN/andrewscott_02_02_sausage.wav"
    )


def test_create_default_path():
    """append _sausage to the end of the input folder"""
    path = Path(
        r"D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN"
    )
    out = utils.create_default_file_path(path)

    assert out == Path(
        r"D:/Documents/Programming_stuff/Python_projects/Sausage file converter/IN_sausage"
    )


def test_remove_too_long_files():
    w = worker.Worker(ctrl={"break": False})

    files_with_variations = [
        [
            Path(r"tests\files\diffchannels\channels_test_file_01.wav"),
            Path(r"tests\files\diffchannels\channels_test_file_02.wav"),
            Path(r"tests\files\diffchannels\channels_test_file_03.wav"),
            Path(r"tests\files\diffchannels\channels_test_file_04.wav"),
            Path(r"tests\files\diffchannels\channels_test_file_05.wav"),
        ]
    ]

    # all files are longer than 0.1 seconds
    max_duration = 0.1
    out = worker.Worker.remove_too_long_files(w, files_with_variations, max_duration)
    assert not out

    # but they are shorter than 1 seconds
    max_duration = 1
    out = worker.Worker.remove_too_long_files(w, files_with_variations, max_duration)
    assert out == [
        [
            Path("tests/files/diffchannels/channels_test_file_01.wav"),
            Path("tests/files/diffchannels/channels_test_file_02.wav"),
            Path("tests/files/diffchannels/channels_test_file_03.wav"),
            Path("tests/files/diffchannels/channels_test_file_04.wav"),
            Path("tests/files/diffchannels/channels_test_file_05.wav"),
        ]
    ]


if __name__ == "__main__":
    pass
