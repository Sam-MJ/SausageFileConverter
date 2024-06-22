from pathlib import Path

"""
#THIS CODE IS FOR WHEN YOU WANT TO RUN TESTS IN __NAME__ MAIN WITHOUT PYTEST

import os
import sys

# Get the parent directory
parent_dir = os.path.dirname(os.path.abspath(__file__)).partition("tests")[0]

# Add the parent directory to sys.path
sys.path.append(parent_dir)

# Import the module from the parent directory """

from src import metadata_v2


def test_validate_test_file():
    """Make sure test file doesn't change because OMG"""
    test_file = Path(r"tests/files/SPRTSkate_Bail Break Board_B00M_MBSB.wav")
    with open(test_file, "rb") as f:
        data = f.read()

    backup_test_file = Path(
        r"tests/files/backup/SPRTSkate_Bail Break Board_B00M_MBSB.wav"
    )

    with open(backup_test_file, "rb") as f:
        backup_data = f.read()

    assert data == backup_data


def test_read_header():

    test_file = Path(r"tests/files/SPRTSkate_Bail Break Board_B00M_MBSB.wav")

    with open(test_file, "rb") as f:
        md = metadata_v2.Metadata_Parser(f)

    assert md.header_info == {
        "header_id": b"RIFF",
        "file_size": 5441222,
        "format": b"WAVE",
    }


def test_read_fmt_chunk():

    test_file = Path(r"tests/files/SPRTSkate_Bail Break Board_B00M_MBSB.wav")

    with open(test_file, "rb") as f:
        md = metadata_v2.Metadata_Parser(f)

    assert md.fmt_info == {
        "sub_chunk_id": b"fmt ",
        "fmt_chunk_size": 16,
        "audio_format": 1,
        "number_of_channels": 2,
        "sample_rate": 96000,
        "byte_rate": 576000,
        "block_align": 6,
        "bits_per_sample": 24,
    }


def test_read_generic_metadata():

    test_file = Path(r"tests/files/SPRTSkate_Bail Break Board_B00M_MBSB.wav")

    with open(test_file, "rb") as f:
        md = metadata_v2.Metadata_Parser(f)

    assert md.generic_metadata_info == {
        b"bext": "sub_chunk_size: 604",
        b"ID3 ": "sub_chunk_size: 40960",
        b"SMED": "sub_chunk_size: 110276",
        b"LIST": "sub_chunk_size: 218",
        b"iXML": "sub_chunk_size: 669",
        b"_PMX": "sub_chunk_size: 3658",
    }


if __name__ == "__main__":
    test_read_generic_metadata()
