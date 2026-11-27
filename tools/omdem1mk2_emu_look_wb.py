#!/usr/bin/env python3
"""Check the E-M1 Mark II look WB patch (patches/omdem1mk2/look_wb) in the MN103 emulator.

    python3 tools/omdem1mk2_emu_look_wb.py [--base releases/em1mk2/v0.4c25t/edits.json] [--patch <look_wb edits.json>]
    python3 tools/omdem1mk2_emu_look_wb.py releases/em1mk2/<version>/edits.json   (a spec with the patch: the seal)

The patch redirects the 14 image-pipeline reads of the WB fine-tune (A-B 0x84F9, G-M 0x9679; ARCHITECTURE_AND_MEMORY_MAP
§7.8) from the getter 0x6005e6cf to wb_get. Base = the release spec the patch is merged into; patched = base + patch.
Every run executes each site's own call instruction (same target, mask and frame) from a synthetic caller, with the
real getter reading the camera's own property registry (tools/omdem1mk2_emu_spare_setting.py fixtures; property data
written directly) and P in an uncached fixture region.

1. Static: the 14 sites call wb_get in the patched image and the getter in the base; the RAW pair calls the getter in
   both; wb_get's p_get call lands on sd_loader's p_get (`movhu (0x621e24ae),d2`) of the base.
2. Per site x state: override cases return the look's value, sign-extended like the getter, with d1 = idx and
   d2/d3/a1/a2/a3/sp/mdr equal to the stock getter run; every other case equals the stock getter run in every
   register except psw. States: no P, look inactive, picture mode != P_CCMODE, P_CCMODE 0, WB category 0/1/2/3/4
   (3 = CWB stays stock), built-in look with and without WB, built-in index 16, P_INIT 0, card look with WB, card not
   loaded / failed, card index past the pack, hostile records (flag 0xFF / 0x80 / 0x02 / 0x81 / 0x03, values
   +8 / -8 / 127 / -128 on either axis), and the -7 / +7 corners.
3. A non-WB key (0x9481, 0x8121, 0xF709) sent to wb_get equals the stock getter in every register except psw.
4. The capture WB segment 0x6033a1d2 -> 0x6033a5ab, run natively on a 25.6 KB capture block for category 1 with
   preset 0..14 (Flash and the default branch included) and categories 0 / 2 / 3 / 4. No look: the patched block equals
   stock byte for byte. Card look (+5 / -4): the patched block equals the stock block with +5 / -4 stored as the
   fine-tune (so the derived fields follow too), A / G at capture+24248 / +24250; CWB: equal to stock.
Not emulated: what happens after the segment (WB bracketing, the gain calculator), the compact slot's consumer and
live view.
"""
import argparse
import json
import struct
import sys
import tempfile
from pathlib import Path

import omdem1mk2_emu_spare_setting as SS
import omdem1mk2_emu_validator as V
from penf_emulator import Region

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'patches/omdem1mk2/look_wb'))
import build as WB  # noqa: E402

GETTER, BUILTIN = WB.GETTER, WB.BUILTIN
KEY_A, KEY_G, KEY_PMODE, KEY_WBCAT = 0x84F9, 0x9679, 0x9481, 0x8121
HANDLE_ADDR, P_BASE, HANDLE = 0x621E24AE, 0xA1B00000, 1
P_ADDR = P_BASE + (HANDLE << 7)
P_MAGIC = 0x50314D45
P_SD_STATE, P_BUF, P_LOOK, P_INIT, P_NLOOKS, P_ACTIVE, P_CCMODE = 6, 8, 16, 20, 28, 30, 32
BUF_ADDR = P_BASE + 0x400
CC_RAW = 9
SITE_IDX = {0x6033A366: 15, 0x6033A37B: 15, 0x6033A571: 1, 0x6033A58A: 1}     # others read index 0
SAME = ('d1', 'd2', 'd3', 'a1', 'a2', 'a3', 'sp', 'mdr')
# capture WB segment (ARCHITECTURE_AND_MEMORY_MAP §7.8): entry loads the capture pointer from (8,sp) and switches on
# capture+24158; every branch joins at 0x6033a5ab. Capture block and frame live in fixture RAM.
SEG_START, SEG_END = 0x6033A1D2, 0x6033A5AB
CAP, CAP_SIZE, CAP_SP = 0x62700000, 0x6400, 0x62710F00
PRESET_TABLE = 0x604FF91C                       # 14 jump targets for capture+24154 = 0..13 (0x6033a247)


def record(flag, ab, gm, mono=False):
    r = bytearray(64)
    r[25], r[26], r[27] = flag & 0xFF, ab & 0xFF, gm & 0xFF
    r[45] = 1 if mono else 0
    return bytes(r)


def look_value(rec, key):
    """The value the design gives for a record, or None (stock)."""
    if rec[25] & 0x81 != 1:
        return None
    ab, gm = (struct.unpack('b', rec[i:i + 1])[0] for i in (26, 27))
    if not (-7 <= ab <= 7 and -7 <= gm <= 7):
        return None
    return ab if key == KEY_A else gm


class Bench:
    def __init__(self, spec):
        self.emu = SS.Emu(spec)

    def addr(self, key):
        return struct.unpack('<I', self.emu.read(SS.REGISTRY + (key >> 4) * 8 + 4, 4))[0]

    def settings(self, pmode, wbcat, stored=None):
        """stored = None: fine-tune A 3, 4, ... and G -2, -3, ... per index; (a, g): every index holds a / g."""
        e = self.emu
        a = bytes((3 + i) & 0xFF for i in range(24)) if stored is None else bytes([stored[0] & 0xFF]) * 24
        g = bytes((-2 - i) & 0xFF for i in range(24)) if stored is None else bytes([stored[1] & 0xFF]) * 24
        e.write(self.addr(KEY_A), a)
        e.write(self.addr(KEY_G), g)
        e.write(self.addr(KEY_PMODE), bytes([pmode]))
        e.write(self.addr(KEY_WBCAT), bytes([wbcat]))

    def capture(self, cat, preset, p_region, handle):
        """Run the capture WB segment 0x6033a1d2 -> 0x6033a5ab on a fresh capture block; -> the block after it."""
        e = self.emu
        block = bytearray((i * 37 + 11) & 0xFF for i in range(CAP_SIZE))   # every byte known, so stray writes show
        struct.pack_into('<H', block, 24158, cat)
        struct.pack_into('<H', block, 24154, preset)
        struct.pack_into('<HH', block, 24280, 2, 3)                       # one-touch slot 2, CWB slot 3
        struct.pack_into('<H', block, 24156, 5300)                        # CWB Kelvin
        struct.pack_into('<H', block, 24326, 0)
        block[24953] = 0
        e.write(CAP, bytes(block))
        e.write(CAP_SP, bytes(8) + struct.pack('<I', CAP) + bytes(0x40))
        e.write(HANDLE_ADDR, struct.pack('<H', handle))
        e.run(SEG_START, SEG_END, {'sp': CAP_SP}, extra=(p_region,))
        return e.read(CAP, CAP_SIZE)

    def run(self, target, key, idx, p_region, handle):
        self.emu.write(HANDLE_ADDR, struct.pack('<H', handle))
        return self.emu.call(target, 0xC0, 12, {'d0': key, 'd1': idx, 'a0': 0}, extra=(p_region,))


def p_region(active=1, ccmode=CC_RAW, init=1, look=0, sd_state=1, nlooks=2, cards=()):
    p = bytearray(0x1000)
    struct.pack_into('<IH', p, 0x80, P_MAGIC, HANDLE)
    struct.pack_into('<H', p, 0x80 + P_SD_STATE, sd_state)
    struct.pack_into('<I', p, 0x80 + P_BUF, BUF_ADDR)
    struct.pack_into('<HH', p, 0x80 + P_LOOK, look, 0)
    struct.pack_into('<H', p, 0x80 + P_INIT, init)
    struct.pack_into('<H', p, 0x80 + P_NLOOKS, nlooks)
    p[0x80 + P_ACTIVE] = active
    struct.pack_into('<I', p, 0x80 + P_CCMODE, ccmode)
    for i, rec in enumerate(cards):
        o = BUF_ADDR - P_BASE + 64 + 64 * i
        p[o:o + 64] = rec
    return Region('p', P_BASE, bytes(p), 'r')


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('spec', nargs='?', help='a release spec that already carries the look WB edits (the seal): the '
                    'base is that spec without them')
    ap.add_argument('--base', default=str(ROOT / 'releases/em1mk2/v0.4c25t/edits.json'))
    ap.add_argument('--patch', default=str(ROOT / 'patches/omdem1mk2/look_wb/edits.json'))
    a = ap.parse_args()
    patch = json.loads(Path(a.patch).read_text())['edits']
    with tempfile.TemporaryDirectory() as t:
        if a.spec:
            full = json.loads(Path(a.spec).read_text())
            missing = [e['addr'] for e in patch if e not in full['edits']]
            assert not missing, f'spec lacks the look WB edits at {missing}'
            base_spec = {**full, 'edits': [e for e in full['edits'] if e not in patch]}
        else:
            base_spec = json.loads(Path(a.base).read_text())
        base, merged = Path(t) / 'base.json', Path(t) / 'edits.json'
        base.write_text(json.dumps(base_spec))
        merged.write_text(json.dumps({**base_spec, 'edits': base_spec['edits'] + patch}))
        pat, stock = Bench(str(merged)), Bench(str(base))
    fails = 0

    # 1. static
    wb_get = int(patch[0]['addr'], 16)
    for site, *_ in WB.SITES:
        assert WB.call_to(pat.emu.img, site) == wb_get, f'{site:#x} not redirected'
        assert WB.call_to(stock.emu.img, site) == GETTER, f'{site:#x} not stock in the base'
    for site in WB.RAW_SITES:
        assert WB.call_to(pat.emu.img, site) == GETTER, f'RAW site {site:#x} redirected'
    pget = struct.unpack('<i', bytes.fromhex(patch[0]['new'])[0x2A:0x2E])[0] + wb_get + 0x29
    got = pat.emu.img[pget - V.B:pget - V.B + 6]
    assert got == bytes.fromhex('fcaeae241e62'), f'p_get call {pget:#x} is not sd_loader p_get ({got.hex()})'
    print(f'static: 14 sites -> wb_get {wb_get:#x}, RAW pair stock, p_get {pget:#x} matches the base sd_loader')

    builtin = pat.emu.img[BUILTIN - V.B:BUILTIN - V.B + 1024]
    with_wb = [i for i in range(16) if look_value(builtin[64 * i:64 * i + 64], KEY_A) is not None]
    without = [i for i in range(16) if builtin[64 * i + 25] == 0]
    assert with_wb and without, 'need built-in looks with and without WB'
    bi_wb, bi_none = with_wb[0], without[0]
    card_wb = record(1, 5, -4)
    hostile = [record(f, ab, gm) for f, ab, gm in ((0xFF, 1, 1), (0x80, 1, 1), (0x02, 1, 1), (0x81, 1, 1),
                                                   (0x03, 2, 3), (1, 8, 0), (1, -8, 0), (1, 0, 127), (1, 0, -128),
                                                   (1, -7, 7), (1, 7, -7))]
    # (name, pmode, wbcat, handle, p kwargs, record giving the look's value or None)
    states = [
        ('no P', CC_RAW, 1, 0, {}, None),
        ('look inactive', CC_RAW, 1, HANDLE, dict(active=0, look=bi_wb), None),
        ('picture mode != P_CCMODE', 5, 1, HANDLE, dict(look=bi_wb), None),
        ('P_CCMODE 0', 0, 1, HANDLE, dict(ccmode=0, look=bi_wb), None),
        ('CWB', CC_RAW, 3, HANDLE, dict(look=bi_wb), None),
        ('P_INIT 0', CC_RAW, 1, HANDLE, dict(init=0, look=bi_wb), None),
        ('built-in index 16', CC_RAW, 1, HANDLE, dict(look=16), None),
        (f'built-in {bi_none} without WB', CC_RAW, 1, HANDLE, dict(look=bi_none), None),
        ('card not loaded', CC_RAW, 1, HANDLE, dict(init=2, sd_state=0, cards=(card_wb,)), None),
        ('card failed', CC_RAW, 1, HANDLE, dict(init=2, sd_state=0xFFFF, cards=(card_wb,)), None),
        ('card index past the pack', CC_RAW, 1, HANDLE, dict(init=2, look=2, cards=(card_wb, card_wb)), None),
    ] + [(f'built-in {bi_wb}, category {c}', CC_RAW, c, HANDLE, dict(look=bi_wb), builtin[64 * bi_wb:64 * bi_wb + 64])
         for c in (0, 1, 2, 4)] + [
        ('card look 1 with WB', CC_RAW, 1, HANDLE, dict(init=2, look=1, cards=(record(0, 0, 0), card_wb)), card_wb),
    ] + [(f'card record flag {r[25]:#x} a_b {struct.unpack("b", r[26:27])[0]} g_m {struct.unpack("b", r[27:28])[0]}',
          CC_RAW, 1, HANDLE, dict(init=2, cards=(r,)), r) for r in hostile]

    overrides = 0
    for name, pmode, wbcat, handle, pk, rec in states:
        region = p_region(**pk)
        pat.settings(pmode, wbcat)
        stock.settings(pmode, wbcat)
        before = fails
        for site, key, _ in WB.SITES:
            idx = SITE_IDX.get(site, 0)
            s = stock.run(GETTER, key, idx, region, handle)
            p = pat.run(wb_get, key, idx, region, handle)
            want = look_value(rec, key) if rec is not None else None
            if want is None:
                bad = [r for r in s if r != 'psw' and s[r] != p[r]]
            else:
                overrides += 1
                bad = [r for r in SAME if s[r] != p[r]]
                if p['d0'] != want & 0xFFFFFFFF:
                    bad.append(f'd0 {p["d0"]:#x} != {want}')
                if p['d1'] != idx:
                    bad.append('d1 != idx')
            if bad:
                fails += 1
                print(f'FAIL {name} @ {site:#x}: {bad}')
        if fails == before:
            kind = 'stock' if rec is None or look_value(rec, KEY_A) is None else 'look value'
            print(f'{name}: {kind} at all 14 sites')

    # 4. capture WB segment, natively, whole capture block compared
    table = [struct.unpack_from('<I', pat.emu.img, PRESET_TABLE - V.B + 4 * i)[0] for i in range(14)]
    flash = [i for i, t in enumerate(table) if t == 0x6033A35C]
    assert flash, 'no preset table entry reaches the Flash reads'
    look = (5, -4)                                  # differs from every stored value, so a missed redirect shows
    with_look = p_region(init=2, cards=(record(1, *look),))
    no_look = p_region(active=0)
    runs = [(1, p) for p in range(15)] + [(c, 0) for c in (0, 2, 3, 4)]
    for cat, preset in runs:
        for b in (pat, stock):
            b.settings(CC_RAW, cat)
        base = stock.capture(cat, preset, no_look, 0)
        bad = []
        if pat.capture(cat, preset, no_look, HANDLE) != base:
            bad.append('no look: block differs from stock')
        got = pat.capture(cat, preset, with_look, HANDLE)
        if cat == 3:
            want = base
        else:
            stock.settings(CC_RAW, cat, stored=look)
            want = stock.capture(cat, preset, no_look, 0)
            if want == base:
                bad.append('the look value does not change the stock block (case not exercised)')
        if got != want:
            diff = [i for i in range(CAP_SIZE) if got[i] != want[i]]
            bad.append(f'look: block differs at +{diff[:8]}')
        if cat != 3 and struct.unpack_from('<hh', got, 24248) != look:      # A at +24248, G at +24250
            bad.append(f'capture+24248/24250 = {struct.unpack_from("<hh", got, 24248)} != look {look}')
        if bad:
            fails += 1
            print(f'FAIL capture category {cat} preset {preset}: {bad}')
    print(f'capture segment: {len(runs)} category/preset runs (Flash = preset {flash}); no look = stock byte for byte; '
          f'look = stock with the look stored as fine-tune, except CWB = stock')

    region = p_region(look=bi_wb)
    pat.settings(CC_RAW, 1)
    stock.settings(CC_RAW, 1)
    for key in (KEY_PMODE, KEY_WBCAT, 0xF709):
        s, p = stock.run(GETTER, key, 0, region, HANDLE), pat.run(wb_get, key, 0, region, HANDLE)
        bad = [r for r in s if r != 'psw' and s[r] != p[r]]
        if bad:
            fails += 1
            print(f'FAIL non-WB key {key:#x}: {bad}')
    print('non-WB keys through wb_get: equal to the stock getter')
    print(f'{len(states)} states x 14 sites, {overrides} override runs')
    print('RESULT ' + ('PASS' if not fails else f'FAIL ({fails})'))
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
