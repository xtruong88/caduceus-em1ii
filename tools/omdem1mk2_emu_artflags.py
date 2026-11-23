#!/usr/bin/env python3
"""Run the E-M1 Mark II Art Effect -> job-flag converter 0x6042285e in the MN103 emulator.

    python3 tools/omdem1mk2_emu_artflags.py [releases/em1mk2/<VERSION>/edits.json]

The converter is the E-P7 0x603eab39 equivalent and holds the halation flag-hook site 0x604228fc
(docs/OMD-EM1-II/HALATION.md). It reads the capture record through request+28: Art Effect byte +24951 and the two
hook bytes +24204 / +24205, then rewrites the flag word at a1. This harness calls it through a real `call` with
fabricated request / capture / flag memory and checks every Art Effect value 0..9 and every hook-byte combination
against the expected table: art 1 sets the Soft Focus flag 0x80; 0x4000 and 0x10000 are always cleared; 0x200000
follows +24204 | +24205. With a spec it checks the patched image gives the same results (a release that does not
touch the converter must not change it) unless --expect-changed is given.
"""
import argparse
import struct
import sys

import omdem1mk2_emu_validator as V
from penf_emulator import Region, execute

CONVERTER = 0x6042285E
CALLER, STACK, SP = 0x18020000, 0x18010000, 0x18010F00
REQUEST, FLAGS, CAPTURE = 0x18030000, 0x18040000, 0x18100000
ART, HOOK_A, HOOK_B = 24951, 24204, 24205
CAPTURE_SIZE = 0x6200

ART_SET = {1: 0x80, 2: 0x400, 3: 0x8000, 4: 0x2000, 5: 0x40}
ART_REPLACE = {6: (0x300, 0x100), 7: (0x300, 0x200), 8: (0x1800, 0x800), 9: (0x1800, 0x1000)}
SEEDS = (0x00000000, 0xFFFFFFFF, 0x00214321, 0x00010080)


def expected(art, hook_a, hook_b, seed):
    flags = seed
    if art in ART_SET:
        flags |= ART_SET[art]
    elif art in ART_REPLACE:
        clear, value = ART_REPLACE[art]
        flags = (flags & ~clear) | value
    flags &= ~0x4000 & ~0x10000 & 0xFFFFFFFF
    flags = flags | 0x200000 if (hook_a or hook_b) else flags & ~0x200000
    return flags & 0xFFFFFFFF


MONOTONE = 5
PICTURE_MODE = 24203


def run(img, art, hook_a, hook_b, seed):
    capture = bytearray(CAPTURE_SIZE)
    capture[ART], capture[HOOK_A], capture[HOOK_B] = art, hook_a, hook_b
    # Picture mode Monotone: the stock converter never reads it, and it keeps the halation gate (which hooks this
    # converter's entry, tools/omdem1mk2_emu_halation_flag.py) off, so a release with halation must match the table.
    capture[PICTURE_MODE] = MONOTONE
    request = bytearray(0x100)
    struct.pack_into('<I', request, 28, CAPTURE)
    # call 0x6042285e,[a2,a3],20 -- the frame both stock callers (0x6041dde2, 0x60420af1) use; then halt.
    code = b'\xdd' + struct.pack('<i', CONVERTER - CALLER) + bytes([0x30, 20]) + b'\xcb'
    regions = (
        Region('caller', CALLER, code, 'rx'),
        *V.main_regions(img),
        Region('stack', STACK, bytes(0x1000), 'rw'),
        Region('request', REQUEST, bytes(request), 'r'),
        Region('flags', FLAGS, struct.pack('<I', seed), 'rw', capture=True),
        Region('capture', CAPTURE, bytes(capture), 'r'),
    )
    marker_a2, marker_a3 = 0x11112222, 0x33334444
    r = execute(regions, {'pc': CALLER, 'sp': SP, 'a0': REQUEST, 'a1': FLAGS, 'a2': marker_a2, 'a3': marker_a3},
                CALLER + 7, limit=2000)
    if r['fault'] or r['registers']['pc'] != CALLER + 7:
        raise SystemExit(f'art {art}: emulation stopped at {r["registers"]["pc"]:#x}: {r["fault"]}')
    if (r['registers']['a2'], r['registers']['a3'], r['registers']['sp']) != (marker_a2, marker_a3, SP):
        raise SystemExit(f'art {art}: call frame not restored: {r["registers"]}')
    flags = next(c for c in r['memory'] if c['name'] == 'flags')
    return struct.unpack('<I', bytes.fromhex(flags['hex']))[0]


def check(img, label):
    cases = 0
    for art in range(10):
        for hook_a, hook_b in ((0, 0), (1, 0), (0, 1), (1, 1)):
            for seed in SEEDS:
                got, want = run(img, art, hook_a, hook_b, seed), expected(art, hook_a, hook_b, seed)
                if got != want:
                    raise SystemExit(f'{label}: art {art} hooks {hook_a}/{hook_b} seed {seed:#x}: '
                                     f'got {got:#010x}, expected {want:#010x}')
                cases += 1
    print(f'{label}: {cases} cases match the flag table (art 1 -> 0x80 Soft Focus)')


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('spec', nargs='?')
    a = p.parse_args()
    check(V.image(None), 'stock')
    if a.spec:
        check(V.image(a.spec), 'patched')
    print('RESULT PASS')


if __name__ == '__main__':
    sys.exit(main())
