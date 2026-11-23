#!/usr/bin/env python3
"""Show in the MN103 emulator that the halation job marker (params+31 -> job+35) changes nothing in stock job handling.

    python3 tools/omdem1mk2_emu_job_marker.py

Design: plans/reports/research-261123-0838-em1ii-halation-job-marker.md. The flag converter's caller builds a 32-byte params
block on its stack (zeroed per shot); the job constructor 0x6038f173 allocates a new 15,484-byte job and copies the block
word for word to job+4..+35 (loop at 0x6038f2a4). hl_flag can therefore leave a magic byte at params+31 that reaches
job+35, where the work-list wrapper (job) and the combiner stub (request - 11329) can read it.
Checks, stock image, a params block with the Soft Focus flag 0x80 and marker byte 0 vs 0xA5:
  1. the constructor returns the same job and error, writes the same request, and the two jobs differ only at job+35;
  2. the work-list builder 0x60392e0d on both jobs leaves them still differing only at job+35 (same work list).
Fixture boundaries: malloc returns a fixed job address; boot-ROM memset / memcpy; .data from its init image.
"""
import struct

import omdem1mk2_emu_rules as R
import omdem1mk2_emu_validator as V
from penf_emulator import Region, execute

CTOR, BUILDER = 0x6038F173, 0x60392E0D
CALLER, STACK, PARAMS, ERR, REQUEST, JOB = 0x18020000, 0x18010000, 0x18030000, 0x18031000, 0x18040000, 0x19000000
MALLOC = 0x600231FE
MAGIC, MARK = 0xA5, 35
JOB_SIZE = 0x4000


def image():
    m = bytearray(V.image(None))
    o = MALLOC - V.B
    m[o:o + 9] = b'\xfc\xdc' + struct.pack('<I', JOB) + b'\xdf\x00\x04'      # mov JOB,a0; ret [],4
    return bytes(m)


def common(img):
    return [*V.main_regions(img), Region('stack', STACK, bytes(0x1000), 'rw'),
            Region('rom_memset', R.ROM_MEMSET[0], bytes.fromhex(R.ROM_MEMSET[1]), 'rx'),
            Region('rom_memcpy', R.ROM_MEMCPY[0], bytes.fromhex(R.ROM_MEMCPY[1]), 'rx'),
            Region('data', 0x61F7D540, img[0x60258000 - V.B:0x602AE000 - V.B], 'rw'), Region('cpuid', 0x8050, bytes(4), 'r')]


def call(img, target, frame, regs, extra):
    code = b'\xdd' + struct.pack('<i', target - CALLER) + bytes([0xF0, frame]) + b'\xcb'
    r = execute([Region('caller', CALLER, code, 'rx'), *common(img), *extra],
                dict({'pc': CALLER, 'sp': STACK + 0xF00}, **regs), CALLER + 7, limit=2_000_000)
    if r['fault'] or r['registers']['pc'] != CALLER + 7:
        raise SystemExit(f'{target:#x} stopped at {r["registers"]["pc"]:#x}: {r["fault"]}')
    return r['registers'], {c['name']: bytes.fromhex(c['hex']) for c in r['memory']}


def construct(img, marker):
    params = bytearray(32)                 # callback, request, key bytes, flags (0x80), type 0x1000, ..., marker at +31
    struct.pack_into('<IIBBBBIH', params, 0, 0x6041DD00, REQUEST, 1, 1, 0, 0x65, 0x80, 0x1000)
    params[31] = marker
    regs, mem = call(img, CTOR, 44, {'a0': PARAMS, 'a1': ERR, 'd0': 0},
                     [Region('params', PARAMS, bytes(params), 'r'), Region('err', ERR, bytes(16), 'rw', True),
                      Region('request', REQUEST, bytes(0x2000), 'rw', True), Region('job', JOB, bytes(JOB_SIZE), 'rw', True)])
    return regs['d0'], mem


def build(img, job):
    _, mem = call(img, BUILDER, 40, {'a0': JOB}, [Region('job', JOB, job, 'rw', True)])
    return mem['job']


def diff(a, b):
    return [i for i in range(len(a)) if a[i] != b[i]]


def main():
    img = image()
    (j0, m0), (j1, m1) = construct(img, 0), construct(img, MAGIC)
    assert j0 == j1 == JOB, (hex(j0), hex(j1))
    assert m0['request'] == m1['request'] and m0['err'] == m1['err']
    assert diff(m0['job'], m1['job']) == [MARK] and m1['job'][MARK] == MAGIC
    assert struct.unpack_from('<I', m0['job'], 16)[0] & 0x80
    print('constructor: same job, request and error; jobs differ only at job+35 (= params+31), flag 0x80 kept')
    b0, b1 = build(img, m0['job']), build(img, m1['job'])
    assert diff(b0, b1) == [MARK]
    print('work-list builder: the two jobs still differ only at job+35')
    print('RESULT PASS')


if __name__ == '__main__':
    main()
