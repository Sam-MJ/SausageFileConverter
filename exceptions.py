# appender
class SampleRateError(Exception):
    pass


class BitDepthError(Exception):
    pass


# metadata reader
class InvalidRIFFFileException(Exception):
    pass


class InvalidWavFileException(Exception):
    pass


class InvalidSizeValue(Exception):
    pass


class EmptyFileExeption(Exception):
    pass


class FormatChunkError(Exception):
    pass


class SubchunkIDParsingError(Exception):
    pass
