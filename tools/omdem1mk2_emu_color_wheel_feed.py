#!/usr/bin/env python3
"""Run the colour-wheel value feed (patches/omdem1mk2/color_wheel, cw_get) against stock in the emulator.

    EM1_LOOKMEM=1 python3 patches/omdem1mk2/color_wheel/build.py      # fragment, look memory sd_loader
    python3 tools/omdem1mk2_emu_color_wheel_feed.py [color_wheel edits.json | release edits.json]

Patched image = stock + sd_loader (edits_lookmem.json: p_get) + halation (Section 6 loads the 100 KB gap) + color_wheel,
or a sealed release spec as it is (a spec with stock_sha256, e.g. releases/em1mk2/v0.4c27t/edits.json).
cw_get itself is also called as a producer site calls it, with sentinel d1 / a0 / a1: kept on the override and the
pass-through paths, and the stack as at entry (the getter's `ret [],4` returns to the site).
The producer 0x6097a1b5 runs to its C3d client call (0x6031629a, logged with the buffer) on both images with the same
settings model (getter 0x602da802 -> fixture) and the same P block:
  (i)   P_WON = 0, and no P at all: kind-5 buffer byte-identical to stock;
  (ii)  P_WON = 1, axis S / H / L: profile forced to 1, buffer[k] = the axis value of UI sector k (asymmetric vectors,
        clamp / round(v/3)), cursor = P_WCUR (3 and 255); then builder + renderer: vertex k (angle -30 k) gets radius
        23 + 9 (value + 5);
  (iii) kind 1 (Color Creator, settings 617/618) with P_WON = 1: buffer identical to stock.
Fixtures and UDF model: tools/omdem1mk2_emu_color_wheel_probe.py.
"""
import json
import struct
import sys
import tempfile
from pathlib import Path

import omdem1mk2_emu_color_wheel_probe as W
import omdem1mk2_emu_sdload as SD
import omdem1mk2_emu_validator as V
from penf_emulator import Region

PATCHES = SD.ROOT / 'patches/omdem1mk2'
P_SAT, P_HUE, P_LIGHT, P_WON, P_WAXIS, P_WCUR = 44, 56, 68, 84, 85, 86
SAT = [-10, -6, -5, -4, -1, 0, 1, 2, 4, 5, 6, 10]
HUE = [15, -15, 14, -13, 7, -8, 1, -1, 2, -2, 0, 5]
LIGHT = [-1, 2, -3, 4, -5, 6, -7, 8, -9, 10, -12, 13]
STOCK_SECTORS = {1: [1, -1, 2, -2, 3, -3, 4, -4, 5, -5, 0, 1], 2: [2] * 12, 3: [-2] * 12}


def combined_image(cw_spec):
    if 'stock_sha256' in json.loads(Path(cw_spec).read_text()):
        return V.image(str(cw_spec))                     # a sealed release: already has sd_loader and halation
    edits = []
    for path in (PATCHES / 'sd_loader/edits_lookmem.json', PATCHES / 'halation/edits.json', Path(cw_spec)):
        edits += [e for e in json.loads(path.read_text())['edits'] if e.get('kind', '0x100') == '0x100']
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
        json.dump({'edits': edits}, f)
    return V.image(f.name)


def model(profile=2, cursor=4, hue=7, vivid=2):
    m = bytearray(0x4000)
    put = lambda sid, v: struct.pack_into('<i', m, 4 * sid, v)
    put(906, profile)
    put(617, hue)
    put(618, vivid)
    for p, (first, cur) in {1: (925, 1089), 2: (937, 1094), 3: (949, 1095)}.items():
        for k, v in enumerate(STOCK_SECTORS[p]):
            put(first + k, v)
        put(cur, cursor)
    return bytes(m)


def p_block(won, axis=0, cur=255):
    blk = bytearray(0x200)
    struct.pack_into('<IH', blk, 0, 0x50314D45, SD.HANDLE)
    for off, vals in ((P_SAT, SAT), (P_HUE, HUE), (P_LIGHT, LIGHT)):
        blk[off:off + 12] = bytes(v & 0xFF for v in vals)
    blk[P_WON], blk[P_WAXIS], blk[P_WCUR] = won, axis, cur
    return bytes(blk)


def producer(img, code, kind, p=None):
    regions = [Region('req', 0x9F400000, struct.pack('<H', kind).ljust(64, b'\0'), 'r'),
               Region('view', 0x9F500000, bytes(0x2000), 'rw')]
    handle = bytearray(0x1000)            # handle 0 = no P (p_get returns 0)
    if p is not None:
        struct.pack_into('<H', handle, 0x4AE, SD.HANDLE)
        regions.append(Region('p', SD.P, p, 'r'))
    regions.append(Region('p_handle', SD.P_RAM, bytes(handle), 'r'))
    _, calls, _ = W.run(img, code, W.calls_bytes(W.RECEIVER), {'a0': 0x9F500000, 'a1': 0x9F400000}, 0x6097A573,
                        model=model(), extra=tuple(regions))
    client = [(regs, data) for regs, data in calls if regs[0] == 0x6031629A]
    assert len(client) == 1, [hex(c[0][0]) for c in calls]
    (_, k, _, _, _), data = client[0]
    return k & 0xFFFF, bytes(data[:13])


def s8(b):
    return b - 256 if b > 127 else b


def div3(v):
    q = (abs(v) + 1) // 3
    return -q if v < 0 else q


def expected(axis):
    if axis == 0:
        return [max(-5, min(5, v)) for v in SAT]
    return [max(-5, min(5, div3(v))) for v in (HUE if axis == 1 else LIGHT)]


def cw_get_regs(img, code, cw_at, sid, p):
    """cw_get called as a producer site does (`call cw_get,[],4`) with sentinel d1 / a0 / a1; returns the registers
    at the site's next instruction (the stack must be as at entry for the `ret [],4` to land there)."""
    handle = bytearray(0x1000)
    regions = []
    if p is not None:
        struct.pack_into('<H', handle, 0x4AE, SD.HANDLE)
        regions.append(Region('p', SD.P, p, 'r'))
    regions.append(Region('p_handle', SD.P_RAM, bytes(handle), 'r'))
    entry = W.call_bytes(cw_at, 0, 4)
    regs, _, _ = W.run(img, code, entry, {'d0': sid, 'd1': 0xD1D1D1D1, 'a0': 0xA0A0A0A0, 'a1': 0xA1A1A1A1},
                       W.CALLER + len(entry) - 1, model=model(), extra=tuple(regions))
    return regs


def main(cw_spec=str(PATCHES / 'color_wheel/edits.json')):
    code, syms = W.build_fixture()
    W.STUB_SYMS = syms
    W.KERN_REGION = W.kern_region(syms)
    stock = W.patched_image(syms)
    patched = W.patched_image(syms, combined_image(cw_spec))

    cw_at = int(json.loads((PATCHES / 'color_wheel/edits.json').read_text())['edits'][0]['addr'], 16)   # cw_get
    for label, sid, p, want in (('override 906', 906, p_block(1, 0, 3), 1),
                                ('override sector 925', 925, p_block(1, 0, 3), expected(0)[0]),
                                ('pass-through, P_WON = 0', 925, p_block(0, 0, 3), STOCK_SECTORS[1][0]),
                                ('pass-through, no P', 906, None, 2),
                                ('pass-through, other id', 617, p_block(1, 0, 3), 7)):
        r = cw_get_regs(patched, code, cw_at, sid, p)
        kept = ['d1', 'a1'] + (['a0'] if label.startswith('override') else [])   # the getter fixture uses a0
        print(f'cw_get {label}: d0 {r["d0"]:#x}, '
              f'd1 {r["d1"]:#x}, a0 {r["a0"]:#x}, a1 {r["a1"]:#x}')
        assert (r['d0'] & 0xFF if want < 0 else r['d0']) == (want & 0xFF if want < 0 else want), (label, r['d0'])
        assert all(r[k] == {'d1': 0xD1D1D1D1, 'a0': 0xA0A0A0A0, 'a1': 0xA1A1A1A1}[k] for k in kept), (label, r)

    base5 = producer(stock, code, 5)
    print(f'stock kind 5 (profile 2 in the model): {[s8(b) for b in base5[1][:12]]} + cursor {base5[1][12]}')
    for label, p in (('no P', None), ('P_WON = 0', p_block(0, 1, 3)), ('P_WON = 2', p_block(2, 0, 3))):
        got = producer(patched, code, 5, p)
        print(f'(i) patched, {label}: {"identical" if got == base5 else "DIFFERENT"}')
        assert got == base5

    for axis, name in enumerate('SHL'):
        for cur in (3, 255):
            kind, buf = producer(patched, code, 5, p_block(1, axis, cur))
            vals = [s8(b) for b in buf[:12]]
            print(f'(ii) P_WON = 1, axis {name}, P_WCUR {cur}: {vals} + cursor {buf[12]}')
            assert kind == 5 and vals == expected(axis) and buf[12] == cur
        err, codes = W.builder(patched, code, buf)
        verts, _, _, _ = W.render(patched, code, codes)
        radii = [r for _, r, _, _ in verts]
        assert codes[:12] == bytes(v + 5 for v in expected(axis)) and radii == [23 + 9 * c for c in codes[:12]]
        print(f'     builder codes {list(codes[:12])}, renderer radii (vertex k at -30k deg) {radii}')
    _, bad = producer(patched, code, 5, p_block(1, 3, 3))
    print(f'     P_WAXIS = 3 (invalid): sectors fall back to the getter, profile/cursor still overridden: '
          f'{[s8(b) for b in bad[:12]]} + cursor {bad[12]}')
    assert [s8(b) for b in bad[:12]] == STOCK_SECTORS[1] and bad[12] == 3

    base1 = producer(stock, code, 1)
    got1 = producer(patched, code, 1, p_block(1, 0, 3))
    print(f'(iii) kind 1 (617/618): stock {list(base1[1][:4])}, patched P_WON = 1 {list(got1[1][:4])}')
    assert got1 == base1
    print('OK: colour-wheel feed checks')


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))
