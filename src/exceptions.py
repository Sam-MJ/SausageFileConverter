# appender
class BitDepthError(Exception):
    pass


class ChannelCountError(Exception):
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
