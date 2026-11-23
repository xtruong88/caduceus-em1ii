#!/usr/bin/env python3
"""E-M1 Mark II: where the camera puts the full-size record 0x1000 that the halation pass reads (stock code, emulated).

    python3 tools/omdem1mk2_emu_image_heap.py

Static path (stock 3.70 catalog image): the development allocates record 0x1000 through 0x6038bc07 -> 0x6038bb47
(record +76 = 0x1000, +81 = 0), which calls the job callback 0x60380399 with op 19. The capture code's callback
0x6041f8ae (table 0x605569d8) sends op 19 to 0x6041fcf6; for kind 0x1000 the special-kind test 0x604263a0 returns 0,
+81 is 0, +76 has neither 0x01000000 nor 0x10000, so 0x6041febc allocates in mode 0: 0x604254fe -> 0x60411126 ->
0x604111b7, which takes heap 0 (control 0xa26d4f8c) when the heap mode 0xa26d4f84 is 1, else heap 1 (0xa26d4fe0),
through the table 0x60553370. The init function 0x6041157a (in the init table 0x6058017c) creates both heaps with
fixed constants (0x6040ebe0: base, size).

This harness runs the camera's own heap init and allocator:
  1. after 0x6041157a, a 40 MB allocation (5184 x 3888 x 2, the record's size) returns 0x8dc64e00 in heap mode 1 and
     0x9b758800 otherwise, the heaps' first addresses;
  2. both heaps (0x8dc64e00 + 0x11982600 and 0x9b758800 + 0x3e8ec00, both ending at 0x9f5e7400) lie inside
     0x84000000..0x9fffffff, the range hl_pass maps through this CPU's window (tools/omdem1mk2_emu_mapper.py); none is
     below 0x84000000, where hl_pass would leave the photo alone.
tools/omdem1mk2_emu_halation_pass.py runs the pass bit-exact at these addresses and across the 0x90000000 and
0x98000000 window edges inside them.
Fixture boundary: only the first allocation of a fresh heap is run (the fixture keeps the cached heap region per call);
later allocations come from the same heap, so they stay inside the ranges in 2.
"""
import struct

import omdem1mk2_emu_spare_setting as S
import omdem1mk2_emu_validator as V
from penf_emulator import Region

INIT, ALLOC, NAME = 0x6041157A, 0x60411126, 0x605569C0
MODE = 0xA26D4F84
SIZE = 5184 * 3888 * 2
HEAPS = {1: (0x8DC64E00, 0x11982600), 2: (0x9B758800, 0x03E8EC00)}
WINDOWED = (0x84000000, 0xA0000000)
HEAP_UNC = (Region('heap_unc', 0xA1A00000, bytes(0x57D000), 'rw', alias_of='heap'),)


def creation(img, at):
    """(base, size) from `mov imm32,d0; mov imm32,d1; mov imm16,a1` right before the 0x6040ebe0 call at `at`."""
    o = at - V.B
    assert img[o - 15:o - 13] == b'\xfc\xcc' and img[o - 9:o - 7] == b'\xfc\xcd' and img[o - 3] == 0x25, \
        img[o - 15:o].hex()
    return struct.unpack_from('<I', img, o - 13)[0], struct.unpack_from('<I', img, o - 7)[0]


def main():
    img = V.image(None)
    assert creation(img, 0x60411597) == HEAPS[1] and creation(img, 0x604115B6) == HEAPS[2]
    for mode, (base, size) in HEAPS.items():
        e = S.Emu(None)
        e.call(INIT, None, 0, {})
        e.write(MODE, struct.pack('<H', mode))
        got = e.call(ALLOC, 0x00, 4, {'d0': SIZE, 'd1': 0, 'a0': NAME, 'a1': 0}, HEAP_UNC)['d0']
        assert got == base, (mode, hex(got))
        assert WINDOWED[0] <= base and base + size <= WINDOWED[1], (hex(base), hex(size))
        print(f'heap mode {mode}: record 0x1000 ({SIZE} B) at {got:#010x}; heap {base:#010x}..{base + size:#010x} '
              f'is inside the windowed range {WINDOWED[0]:#x}..{WINDOWED[1]:#x}')
    print('RESULT PASS')


if __name__ == '__main__':
    main()
