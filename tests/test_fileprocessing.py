from src import utils
from pathlib import Path
import soundfile as sf
import numpy as np


def test_file_append_different_sample_rates():
    single_variation_list = [
        Path("tests/files/test_file_48.wav"),
        Path("tests/files/test_file_96.wav"),
        Path("tests/files/test_file_192.wav"),
    ]
    silence_duration = 0.5
    input_folder = Path(r"tests/files")
    output_folder = Path(r"tests/files/outputs")
    append_tag = ""

    utils.file_append(
        single_variation_list, silence_duration, input_folder, output_folder, append_tag
    )

    # check output
    output_file = Path(r"tests\files\outputs\test_file_48.wav")

    with sf.SoundFile(output_file, "r") as of:
        samplerate = of.samplerate
        audio = of.read()
        assert samplerate == 192000

    # delete output file when we're done
    output_file.unlink()


def test_file_append_mono_and_stereo_variations():
    # mono and stereo in the same set of variations, mono should be converted to stereo format and then concatenated
    single_variation_list = [
        Path("tests/files/channels_test_file_01.wav"),
        Path("tests/files/channels_test_file_02.wav"),
    ]
    silence_duration = 0.5
    input_folder = Path(r"tests/files")
    output_folder = Path(r"tests/files/outputs")
    append_tag = ""

    utils.file_append(
        single_variation_list, silence_duration, input_folder, output_folder, append_tag
    )

    # check output
    output_file = Path(r"tests/files/outputs/channels_test_file_01.wav")

    with sf.SoundFile(output_file, "r") as of:
        audio = of.read()
        channels = audio.shape[1:][0]
        assert channels == 2
        # check that channels are not equal (i.e have stereo content)
        left, right = np.hsplit(audio, 2)
        assert not np.array_equal(left, right)

    # delete output file when we're done
    output_file.unlink()
