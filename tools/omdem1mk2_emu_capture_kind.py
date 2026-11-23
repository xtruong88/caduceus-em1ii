#!/usr/bin/env python3
"""Run the E-M1 Mark II capture-kind -> job-type mapper 0x6042257f in the MN103 emulator.

    python3 tools/omdem1mk2_emu_capture_kind.py [releases/em1mk2/<VERSION>/edits.json]

The halation gate (docs/OMD-EM1-II/HALATION.md) skips the capture kinds the E-P7 skips for grain: 0x2001, 0x2006,
0x1008, 0x1006. On this body the kind is request+194 and the mapper (E-P7 equivalent of the kind -> type mapper)
returns: 0x2001 / 0x2006 -> 0x120 if request+206 == 2 else 0x110, unless the helper 0x60425e48 returns 1 (then
0x1000); 0x1008 / 0x1006 -> 0; every other kind -> 0x1000 (an ordinary still). The helper is replaced by a 3-byte
fixture returning 0 or 1; the mapper itself runs from the image.
"""
import argparse
import struct

import omdem1mk2_emu_validator as V
from penf_emulator import Region, execute

MAPPER, HELPER = 0x6042257F, 0x60425E48
CALLER, STACK, REQUEST = 0x18020000, 0x18010000, 0x18040000
KINDS = (0x2001, 0x2006, 0x1008, 0x1006, 0x1000, 0x1001, 0x100C, 0x2000, 0x0000)


def expected(kind, sub, helper):
    if kind in (0x2001, 0x2006):
        return 0x1000 if helper == 1 else (0x120 if sub == 2 else 0x110)
    if kind in (0x1008, 0x1006):
        return 0
    return 0x1000


def run(img, kind, sub, helper):
    m = bytearray(img)
    # helper fixture, called with call [],0: `mov 1,d0; ret [],0` or `clr d0; nop; ret [],0`
    stub = b'\x80\x01\xdf\x00\x00' if helper else b'\x00\xcb\xdf\x00\x00'
    m[HELPER - V.B:HELPER - V.B + len(stub)] = stub
    request = bytearray(0x100)
    struct.pack_into('<H', request, 194, kind)
    struct.pack_into('<H', request, 206, sub)
    struct.pack_into('<I', request, 28, 0x18050000)
    code = b'\xdd' + struct.pack('<i', MAPPER - CALLER) + bytes([0xA0, 12]) + b'\xcb'
    r = execute((Region('caller', CALLER, code, 'rx'), *V.main_regions(bytes(m)),
                 Region('stack', STACK, bytes(0x1000), 'rw'), Region('request', REQUEST, bytes(request), 'r')),
                {'pc': CALLER, 'sp': STACK + 0xF00, 'a0': REQUEST, 'a2': 0x5A5A5A5A}, CALLER + 7, limit=2000)
    if r['fault'] or r['registers']['pc'] != CALLER + 7:
        raise SystemExit(f'kind {kind:#x}: stopped at {r["registers"]["pc"]:#x}: {r["fault"]}')
    assert (r['registers']['sp'], r['registers']['a2']) == (STACK + 0xF00, 0x5A5A5A5A), r['registers']
    return r['registers']['d0'] & 0xFFFF


def check(img, label):
    n = 0
    for kind in KINDS:
        for sub in (0, 2):
            for helper in (0, 1):
                got, want = run(img, kind, sub, helper), expected(kind, sub, helper)
                assert got == want, (label, hex(kind), sub, helper, hex(got), hex(want))
                n += 1
    print(f'{label}: {n} cases; 0x2001/0x2006 -> 0x110/0x120, 0x1008/0x1006 -> 0, other kinds -> 0x1000')


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('spec', nargs='?')
    a = p.parse_args()
    check(V.image(None), 'stock')
    if a.spec:
        check(V.image(a.spec), 'patched')
    print('RESULT PASS')


if __name__ == '__main__':
    main()
