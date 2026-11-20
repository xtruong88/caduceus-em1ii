"""Loaded ranges of the E-M1 Mark II 3.70 main image."""

import struct


BASE = 0x60021020
SECTION_TABLE = 0x60027450
END_GETTER_TABLE = 0x6004354C
SECTION_COUNT = 9


def loaded_sections(image):
    """Read the resident range and the nine section ranges from the loader."""
    def word(addr):
        return struct.unpack_from('<I', image, addr - BASE)[0]

    ranges = [(BASE, word(SECTION_TABLE))]
    for index in range(SECTION_COUNT):
        start = word(SECTION_TABLE + 12 * index)
        stub = word(END_GETTER_TABLE + 4 * index)
        offset = stub - BASE
        if not 0 <= offset < len(image) - 6 or image[offset:offset + 2] != b'\xfc\xcc':
            raise ValueError(f'Unexpected section end getter at {stub:#x}')
        end = word(stub + 2)
        if not ranges[-1][1] <= start <= end <= BASE + len(image):
            raise ValueError(f'Invalid loaded range for section {index + 1}: {start:#x}..{end:#x}')
        if start < end:
            ranges.append((start, end))
    return tuple(ranges)
