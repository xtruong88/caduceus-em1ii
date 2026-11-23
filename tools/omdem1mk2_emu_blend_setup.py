#!/usr/bin/env python3
"""Run the E-M1 Mark II Soft Focus blend setup 0x60398ee1 (work-list entry) in the MN103 emulator.

    python3 tools/omdem1mk2_emu_blend_setup.py [releases/em1mk2/<VERSION>/edits.json]

This fixture calls Blend Setup directly. See omdem1mk2_emu_work_list.py for the Art work-list dispatch conditions.
Blend Setup looks up records 0x1000 (image) and 0x1061 through bufidx 0x6038c01c. The records start at job+6592,
are 88 bytes each, and have their ID at +76. It initializes the embedded request at job+11364 via 0x60390dbe,
sets stage 0xf005 at request+12 and effect 0x0402 at request+656,
copies the two records (16 words each) to request+20 / +84, describes an output buffer at request+340 and queues it.
Checks, on the fabricated job:
  1. it returns 0; request = job+11364; stage / effect / both record copies / the output descriptor are as above;
  2. the selector 0x603f1653 maps the request it built to combiner 11;
  3. at the blend-setup hook site 0x60398f5f (E-P7 halation probe site, same 6 bytes) a2 = request, a3 = record 0x1000;
  4. without record 0x1061 it returns 48 and leaves the request untouched.
Boot-ROM memcpy / memset as in the other harnesses. Fixture boundaries (frame-correct stubs): output allocation 0x6038bc07 (returns record index 7), queue submit
0x60390536 (0 = queued), 0x60390293 and the release 0x6038beea. bufidx and the request init run from the image.
"""
import argparse
import struct

import omdem1mk2_emu_rules as R
import omdem1mk2_emu_validator as V
from penf_emulator import Region, execute

BLEND, SELECTOR, HOOK = 0x60398EE1, 0x603F1653, 0x60398F5F
CALLER, STACK, JOB = 0x18020000, 0x18010000, 0x18100000
RECORDS, REQUEST = 6592, 11364
OUT_INDEX = 7
STUBS = {  # address: bytes, matching each caller's call frame
    0x6038BC07: bytes([0x80, OUT_INDEX, 0xDF, 0xF0, 84]),  # mov 7,d0; ret [d2,d3,a2,a3],84
    0x60390536: bytes([0x00, 0xDF, 0xF0, 24]),             # clr d0;   ret [d2,d3,a2,a3],24
    0x60390293: bytes([0xDF, 0x20, 8]),                    # ret [a2],8
    0x6038BEEA: bytes([0xDF, 0x30, 12]),                   # ret [a2,a3],12
}
WIDTH, HEIGHT = 5180, 3888       # 5180: not 32-aligned, so the stride rounding (to 5184) is exercised


def image(spec):
    m = bytearray(V.image(spec))
    for a, b in STUBS.items():
        m[a - V.B:a - V.B + len(b)] = b
    return bytes(m)


def record(seed, ident, w=0, h=0):
    r = bytearray(struct.pack('<22I', *((seed + i * 0x01010101) & 0xFFFFFFFF for i in range(22))))
    struct.pack_into('<HH', r, 12, w, h)
    struct.pack_into('<I', r, 76, ident)
    return bytes(r)


def make_job(with_1061=True):
    job = bytearray(0x4000)
    for i in range(48):
        struct.pack_into('<I', job, RECORDS + 88 * i + 76, 0xFFFF0000 + i)      # unused ids
    job[RECORDS + 88 * 2:RECORDS + 88 * 3] = record(0x11000000, 0x1000, WIDTH, HEIGHT)
    if with_1061:
        job[RECORDS + 88 * 5:RECORDS + 88 * 6] = record(0x22000000, 0x1061)
    job[RECORDS + 88 * OUT_INDEX:RECORDS + 88 * (OUT_INDEX + 1)] = record(0x33000000, 0x7777)
    return bytes(job)


def run(img, job, entry=BLEND, stop_at=None):
    code = b'\xfc\xff' + struct.pack('<i', entry - CALLER) + b'\xcb'               # calls d32 (work-list entries)
    regions = (Region('caller', CALLER, code, 'rx'), *V.main_regions(img), Region('stack', STACK, bytes(0x1000), 'rw'),
               Region('job', JOB, job, 'rw', capture=True),
               Region('rom_memcpy', R.ROM_MEMCPY[0], bytes.fromhex(R.ROM_MEMCPY[1]), 'rx'),
               Region('rom_memset', R.ROM_MEMSET[0], bytes.fromhex(R.ROM_MEMSET[1]), 'rx'))
    r = execute(regions, {'pc': CALLER, 'sp': STACK + 0xF00, 'a0': JOB}, CALLER + 6, limit=200_000,
                breakpoints=[stop_at] if stop_at else [])
    if stop_at:
        assert r['status'] == 'breakpoint' and r['registers']['pc'] == stop_at, (r['status'], r['fault'])
        return r['registers'], None
    if r['fault'] or r['registers']['pc'] != CALLER + 6:
        raise SystemExit(f'stopped at {r["registers"]["pc"]:#x}: {r["fault"]}')
    assert r['registers']['sp'] == STACK + 0xF00, r['registers']
    return r['registers'], bytes.fromhex(r['memory'][0]['hex'])


def selector_on(img, request_bytes):
    ctx = struct.pack('<II', 0, JOB + REQUEST).ljust(0x100, b'\0')
    code = b'\xdd' + struct.pack('<i', SELECTOR - CALLER) + bytes([0xA0, 12]) + b'\xcb'
    r = execute((Region('caller', CALLER, code, 'rx'), *V.main_regions(img), Region('stack', STACK, bytes(0x1000), 'rw'),
                 Region('ctx', 0x18030000, ctx, 'r'), Region('request', JOB + REQUEST, request_bytes, 'r')),
                {'pc': CALLER, 'sp': STACK + 0xF00, 'a0': 0x18030000}, CALLER + 7, limit=5000)
    assert not r['fault'] and r['registers']['pc'] == CALLER + 7, r['fault']
    return r['registers']['d0'] & 0xFF


def check(img, label):
    job = make_job()
    regs, after = run(img, job)
    assert regs['d0'] & 0xFFFF == 0, hex(regs['d0'])
    req = after[REQUEST:REQUEST + 0x800]
    rec = lambda i: job[RECORDS + 88 * i:RECORDS + 88 * (i + 1)]
    assert struct.unpack_from('<H', req, 12)[0] == 0xF005 and struct.unpack_from('<H', req, 656)[0] == 0x0402
    assert req[20:84] == rec(2)[:64] and req[84:148] == rec(5)[:64], 'record copies'
    out = req[340:]
    descriptor = struct.unpack_from('<HHHHHH', out, 8)    # +8 format, +10 stride (32-aligned), +12 w, +14 h, +16/+18 0
    assert descriptor == (0x302, (WIDTH + 31) & ~31, WIDTH, HEIGHT, 0, 0), ('output descriptor', descriptor)
    assert out[:4] == rec(OUT_INDEX)[:4] and out[20:56] == rec(OUT_INDEX)[28:64], 'output record copy'
    print(f'{label}: request = job+11364, stage 0xf005, effect 0x0402, records 0x1000 / 0x1061 copied, output queued')
    assert selector_on(img, req) == 11
    print(f'{label}: selector maps that request to combiner 11')
    regs, _ = run(img, job, stop_at=HOOK)
    assert regs['a2'] == JOB + REQUEST and regs['a3'] == JOB + RECORDS + 88 * 2, {k: hex(regs[k]) for k in ('a2', 'a3')}
    print(f'{label}: hook site {HOOK:#x}: a2 = request, a3 = record 0x1000 (job+6592+88*idx)')
    missing = make_job(with_1061=False)
    regs, after = run(img, missing)
    assert regs['d0'] & 0xFFFF == 48 and after == missing, (hex(regs['d0']), 'job changed')
    print(f'{label}: without record 0x1061 it returns 48 and writes nothing')


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('spec', nargs='?')
    a = p.parse_args()
    check(image(None), 'stock')
    if a.spec:
        check(image(a.spec), 'patched')
    print('RESULT PASS')


if __name__ == '__main__':
    main()
