from pathlib import Path
import shutil

from src import metadata_v2


def test_validate_data():

    # testfile 1 has soundminer chunk
    test_file1 = Path(r"tests\files\SPRTSkate_Bail Break Board_B00M_MBSB.wav")

    with open(test_file1, "rb") as f:
        file1 = f.read()

    backup_test_file = Path(
        r"tests\files\backup\SPRTSkate_Bail Break Board_B00M_MBSB.wav"
    )

    with open(backup_test_file, "rb") as f:
        file1_b = f.read()

    assert file1 == file1_b

    # file 2 has nonsence all over it and an img imbedded
    test_file2 = Path(r"tests\files\Reaper_Metadata.wav")

    with open(test_file2, "rb") as f:
        file2 = f.read()

    test_file2_bu = Path(r"tests\files\backup\Reaper_Metadata.wav")

    with open(test_file2_bu, "rb") as f:
        file2_b = f.read()

    assert file2 == file2_b


def test_assemble():

    test_file1 = Path(r"tests\files\SPRTSkate_Bail Break Board_B00M_MBSB.wav")

    test_file2 = Path(r"tests\files\Reaper_Metadata.wav")

    md = metadata_v2.Metadata_Assembler(
        original_filename=test_file1, new_filename=test_file2
    )
    md.assemble()

    # check the metadata is the same as file2.
    with open(test_file2, "rb") as f:
        md = metadata_v2.Metadata_Parser(f)

    assert md.header_info == {
        "header_id": b"RIFF",
        "file_size": 184994,
        "format": b"WAVE",
    }

    assert md.fmt_info == {
        "sub_chunk_id": b"fmt ",
        "fmt_chunk_size": 16,
        "audio_format": 1,
        "number_of_channels": 1,
        "sample_rate": 48000,
        "byte_rate": 144000,
        "block_align": 3,
        "bits_per_sample": 24,
    }

    assert md.generic_metadata_info == {
        b"bext": "sub_chunk_size: 604",
        b"ID3 ": "sub_chunk_size: 40960",
        b"SMED": "sub_chunk_size: 110276",
        b"LIST": "sub_chunk_size: 218",
        b"iXML": "sub_chunk_size: 669",
        b"_PMX": "sub_chunk_size: 3658",
    }

    # clean up
    shutil.copy(
        r"tests\files\backup\Reaper_Metadata.wav",
        test_file2,
    )

    # double check input file isn't broken afterwards
    test_validate_data()


if __name__ == "__main__":
    test_assemble()
