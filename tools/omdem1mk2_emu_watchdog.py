#!/usr/bin/env python3
"""Run the E-M1 Mark II hardware watchdog's run-time timeout settings in the MN103 emulator, stock and with halation.

    python3 tools/omdem1mk2_emu_watchdog.py [SPEC]

SPEC: a release edits.json with the halation edits (default: v0.4c17 + those edits built here).

The halation patch (patches/omdem1mk2/halation) raises the timeout 10 s -> 30 s at the two run-time settings, as E-P7
v0.31b did (docs/HALATION_RED.md section 22):
  - SYS_WDT on, 0x600792bc: sets the on flag 0x62095e4a and passes 10 (`mov 10,d0` at 0x600792c4) to the setter wrapper
    0x60079282 -> setter 0x600226fd;
  - the restore after a flash operation, `mov 10,d0` at 0x6005aecc before the setter (the path turns it off with 0 at
    0x6005aeb0 / 0x6005ae8c, runs the operation, then restores).
The setter waits for 0x98e000a4 to be 0, writes the seconds into bits 0..5 of 0x98e0008c (upper bits kept), writes
0x20041001 to 0x98e000a4 and waits for the hardware to clear it; the run stops at that wait (0x60022728), which needs the
real timer. Checks, from v0.4c17 stock and v0.4c17 + halation: the field becomes 10 / 30 with the upper bits of the old
register value kept, the handshake word is written, SYS_WDT's on flag is 1; the setter, its wrapper and every other
setting site (0 / 1, and the 10 before the `bra .` at 0x600cdfb5) are byte for byte stock.
Not emulated: the timer itself (seconds are the unit per the E-P7 debug command `time XXX`), SYS_WDT's kicks.
"""
import json
import struct
import sys
import tempfile

import omdem1mk2_emu_halation_route as HR
import omdem1mk2_emu_validator as V
from penf_emulator import Region, execute

REGS, CTRL, ACK = 0x98E00000, 0x8C, 0xA4
ON_FLAG = 0x62095E4A
SETTER, WRAPPER, WAIT = 0x600226FD, 0x60079282, 0x60022728
WDT_ON, FLASH_RESTORE = 0x600792BC, 0x6005AECC
OLD_CTRL = 0x0BADC13F                      # upper bits must survive; low 6 bits are the seconds
OTHER_SITES = (0x600cdfac, 0x60059a4a, 0x6005aeb0, 0x6005ae8c, 0x600792ce)


def spec_path():
    base = json.load(open(HR.BASE_SPEC))
    hl, _, _ = HR.load_build().make_edits(0, 0)
    base['edits'] = hl['edits'] + base['edits']
    f = tempfile.NamedTemporaryFile('w', suffix='.json', delete=False)
    json.dump(base, f)
    f.close()
    return f.name


def run(img, entry, via_call):
    regs = bytearray(0x100)
    struct.pack_into('<I', regs, CTRL, OLD_CTRL)
    if via_call:                                          # call WDT_ON,[],4 from a caller stub
        code = b'\xdd' + struct.pack('<i', entry - V.CALLER) + b'\x00\x04\xcb'
        pc = V.CALLER
    else:                                                 # the flash path's tail: pc at the `mov 10,d0`
        code, pc = b'\xcb', entry
    r = execute([Region('caller', V.CALLER, code, 'rx'), *V.main_regions(img),
                 Region('stack', V.STACK, bytes(0x1000), 'rw'),
                 Region('wdt', REGS, bytes(regs), 'rw', True),
                 Region('flag', ON_FLAG & ~0xFFF, bytes(0x1000), 'rw', True)],
                dict(pc=pc, sp=V.SP, d2=0x1234), WAIT, limit=10_000, breakpoints=[WAIT])
    assert r['registers']['pc'] == WAIT and not r['fault'], (hex(entry), r['status'], r['fault'])
    mem = {c['name']: bytes.fromhex(c['hex']) for c in r['memory']}
    ctrl, ack = struct.unpack_from('<I', mem['wdt'], CTRL)[0], struct.unpack_from('<I', mem['wdt'], ACK)[0]
    flag = struct.unpack_from('<H', mem['flag'], ON_FLAG & 0xFFF)[0]
    return ctrl, ack, flag


def main():
    stock, patched = V.image(HR.BASE_SPEC), V.image(sys.argv[1] if len(sys.argv) > 1 else spec_path())
    for name, entry, via_call in (('SYS_WDT on', WDT_ON, True), ('flash restore', FLASH_RESTORE, False)):
        for label, img, secs in (('stock', stock, 10), ('halation', patched, 30)):
            ctrl, ack, flag = run(img, entry, via_call)
            assert ctrl == (OLD_CTRL & ~0x3F) | secs, (name, label, hex(ctrl))
            assert ack == 0x20041001, (name, label, hex(ack))
            assert flag == (1 if via_call else 0), (name, label, flag)
            print(f'{name:14s} {label:8s}: 0x98e0008c {OLD_CTRL:#x} -> {ctrl:#x} ({secs} s), handshake {ack:#x}'
                  + (', on flag 1' if via_call else ''))
    B = V.B
    for a in (*OTHER_SITES, SETTER, WRAPPER):
        assert stock[a - B:a - B + 16] == patched[a - B:a - B + 16], hex(a)
    diff = [a + B for a in range(0x60050000 - B, 0x60080000 - B) if stock[a] != patched[a]]   # SYS / watchdog code
    assert diff == [0x6005AECD, 0x600792C5], [hex(a) for a in diff]
    print('only the two timeout bytes differ; setter, wrapper and the other settings (0 / 1 / 10 before `bra .`) stock')
    print('RESULT PASS')


if __name__ == '__main__':
    main()
