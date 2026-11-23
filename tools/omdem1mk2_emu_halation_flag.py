#!/usr/bin/env python3
"""Run the halation flag gate (patches/omdem1mk2/halation) through the real flag converter in the MN103 emulator.

    python3 tools/omdem1mk2_emu_halation_flag.py SPEC [--force-stage N]

SPEC is an edits.json that contains the halation edits (a release, or patches/omdem1mk2/halation/edits.json, which
is then applied alone). The settings store is the real one (tools/omdem1mk2_emu_spare_setting.py): the stage is
written to sid 961 through the facade, and hl_flag reads it back through the stock property getter 0x6005e6cf.
For every stage (0..3 and the out-of-range 7), Art Effect (0, 1 Soft Focus, 2), picture mode (Vivid 1, Natural 2,
Monotone 5, Color Creator 10, MONO 12, Art Filters 100 and 104), capture kind (0x1000, 0x1001, 0x1002, 0x2000, 0x2001,
0x2006, 0x1008, 0x1006) and two flag seeds, the patched converter must give exactly the stock flag word, and the job
marker 0xA0 | stage at params+31 only when the gate holds: stage 1..3, Art Effect 0, picture mode < 100 and not 5 / 12,
kind 0x1000 or 0x1001. The Soft Focus flag 0x80 is not set here (hl_route sets it). a2/a3/sp restored.
With --force-stage N (a test build) the stage is N whatever sid 961 holds.
"""
import argparse
import itertools
import json
import struct

import omdem1mk2_emu_spare_setting as S
import omdem1mk2_emu_validator as V
from penf_emulator import Region

CONVERTER = 0x6042285E
REQUEST, FLAGS, CAPTURE = 0x18030000, 0x18040000, 0x18100000
STAGES = (0, 1, 2, 3, 7)
ARTS = (0, 1, 2)
MODES = (1, 2, 5, 10, 12, 100, 104)
KINDS = (0x1000, 0x1001, 0x1002, 0x2000, 0x2001, 0x2006, 0x1008, 0x1006)
SEEDS = (0x00000000, 0x00214321)


def gate(stage, art, mode, kind):
    return 1 <= stage <= 3 and art == 0 and mode < 100 and mode not in (5, 12) and kind in (0x1000, 0x1001)


def convert(emu, art, mode, kind, seed, more=()):
    capture = bytearray(0x6200)
    capture[24951], capture[24203] = art, mode
    request = bytearray(0x100)
    struct.pack_into('<I', request, 28, CAPTURE)
    struct.pack_into('<H', request, 194, kind)
    params = bytearray(32)                                  # the caller's params block: flags at +12, marker at +31
    struct.pack_into('<I', params, 12, seed)
    extra = (Region('request', REQUEST, bytes(request), 'r'), Region('params', FLAGS - 12, bytes(params), 'rw', True),
             Region('capture', CAPTURE, bytes(capture), 'r'), *more)
    regs = emu.call(CONVERTER, 0x30, 20, {'a0': REQUEST, 'a1': FLAGS, 'a2': 0x11112222, 'a3': 0x33334444}, extra)
    assert (regs['a2'], regs['a3'], regs['sp']) == (0x11112222, 0x33334444, V.SP), regs
    out = emu.captured['params']
    assert out[:12] == bytes(12) and out[16:31] == bytes(15), 'params outside the flags and marker changed'
    return struct.unpack_from('<I', out, 12)[0], out[31]

P_HANDLE_ADDR, P_BASE, P_MAGIC = 0x621E24AE, 0xA1B00000, 0x50314D45
P_AT = 0xA1C00000                                      # handle 0x2000
CARD_AT = 0xA1C01000
BUILTIN, TINT_OFF = 0x60BC8150, 47


def p_block(active, init, look, nlooks=0):
    blk = bytearray(256)
    struct.pack_into('<IH', blk, 0, P_MAGIC, (P_AT - P_BASE) >> 7)
    struct.pack_into('<I', blk, 8, CARD_AT if init == 2 else 0)
    struct.pack_into('<HHH', blk, 16, look, 0, init)
    struct.pack_into('<H', blk, 28, nlooks)
    blk[30] = active
    return bytes(blk)


def check_tint(patched, img):
    """Gated shot (stage 2, Vivid, no Art Effect, kind 0x1000): the marker's tint bits follow the active look."""
    assert patched.set_value(961, 2) == 0
    builtin = [img[BUILTIN - V.B + 64 * k + TINT_OFF] for k in range(16)]
    card = bytearray(64 + 64 * 3)
    for i, t in enumerate((2, 3, 4)):
        card[64 + 64 * i + TINT_OFF] = t
    want = lambda t: 0xA2 | ((t - 1) << 2 if 1 <= t <= 4 else 0)
    cases = [(None, 0xA2), (p_block(0, 1, 3), 0xA2)]
    cases += [(p_block(1, 1, k), want(builtin[k])) for k in range(16)]
    cases += [(p_block(1, 2, k, 3), want((2, 3, 4)[k])) for k in range(3)]
    cases += [(p_block(1, 2, 5, 3), want(builtin[5]))]                # index past the card pack -> built-in table
    n = 0
    for blk, marker in cases:
        handle = 0 if blk is None else (P_AT - P_BASE) >> 7
        patched.write(P_HANDLE_ADDR, struct.pack('<H', handle))
        more = () if blk is None else (Region('p', P_AT, blk, 'r'), Region('card', CARD_AT, bytes(card), 'r'))
        flags, got = convert(patched, 0, 1, 0x1000, 0, more)
        assert not flags & 0x80 and got == marker, (n, hex(flags), hex(got), hex(marker))
        n += 1
    patched.write(P_HANDLE_ADDR, bytes(2))
    tints = sorted(set(builtin))
    print(f'tint: {n} cases (no P, look inactive, 16 built-in looks with tints {tints}, card looks 2/3/4, index past the '
          'card pack) give the expected marker; tint 0 or > 4 stays red')


def spec_with_release(path):
    """A patch-only spec is applied on top of the newest catalog release, as the release builder would."""
    spec = json.load(open(path))
    if 'camera' in spec:
        return path
    base = json.load(open(V.ROOT / 'releases/em1mk2/v0.4c17/edits.json'))
    base['edits'] = spec['edits'] + base['edits']
    out = '/tmp/halation_check_edits.json'
    json.dump(base, open(out, 'w'))
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('spec')
    p.add_argument('--force-stage', type=int, default=0)
    a = p.parse_args()
    stock, patched = S.Emu(None), S.Emu(spec_with_release(a.spec))
    cases = list(itertools.product(ARTS, MODES, KINDS, SEEDS))
    stock_flags = {}
    for case in cases:                                                  # stock does not read the stage
        stock_flags[case], marker = convert(stock, *case)
        assert marker == 0
    n = added = 0
    for stage in STAGES:
        assert patched.set_value(961, stage) == 0
        effective = a.force_stage or stage
        for case in cases:
            art, mode, kind, seed = case
            want, want_marker = stock_flags[case], 0
            if gate(effective, art, mode, kind):
                want_marker = 0xA0 | effective                       # tint bits 0 = red
                added += 1
            got, marker = convert(patched, art, mode, kind, seed)
            assert (got, marker) == (want, want_marker), (stage, art, mode, hex(kind), hex(seed), hex(got), hex(marker))
            n += 1
    if not a.force_stage:
        check_tint(patched, V.image(spec_with_release(a.spec)))
    print(f'{n} converter runs: flags = stock exactly; marker 0xA0|stage at params+31 only in the {added} gated cases '
          f'({"stage forced to %d" % a.force_stage if a.force_stage else "stage from sid 961"})')
    print('RESULT PASS')


if __name__ == '__main__':
    main()
