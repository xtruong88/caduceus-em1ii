#!/usr/bin/env python3
"""Run the E-M1 Mark II bus-address mapper 0x6006888f in the MN103 emulator and check its address map.

    python3 tools/omdem1mk2_emu_mapper.py [releases/em1mk2/<VERSION>/edits.json]

The CPU-side image pass (grain / halation, docs/OMD-EM1-II/HALATION.md) reaches image buffers through this mapper.
Unlike the E-P7's (which treated every address below 0xb0000000 as direct), it:
  - refuses addresses below 0x84000000 and 0xa0000000..0xafffffff: prints "[exad]change_addr_err!!" and returns 0,
    without locking (those ranges are CPU-addressable directly: use them as they are);
  - otherwise locks, flushes, and maps the bucket that holds the address (0x84..0x87 is 64 MB, the rest 128 MB)
    into this CPU's window: returns
    0xb0000000 | (addr & 0x07ffffff) (0xb8000000 | ... for 0x98..0x9f and 0xf8..0xff), writes the bucket code into the
    window registers (0x98100058 / 0x9810004c, +0x400 per CPU id 0..2, low byte kept), stores the mode in the per-CPU
    table 0xa274d410[cpu], then unlocks with the lock's token.
Every bucket is checked for CPU ids 0, 1 and 2. Lock / unlock / flush / log are counting fixtures
(tools/emu_fixtures/em1_mapper_stubs.s); the window registers and the mode table are plain memory.
"""
import argparse
import struct

import omdem1mk2_emu_sdload as SD
import omdem1mk2_emu_validator as V
from penf_emulator import Region, execute

MAPPER = 0x6006888F
ROUTINES = {'lock': 0x6006E9D0, 'unlock': 0x6006EA19, 'flush': 0x60068709, 'log': 0x60023188}
CALLER, STACK, FIXTURE, COUNTS = 0x18020000, 0x18010000, 0x18060000, 0x18070000
MMIO, MODES = 0x98100000, 0x6274D000     # mode table 0xa274d410 = uncached alias of 0x6274d410
LOW = 0x5A                                # low byte the window registers keep

# (first address of the bucket, window base, bucket code ORed into the registers, mode stored)
BUCKETS = [(0x84000000, 0xB0000000, 0x1000, 9), (0x88000000, 0xB0000000, 0x2100, 10),
           (0x90000000, 0xB0000000, 0x3200, 11), (0x98000000, 0xB8000000, 0x3200, 11),
           (0xB0000000, 0xB0000000, 0x7600, 0), (0xB8000000, 0xB0000000, 0x8700, 1),
           (0xC0000000, 0xB0000000, 0x9800, 2), (0xC8000000, 0xB0000000, 0xA900, 3),
           (0xD0000000, 0xB0000000, 0xBA00, 4), (0xD8000000, 0xB0000000, 0xCB00, 5),
           (0xE0000000, 0xB0000000, 0xDC00, 6), (0xE8000000, 0xB0000000, 0xED00, 7),
           (0xF0000000, 0xB0000000, 0xFE00, 8), (0xF8000000, 0xB8000000, 0xFE00, 8)]
REFUSED = (0x00000000, 0x60021020, 0x83FFFFFC, 0xA0000000, 0xA3BB7140, 0xAFFFFFFC)


def image_with_fixture(img, syms):
    m = bytearray(img)
    for name, addr in ROUTINES.items():
        m[addr - V.B:addr - V.B + 5] = b'\xdc' + struct.pack('<i', syms[name] - addr)
    return bytes(m)


def run(img, fixture, address, cpu):
    mmio = bytearray(0x1000)
    for c in range(3):
        struct.pack_into('<II', mmio, 0x4C + 0x400 * c, 0xFFFF0000 | LOW, 0)
        struct.pack_into('<I', mmio, 0x58 + 0x400 * c, 0xFFFF0000 | LOW)
    code = b'\xdd' + struct.pack('<i', MAPPER - CALLER) + bytes([0xF0, 28]) + b'\xcb'
    regions = (Region('caller', CALLER, code, 'rx'), *V.main_regions(img), Region('stack', STACK, bytes(0x1000), 'rw'),
               Region('fixture', FIXTURE, fixture, 'rx'), Region('counts', COUNTS, bytes(0x20), 'rw', capture=True),
               Region('mmio', MMIO, bytes(mmio), 'rw', capture=True),
               Region('modes', MODES, bytes(0x1000), 'rw', capture=True),
               Region('modes_unc', MODES + 0x40000000, bytes(0x1000), 'rw', alias_of='modes'),
               Region('cpuid', 0x8050, struct.pack('<I', cpu), 'r'))
    r = execute(regions, {'pc': CALLER, 'sp': STACK + 0xF00, 'a0': address, 'a2': 0x5A5A5A5A, 'a3': 0x3C3C3C3C},
                CALLER + 7, limit=5000)
    if r['fault'] or r['registers']['pc'] != CALLER + 7:
        raise SystemExit(f'{address:#x} cpu {cpu}: stopped at {r["registers"]["pc"]:#x}: {r["fault"]}')
    regs = r['registers']
    assert (regs['sp'], regs['a2'], regs['a3']) == (STACK + 0xF00, 0x5A5A5A5A, 0x3C3C3C3C), regs
    mem = {c['name']: bytes.fromhex(c['hex']) for c in r['memory']}
    counts = struct.unpack('<5I', mem['counts'][:20])
    windows = [struct.unpack_from('<II', mem['mmio'], 0x58 + 0x400 * c)[0] for c in range(3)]
    windows_b = [struct.unpack_from('<I', mem['mmio'], 0x4C + 0x400 * c)[0] for c in range(3)]
    mode = struct.unpack_from('<I', mem['modes'], 0x410 + 4 * cpu)[0]
    return regs['a0'], counts, windows, windows_b, mode


def check(img, fixture, label):
    n = 0
    for cpu in range(3):
        for address in REFUSED:
            result, counts, windows, windows_b, mode = run(img, fixture, address, cpu)
            assert result == 0 and counts[:4] == (0, 0, 0, 1), (label, hex(address), cpu, hex(result), counts)
            assert windows == [0xFFFF0000 | LOW] * 3 and mode == 0, (label, hex(address), 'state changed')
            n += 1
        ends = [b[0] for b in BUCKETS[1:]] + [0x100000000]
        ends[BUCKETS.index(next(b for b in BUCKETS if b[0] == 0x98000000))] = 0xA0000000
        for (first, window, bits, want_mode), end in zip(BUCKETS, ends):
            for address in (first, first + 0x0123456C, end - 4):     # 0x84.. is 64 MB, the others 128 MB
                result, counts, windows, windows_b, mode = run(img, fixture, address, cpu)
                assert result == window | (address & 0x07FFFFFF), (label, hex(address), cpu, hex(result))
                assert counts == (1, 1, 1, 0, 0x1234), (label, hex(address), cpu, counts)
                expect = [0xFFFF0000 | LOW] * 3
                expect[cpu] = LOW | bits
                assert windows == expect and windows_b == expect, (label, hex(address), cpu,
                                                                   [hex(w) for w in windows + windows_b])
                assert mode == want_mode, (label, hex(address), cpu, mode)
                n += 1
    print(f'{label}: {n} cases; < 0x84000000 and 0xa0000000..0xafffffff refused (log, 0, no lock); '
          f'14 buckets map into 0xb0000000 / 0xb8000000 for CPU 0..2 with lock / flush / unlock')


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('spec', nargs='?')
    a = p.parse_args()
    fixture, syms = SD.assemble_fixture(SD.ROOT / 'tools/emu_fixtures/em1_mapper_stubs.s', FIXTURE, COUNTS=COUNTS)
    check(image_with_fixture(V.image(None), syms), fixture, 'stock')
    if a.spec:
        check(image_with_fixture(V.image(a.spec), syms), fixture, 'patched')
    print('RESULT PASS')


if __name__ == '__main__':
    main()
