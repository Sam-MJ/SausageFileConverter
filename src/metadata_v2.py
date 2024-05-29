import struct
from io import BytesIO

import exceptions


class Metadata_Parser:

    def __init__(self, from_file) -> None:
        """from file is a buffered file read with bytes"""
        self.file_bytes = BytesIO(from_file.read())
        # defaults
        self.generic_metadata = b""
        self.generic_metadata_info = {}
        self.header = None
        self.header_info = None
        self.fmt = None
        self.fmt_info = None
        self.data = None
        self.data_info = None
        self.read()

    def _read_header(self):

        if not len(self.file_bytes.read()) > 0:
            raise exceptions.EmptyFileExeption("File does not contain any bytes!")
        self.file_bytes.seek(0)

        header_id = self.file_bytes.read(4)
        if header_id != b"RIFF":
            raise exceptions.InvalidRIFFFileException("Not a RIFF File")

        file_size = struct.unpack("<I", self.file_bytes.read(4))[0]
        if not isinstance(file_size, int):
            raise exceptions.InvalidSizeValue("Not a valid SIZE Value")

        file_format = self.file_bytes.read(4)
        if file_format != b"WAVE":
            raise exceptions.InvalidWavFileException("Not a WAVE file")

        self.header_info = {
            "header_id": header_id,
            "file_size": file_size,
            "format": file_format,
        }

        packed_file_size = struct.pack("<I", file_size)

        self.header = b"".join([header_id, packed_file_size, file_format])

    def _read_fmt(self, sub_chunk_id):

        sub_chunk_size = struct.unpack("<I", self.file_bytes.read(4))[0]
        if not isinstance(sub_chunk_size, int):
            raise exceptions.FormatChunkError("sub_chunk_size is not an int")

        audio_format = struct.unpack("<H", self.file_bytes.read(2))[0]
        if not isinstance(audio_format, int):
            raise exceptions.FormatChunkError("audio_format is not an int")

        num_channels = struct.unpack("<H", self.file_bytes.read(2))[0]
        if not isinstance(num_channels, int):
            raise exceptions.FormatChunkError("num_channels is not an int")

        sample_rate = struct.unpack("<I", self.file_bytes.read(4))[0]
        if not isinstance(sample_rate, int):
            raise exceptions.FormatChunkError("sample_rate is not an int")

        byte_rate = struct.unpack("<I", self.file_bytes.read(4))[0]
        if not isinstance(byte_rate, int):
            raise exceptions.FormatChunkError("byte_rate is not an int")

        block_align = struct.unpack("<H", self.file_bytes.read(2))[0]
        if not isinstance(block_align, int):
            raise exceptions.FormatChunkError("block_align is not an int")

        bits_per_sample = struct.unpack("<H", self.file_bytes.read(2))[0]
        if not isinstance(bits_per_sample, int):
            raise exceptions.FormatChunkError("bits_per_sample is not an int")

        # fmt has 16bytes of info but chunk size can be 24 or 40 bytes, so read to the end of it and continue.
        self.file_bytes.read(sub_chunk_size - 16)

        self.fmt_info = {
            "sub_chunk_id": sub_chunk_id,
            "fmt_chunk_size": sub_chunk_size,
            "audio_format": audio_format,
            "number_of_channels": num_channels,
            "sample_rate": sample_rate,
            "byte_rate": byte_rate,
            "block_align": block_align,
            "bits_per_sample": bits_per_sample,
        }

        packed_sub_chunk_size = struct.pack("<I", sub_chunk_size)

        packed_audio_format = struct.pack("<H", audio_format)

        packed_num_channels = struct.pack("<H", num_channels)

        packed_sample_rate = struct.pack("<I", sample_rate)

        packed_byte_rate = struct.pack("<I", byte_rate)

        packed_block_align = struct.pack("<H", block_align)

        packed_bits_per_sample = struct.pack("<H", bits_per_sample)

        self.fmt = b"".join(
            [
                sub_chunk_id,
                packed_sub_chunk_size,
                packed_audio_format,
                packed_num_channels,
                packed_sample_rate,
                packed_byte_rate,
                packed_block_align,
                packed_bits_per_sample,
            ]
        )

    def _read_data(self, sub_chunk_id):

        sub_chunk_size = struct.unpack("<I", self.file_bytes.read(4))[0]
        if not isinstance(sub_chunk_size, int):
            raise exceptions.InvalidSizeValue("Data sub_chunk_size is not an int")

        # read all content of sub chunk
        content = self.file_bytes.read(sub_chunk_size)

        # word align by adding a byte if chunk size isn't an even number. - chunks MUST be an even size
        if sub_chunk_size % 2 != 0:
            self.file_bytes.read(1)
            content += b"\x00"
            # print("WORD ALIGN GO! - Data Chunk")

        self.data_info = {
            "sub_chunk_id": sub_chunk_id,
            "sub_chunk_size": sub_chunk_size,
        }

        # pack and append
        packed_sub_chunk_size = struct.pack("<I", sub_chunk_size)
        self.data = b"".join([sub_chunk_id, packed_sub_chunk_size, content])

    def _read_generic_chunk(self, sub_chunk_id):
        """Reads chunk and appends to generic_metadata bytestring"""

        sub_chunk_size = struct.unpack("<I", self.file_bytes.read(4))[0]
        if not isinstance(sub_chunk_size, int):
            raise exceptions.InvalidSizeValue("sub_chunk_size is not an int")

        # read all content of sub chunk
        content = self.file_bytes.read(sub_chunk_size)

        self.generic_metadata_info[sub_chunk_id] = f"sub_chunk_size: {sub_chunk_size}"

        packed_sub_chunk_size = struct.pack("<I", sub_chunk_size)

        # word align by adding a byte if chunk size isn't an even number. - chunks MUST be an even size (this may only be data chunk?)
        if sub_chunk_size % 2 != 0:
            self.file_bytes.read(1)
            content += b"\x00"
            # print("WORD ALIGN GO! - Metadata chunk")

        self.generic_metadata += b"".join(
            [sub_chunk_id, packed_sub_chunk_size, content]
        )

    def _skip_DGDA(self, sub_chunk_id):
        """DGDA is a weird avid chunk that's different for each file"""
        sub_chunk_size = struct.unpack("<I", self.file_bytes.read(4))[0]
        if not isinstance(sub_chunk_size, int):
            raise exceptions.InvalidSizeValue("sub_chunk_size is not an int")

        self.file_bytes.read(sub_chunk_size)

        # word align by adding a byte if chunk size isn't an even number. - chunks MUST be an even size (this may only be data chunk?)
        if sub_chunk_size % 2 != 0:
            self.file_bytes.read(1)
            # content += b"\x00"
            # print("WORD ALIGN GO! - Metadata chunk")

    def read(self):
        """Start by reading the header and then read the subchunk id and continue reading with the relevant parser"""

        self._read_header()

        # read first chunk
        sub_chunk_id = self.file_bytes.read(4)

        while sub_chunk_id != b"":
            if sub_chunk_id == b"fmt ":
                self._read_fmt(sub_chunk_id)
            elif sub_chunk_id == b"data":
                self._read_data(sub_chunk_id)
            elif sub_chunk_id == b"DGDA":
                self._skip_DGDA(sub_chunk_id)
            else:
                self._read_generic_chunk(sub_chunk_id)

            sub_chunk_id = self.file_bytes.read(4)
            decoded = sub_chunk_id.decode("utf-8", "ignore")
            # check sub_chunk_id is made up of bytes representing alphanumerics or spaces
            # some files are very stupid and don't provide accurate data.
            # i.e fmt size 40 but actually is 16, so you end up skipping into a data chunk
            while len(decoded) != 4 or not all(
                x.isalnum() or x.isspace() or x == "_" for x in decoded
            ):
                if sub_chunk_id == b"":
                    break
                raise exceptions.SubchunkIDParsingError


class Metadata_Assembler:
    """Metadata Assembler class is designed to:
    read the metadata from the original given file
    read the header, data and fmt from the newly created file
    and then combine them together in the same location as the new file, re-writing it with the combined content.
    the combined content also required changing the header's size information to the new combined file size.
    """

    def __init__(self, original_filename, new_filename) -> None:
        self.new_filename = new_filename
        self.original_filename = original_filename

    def _read_original(self):
        """read misc metadata from original file"""
        # print(self.original_filename)
        with open(self.original_filename, "rb") as in_file:
            file1 = Metadata_Parser(in_file)
            # print(file1.generic_metadata_info)

        return file1.generic_metadata

    def _read_new_filename(self):
        with open(self.new_filename, "rb") as in_file:
            file2 = Metadata_Parser(in_file)
            # print(file2.header_info)
            # print(file2.fmt_info)
            # print(file2.data_info)

        header_format_data = b"".join([file2.header, file2.fmt, file2.data])

        return header_format_data

    def _update_header_file_size(self, blob: bytes):
        """New data blob will still have the file size from the old half, so write the new value into the header and return it!"""
        b = BytesIO(blob)

        file_size = len(blob) - 8
        # pack into struct
        packed_file_size = struct.pack("<I", file_size)

        # find size position
        b.seek(4)
        b.write(packed_file_size)
        # go back to the start
        b.seek(0)
        new_bytes = b.read()

        return new_bytes

    def assemble(self):
        header_fmt_data = self._read_new_filename()
        other_chunks = self._read_original()

        blob = b"".join([header_fmt_data, other_chunks])

        updated_blob = self._update_header_file_size(blob)

        with open(self.new_filename, "wb") as out_file:
            out_file.write(updated_blob)
