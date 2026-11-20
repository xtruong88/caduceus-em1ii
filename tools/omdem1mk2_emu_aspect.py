#!/usr/bin/env python3
"""Run the loader up to flash transfer, plus aspect switches and labels."""

import struct
import sys

import omdem1mk2_emu_validator as V
from omdem1mk2_emu_scp import resolve
from penf_emulator import Region, execute


STACK = 0x9F000000
SP = STACK + 0x1000
MENU = 0x6124EA1C
SWITCHES = (
    ('S7', 0x60B2F8EC, 0x608BB796, 40, 'd0'),
    ('S8', 0x60B2F918, 0x608BB9A6, 40, 'd0'),
    ('S9', 0x60B2F944, 0x608BBD2E, 36, 'd0'),
    ('S10', 0x60B4CEDC, 0x60911F49, 'a0', 'd3'),
    ('S_alt', 0x60B3BD68, 0x608D411E, 'd0', 'd1'),
)


def run_case(img, entry, resume, width, height):
    stack = Region('stack', STACK, bytes(0x2000), 'rw', True)
    result = execute((*V.main_regions(img), stack), {'pc': entry, 'sp': SP},
                     0xFFFFFFF0, limit=100, breakpoints=[resume])
    regs = result['registers']
    if result['fault'] or regs['pc'] != resume:
        raise ValueError(f"{entry:#x} stopped at {regs['pc']:#x}: {result['fault']}")
    assert regs['sp'] == SP
    if isinstance(width, int):
        data = bytes.fromhex(result['memory'][0]['hex'])
        width_value, = struct.unpack_from('<I', data, SP - STACK + width)
    else:
        width_value = regs[width]
    return width_value, regs[height]


def transfer_args(img):
    stack = Region('stack', STACK, bytes(0x2000), 'rw')
    result = execute((*V.main_regions(img), stack), {'pc': 0x60042B96, 'sp': SP, 'd0': 1},
                     0xFFFFFFF0, limit=1000, breakpoints=[0x60042BCE])
    assert result['status'] == 'breakpoint' and not result['fault'], result['fault']
    return tuple(result['registers'][name] for name in ('a0', 'a1', 'd0', 'd1'))


def main():
    old, new = V.image(None), V.image(sys.argv[1])
    start, old_end = V.loaded_sections(old)[1]
    _, end = V.loaded_sections(new)[1]
    assert (old_end, end) == (0x60257000, 0x60257800)
    before, after = transfer_args(old), transfer_args(new)
    assert before == (0xA00DE000, 0x8061D000, old_end - start, 0x101), before
    assert after == (before[0], before[1], end - start, before[3]), after
    assert after[1] + after[2] == 0x80796800
    print(f'Section 1 transfer request length: {before[2]:#x} -> {after[2]:#x}, source and destination unchanged')
    for name, table, resume, width, height in SWITCHES:
        for value, h in ((6, 240), (7, 272)):
            target_old, = struct.unpack_from('<I', old, table + 4 * value - V.B)
            target_new, = struct.unpack_from('<I', new, table + 4 * value - V.B)
            assert end - 640 <= target_new < end
            stock = run_case(old, target_old, resume, width, height)
            patched = run_case(new, target_new, resume, width, height)
            assert patched == (640, h) and stock != patched, (name, value, stock, patched)
            print(f'{name} id {value}: {stock} -> {patched} via {target_new:#x}')

    for value, text in ((6, '65:24'), (7, '21:9')):
        old_n, old_list = struct.unpack_from('<HI', old, MENU + 2 - V.B)
        new_n, new_list = struct.unpack_from('<HI', new, MENU + 2 - V.B)
        stock = resolve(old, value, old_n, old_list)
        patched = resolve(new, value, new_n, new_list)
        assert stock is None and patched == (5, text), (value, stock, patched)
        print(f'menu id {value}: {stock} -> {patched}')
    print('RESULT PASS')


if __name__ == '__main__':
    main()
