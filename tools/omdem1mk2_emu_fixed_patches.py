#!/usr/bin/env python3
"""Exercise the recording-limit dispatch and focus-stacking branch on both images."""

import struct
import sys

import omdem1mk2_emu_validator as V
from penf_emulator import Region, execute


OUTPUT = 0x9F100000


def record_limit(img, mode):
    output = Region('limit', OUTPUT, bytes(4), 'rw', True)
    result = execute(
        (*V.main_regions(img), output), {'pc': 0x603549CC, 'd0': mode, 'a0': OUTPUT},
        0xFFFFFFF0, limit=20, breakpoints=[0x60354A0E],
    )
    assert result['status'] == 'breakpoint' and not result['fault'], result['fault']
    return struct.unpack('<I', bytes.fromhex(result['memory'][0]['hex']))[0]


def stacking_branch(img, z):
    result = execute(V.main_regions(img), {'pc': 0x60656A4A, 'psw': z}, 0xFFFFFFF0,
                     limit=5, breakpoints=[0x60656A4C, 0x60656A4E])
    assert result['status'] == 'breakpoint' and not result['fault'], result['fault']
    return result['registers']['pc']


def main():
    old, new = V.image(None), V.image(sys.argv[1])
    for mode, initial in ((9, 1740), (4, 7200)):
        before, after = record_limit(old, mode), record_limit(new, mode)
        assert (before, after) == (initial, 32400), (mode, before, after)
        print(f'Record mode {mode}: {before} -> {after} seconds')
    for z, initial in ((0, 0x60656A4E), (1, 0x60656A4C)):
        before, after = stacking_branch(old, z), stacking_branch(new, z)
        assert (before, after) == (initial, 0x60656A4C), (z, before, after)
        print(f'Focus stacking branch, Z={z}: {before:#x} -> {after:#x}')
    print('RESULT PASS')


if __name__ == '__main__':
    main()
