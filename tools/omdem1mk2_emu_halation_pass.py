#!/usr/bin/env python3
"""Run the E-M1 Mark II halation pass (patches/omdem1mk2/halation/hl_pass.s) in the MN103 emulator against its model.

    python3 tools/omdem1mk2_emu_halation_pass.py

hl_pass runs on fabricated 0x0302 records and buffers with the camera's own mapper 0x6006888f, mode getter 0x60068b78 and mode
setter 0x60068b88 from the image; lock / unlock / flush / log are the counting fixtures of tools/emu_fixtures/em1_mapper_stubs.s,
malloc / free the bump allocator tools/emu_fixtures/em1_halation_alloc.s. The window registers and mode table are memory.
  M  the photo == tools/omdem1mk2_halation_model.py bit for bit: every stage x tint on a direct buffer (0xa...), a windowed
     buffer (0xc8...) and one whose rows cross the 0xd0000000 bucket edge (two window pieces per row); and where the
     camera puts the record (tools/omdem1mk2_emu_image_heap.py): both image heap bases 0x8dc64e00 / 0x9b758800 and rows
     crossing 0x90000000 and 0x98000000 (0xb8 window); padding untouched
  C  coverage cap (daylight) and a frame without highlights: photo untouched (no write pass)
  F  each malloc failing in turn, a bad format, a bus address below 0x84000000: photo untouched
  always: every malloc freed, locks == unlocks, the window mode left as it was, sp / a2 / a3 restored
"""
import struct
import sys

import numpy as np

import omdem1mk2_emu_mapper as MP
import omdem1mk2_emu_sdload as SD
import omdem1mk2_emu_validator as V
import omdem1mk2_halation_model as HM
from penf_emulator import Region, execute

CALLER, STACK = 0x18020000, 0x18010000
PASS_AT, ALLOC_AT, MAPFIX_AT = 0x18200000, 0x18210000, 0x18060000
COUNTS, CTL, RECORD, HEAP = 0x18070000, 0x18080000, 0x18090000, 0x18400000
MALLOC, FREE = 0x600231FE, 0x6002323D
SERVICES = dict(LOCK=0x6006E9D0, UNLOCK=0x6006EA19, FLUSH=0x60068709, MAPPER=0x6006888F, MODEGET=0x60068B78,
                MODESET=0x60068B88, MALLOC=MALLOC, FREE=FREE)
W, H, STRIDE = 640, 448, 672                      # pixels; stride > width leaves padding that must stay untouched
PITCH = STRIDE * 2
LIGHTS = [(100, 100, 8), (400, 300, 6)]          # glows without reaching the coverage cap (19 of 70 cells)


def build():
    pass_code, syms = SD.assemble_fixture(SD.ROOT / 'patches/omdem1mk2/halation/hl_pass.s', PASS_AT, **SERVICES)
    alloc_code, asyms = SD.assemble_fixture(SD.ROOT / 'tools/emu_fixtures/em1_halation_alloc.s', ALLOC_AT, CTL=CTL)
    map_code, msyms = SD.assemble_fixture(SD.ROOT / 'tools/emu_fixtures/em1_mapper_stubs.s', MAPFIX_AT, COUNTS=COUNTS)
    img = bytearray(MP.image_with_fixture(V.image(None), msyms))
    for addr, name in ((MALLOC, 'malloc'), (FREE, 'free')):
        img[addr - V.B:addr - V.B + 5] = b'\xdc' + struct.pack('<i', asyms[name] - addr)
    return bytes(img), pass_code, syms['hl_pass'], alloc_code, map_code


def pieces(bus, size):
    """CPU-visible (address, bus offset, length) pieces of a buffer: direct 0xa..., else per 128 MB bucket in its window."""
    if 0xA0000000 <= bus < 0xB0000000:
        return [(bus, 0, size)]
    out, off = [], 0
    while off < size:
        a = bus + off
        n = min(size - off, ((a >> 27) + 1 << 27) - a)
        base = 0xB8000000 if (0x98000000 <= a < 0xA0000000 or a >= 0xF8000000) else 0xB0000000
        out.append((base | (a & 0x07FFFFFF), off, n))
        off += n
    return out


def run(env, pic, bus, word, fmt=0x0302, fail=0):
    img, pass_code, entry, alloc_code, map_code = env
    size = PITCH * H
    record = bytearray(88)
    struct.pack_into('<I', record, 0, bus)
    struct.pack_into('<HHHH', record, 8, fmt, STRIDE, W, H)
    struct.pack_into('<I', record, 72, size)
    mmio = bytearray(0x1000)
    for c in range(3):
        struct.pack_into('<I', mmio, 0x4C + 0x400 * c, 0x5A)
        struct.pack_into('<I', mmio, 0x58 + 0x400 * c, 0x5A)
    code = b'\xdd' + struct.pack('<i', entry - CALLER) + bytes([0xF0, 96]) + b'\xcb'
    regions = [Region('caller', CALLER, code, 'rx'), *V.main_regions(img), Region('stack', STACK, bytes(0x1000), 'rw'),
               Region('hl', PASS_AT, pass_code, 'rx'), Region('alloc', ALLOC_AT, alloc_code, 'rx'),
               Region('mapfix', MAPFIX_AT, map_code, 'rx'), Region('counts', COUNTS, bytes(0x20), 'rw', True),
               Region('ctl', CTL, struct.pack('<4I', fail, 0, 0, HEAP), 'rw', True),
               Region('heap', HEAP, bytes(0x20000), 'rw'), Region('record', RECORD, bytes(record), 'r'),
               Region('mmio', MP.MMIO, bytes(mmio), 'rw', True), Region('modes', MP.MODES, bytes(0x1000), 'rw', True),
               Region('modes_unc', MP.MODES + 0x40000000, bytes(0x1000), 'rw', alias_of='modes'),
               Region('cpuid', 0x8050, bytes(4), 'r')]
    parts = pieces(bus, size)
    for i, (addr, off, n) in enumerate(parts):
        regions.append(Region(f'pic{i}', addr, pic[off:off + n], 'rw', True))
    r = execute(regions, {'pc': CALLER, 'sp': STACK + 0xF00, 'a0': RECORD, 'd0': word, 'a2': 0x5A5A5A5A,
                          'a3': 0x3C3C3C3C}, CALLER + 7, limit=60_000_000)
    if r['fault'] or r['registers']['pc'] != CALLER + 7:
        raise SystemExit(f'bus {bus:#x} word {word:#x}: stopped at {r["registers"]["pc"]:#x}: {r["fault"]}')
    regs = r['registers']
    assert (regs['sp'], regs['a2'], regs['a3']) == (STACK + 0xF00, 0x5A5A5A5A, 0x3C3C3C3C), regs
    mem = {c['name']: bytes.fromhex(c['hex']) for c in r['memory']}
    out = b''.join(mem[f'pic{i}'] for i in range(len(parts)))
    locks, unlocks = struct.unpack('<2I', mem['counts'][:8])
    _, mallocs, frees, _ = struct.unpack('<4I', mem['ctl'][:16])
    assert locks == unlocks, (hex(bus), locks, unlocks)
    assert frees == (mallocs - (1 if fail and fail <= mallocs else 0)), (hex(bus), fail, mallocs, frees)
    assert struct.unpack_from('<I', mem['modes'], 0x410)[0] == 0, 'window mode not restored'
    return out, len(parts), locks


def main():
    env = build()
    pic = HM.scene(W, H, PITCH, LIGHTS)
    n = 0
    # The last four are where the camera puts a full-size record: the mode-0 image heaps 0x8dc64e00..0x9f5e7400 and
    # 0x9b758800..0x9f5e7400 (pool creation 0x60411597 / 0x604115b6, chosen by 0x604111b7 through 0x60553370), reached
    # from the job callback op 19 (0x6041f8ae -> 0x6041fcf6 -> 0x6041febc -> 0x604254fe mode 0 -> 0x60411126).
    for bus, label in ((0xA3000000, 'direct'), (0xC8001000, 'windowed'), (0xCFFF8000, 'crossing 0xd0000000'),
                       (0x8DC64E00, 'camera heap base'), (0x8FFF8000, 'camera heap, crossing 0x90000000'),
                       (0x97FF8000, 'camera heap, crossing 0x98000000 (0xb8 window)'),
                       (0x9B758800, 'second camera heap base (0xb8 window)')):
        for stage in (1, 2, 3):
            for tint in (1, 2, 3, 4):
                want, cnt = HM.model(pic, W, H, PITCH, stage, tint)
                got, parts, locks = run(env, pic, bus, tint << 4 | stage)
                assert cnt and want != pic, 'scene must glow'
                if got != want:
                    a, b = np.frombuffer(got, np.uint8), np.frombuffer(want, np.uint8)
                    i = int(np.argmax(a != b))
                    raise SystemExit(f'M {label} stage {stage} tint {tint}: first difference at byte {i} '
                                     f'(row {i // PITCH}, col {i % PITCH}): {a[i]} != {b[i]}')
                n += 1
        print(f'M {label}: 12 stage x tint cases == model ({parts} piece(s), {locks} locks)')
    for label, scene in (('daylight (coverage cap)', HM.scene(W, H, PITCH, [], wall=0.6)),
                         ('no highlights', HM.scene(W, H, PITCH, []))):
        assert HM.model(scene, W, H, PITCH, 2, 1)[0] == scene
        assert run(env, scene, 0xC8001000, 0x12)[0] == scene, label
        print(f'C {label}: untouched')
    for fail in (1, 2, 3):
        assert run(env, pic, 0xC8001000, 0x12, fail=fail)[0] == pic, ('malloc', fail)
    assert run(env, pic, 0xC8001000, 0x12, fmt=0x0C02)[0] == pic, 'format'
    assert run(env, pic, 0x80001000, 0x12)[0] == pic, 'below 0x84000000'
    assert run(env, pic, 0xC8001000, 0x04)[0] == pic, 'stage 4'
    print('F malloc 1..3 failing, format 0x0c02, bus 0x80001000, stage 4: untouched, frees balanced')
    print(f'RESULT PASS ({n} model cases)')


if __name__ == '__main__':
    sys.exit(main())
