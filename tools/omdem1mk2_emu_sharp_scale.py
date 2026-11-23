#!/usr/bin/env python3
"""Run the E-M1 Mark II ISP sharpening-gain helper tail (0x603e8bb6..0x603e8c97) on stock and a patched image.

    python3 tools/omdem1mk2_emu_sharp_scale.py patches/omdem1mk2/sharp_scale/edits.json
    python3 tools/omdem1mk2_emu_sharp_scale.py releases/em1mk2/<VERSION>/edits.json

The run starts where the helper has its class index in d0 (0..5), the ISO amount in d3 and the second factor in d2,
and stops at its `ret` 0x603e8c97. Frame fixtures (offsets from the helper's own code): (16,sp) request (Sharpness =
signed byte +1795, table selectors +1810 / +1811), (28,sp) -> flag byte, (40,sp) -> output record, (44,sp) -> job
key, (49,sp)..(51,sp) bytes; a3 -> record with byte +26. Flag byte, +26 and (49,sp) all non-zero take the
alternate base table 0x6052a946.

Checks, over Sharpness -3..+3, class 0..5, both base tables, the three gain tables, three ISO amounts and keys
11 (COLOR), 2 (Natural), 1 (Vivid), 2000 / 2001 (Flat / Log):
  1. stock output byte 2 == a Python model of the stock code (index clamp 0..10, u16 table, two x/256 caps);
  2. patched output == stock at Sharpness +2, scaled by k = Sharpness + 2: k <= 0 -> 0, 1 -> /4, 2 -> /2,
     3 -> x3/4, >= 4 -> unchanged; output bytes 0/1 unchanged;
  3. Flat / Log (2000 / 2001): patched == stock on every input.
"""
import argparse
import struct

import omdem1mk2_emu_validator as V
from penf_emulator import Region, execute

B = V.B
START, RET = 0x603E8BB6, 0x603E8C97
STACK, SP = 0x18010000, 0x18010800
REQ, KEY, FLAG, A3, OUT = 0x18100000, 0x18101000, 0x18102000, 0x18103000, 0x18104000
BASE_MAIN, BASE_ALT = 0x6052A940, 0x6052A946
GAIN_MAIN, GAIN_ALT = 0x6052A94C, 0x6052AACA          # +1810 or +1811 set -> GAIN_ALT


def run(img, *, cls, s, key, amount, factor, alt, sel):
    stack = bytearray(0x1000)
    frame = SP - STACK
    for off, val in ((16, REQ), (28, FLAG), (40, OUT), (44, KEY)):
        struct.pack_into('<I', stack, frame + off, val)
    stack[frame + 49] = 1 if alt else 0
    stack[frame + 50], stack[frame + 51] = 0x5A, 0xA5
    req = bytearray(0x800)
    req[1795] = s & 0xFF
    req[1810], req[1811] = (1, 0) if sel == 1 else (0, 1) if sel == 2 else (0, 0)
    regions = [*V.main_regions(img),
               Region('stack', STACK, bytes(stack), 'rw'),
               Region('req', REQ, bytes(req), 'r'),
               Region('key', KEY, struct.pack('<I', key), 'r'),
               Region('flag', FLAG, bytes([1 if alt else 0]), 'r'),
               Region('a3', A3, bytes(27 * [0]) if not alt else bytes(26 * [0]) + b'\x01', 'r'),
               Region('output', OUT, bytes(4), 'rw', capture=True)]
    regs = {'pc': START, 'sp': SP, 'd0': cls, 'd2': factor, 'd3': amount, 'a3': A3}
    r = execute(regions, regs, 0xFFFFFFF0, limit=500, breakpoints=[RET])
    assert r['status'] == 'breakpoint' and not r['fault'] and r['registers']['pc'] == RET, (r['status'], r['fault'])
    out = bytes.fromhex(next(m['hex'] for m in r['memory'] if m['name'] == 'output'))
    assert out[:2] == b'\x5a\xa5', out.hex()
    return out[2]


def model_stock(img, *, cls, s, key, amount, factor, alt, sel):
    u8 = lambda a: img[a - B]
    u16 = lambda a: struct.unpack_from('<H', img, a - B)[0]
    if alt:
        idx = u8(BASE_ALT + cls) + s
    elif key in (2000, 2001):
        idx = s + 4
    else:
        idx = u8(BASE_MAIN + cls) + s
    idx = min(max(idx, 0), 10)
    gain = min(255, u16((GAIN_ALT if sel else GAIN_MAIN) + 2 * idx) * (amount & 0xFF) >> 8)
    return min(255, gain * (factor & 0xFFFF) >> 8)


def scaled(gain, s):
    k = s + 2
    return gain if k >= 4 else (3 * gain) >> 2 if k == 3 else gain >> 1 if k == 2 else gain >> 2 if k == 1 else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('spec')
    stock, new = V.image(None), V.image(ap.parse_args().spec)
    runs = log_runs = 0
    for key in (11, 2, 1, 2000, 2001):
        for alt in (False, True):
            for sel in (0, 1, 2):
                for amount, factor in ((37, 256), (18, 256), (37, 200)):
                    for cls in range(6):
                        at = dict(cls=cls, key=key, amount=amount, factor=factor, alt=alt, sel=sel)
                        top = run(stock, s=2, **at)
                        for s in range(-3, 4):
                            old, patched = run(stock, s=s, **at), run(new, s=s, **at)
                            assert old == model_stock(stock, s=s, **at), ('stock model', s, at, old)
                            want = old if key in (2000, 2001) else scaled(top, s)
                            assert patched == want, ('patched', s, at, old, patched, want)
                            runs += 1
                            log_runs += key in (2000, 2001)
    print(f'{runs} runs: stock matches the model; patched = stock(+2) x (S+2)/4; Flat/Log unchanged ({log_runs} runs)')
    at = dict(cls=1, key=11, amount=37, factor=256, alt=False, sel=0)
    print('COLOR, class 1, ISO amount 37:  S  stock  patched')
    for s in range(-2, 3):
        print(f'                                {s:+d}  {run(stock, s=s, **at):5d}  {run(new, s=s, **at):7d}')


if __name__ == '__main__':
    main()
