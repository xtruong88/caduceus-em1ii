#!/usr/bin/env python3
"""Build the E-M1 Mark II colour-wheel value feed (cw.s; plans/261127-1641-em1ii-color-wheel phase 02).

    python3 patches/omdem1mk2/color_wheel/build.py                -> edits.json, linked against the default sd_loader
    EM1_LOOKMEM=1 python3 patches/omdem1mk2/color_wheel/build.py  -> edits.json, linked against the look memory sd_loader

Opt-in fragment: no existing build reads color_wheel/edits.json, so default builds stay byte-identical. It needs the
halation edits (Section 6 loaded end -> 0x61300000), like look_wb (tools/omdem1mk2_check_loaded.py refuses otherwise).

Edits:
  1. cw.s at 0x612f1800, in the 100 KB gap after look memory (.lmem 0x612f0800) and look WB (0x612f1000), before
     0x61300000.
  2. The rel32 of the 38 setting-getter calls (`call 0x602da802,[],4`) of the wheel producer 0x6097a1b5's kind-5 path
     -> cw_get. The other getter calls of the producer (617/618 Color Creator, 663..665, 971, 985..995) stay stock.
"""
import json
import os
import struct
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TC = Path('/home/hertzel/ep7fw-toolchains/mn10300/bin')
BIN = ROOT / 'em1mk2/extracted/00_0100_40560020.decoded.bin'
B = 0x60021020
CODE_AT, GAP_END = 0x612F1800, 0x61300000
SET_GET = 0x602DA802
PRODUCER = (0x6097A1B5, 0x6097A573)
# (call site, setting id loaded by the `mov imm16,d0` (2c lo hi) right before it). 0x6097a44b also serves 948 / 960
# (`mov 948,d0; jmp 0x6097a44b` at 0x6097a2fe, `mov 960,d0; jmp` at 0x6097a3a3).
SITES = ((0x6097A22D, 906), (0x6097A262, 1094), (0x6097A307, 1095), (0x6097A3AC, 1089)) + tuple(
    (0x6097A272 + 13 * k, 937 + k) for k in range(11)) + tuple(
    (0x6097A317 + 13 * k, 949 + k) for k in range(11)) + tuple(
    (0x6097A3BC + 13 * k, 925 + k) for k in range(12))
SHARED_TAIL = ((0x6097A2FE, 948), (0x6097A3A3, 960))     # mov id,d0 (2c) then jmp 0x6097a44b (cc rel16)


def p_get(lookmem):
    name = 'exports_lookmem.json' if lookmem else 'exports.json'
    return int(json.loads((HERE.parent / 'sd_loader' / name).read_text())['p_get'], 16)


def call_to(d, site):
    """Target of the 7-byte `call <rel32>,[],4` at site (asserts the instruction shape)."""
    insn = d[site - B:site - B + 7]
    assert insn[0] == 0xDD and insn[5:] == b'\x00\x04', f'not call ..,[],4 at {site:#x}'
    return (site + struct.unpack('<i', insn[1:5])[0]) & 0xFFFFFFFF


def gap_end_of(path, addr):
    """End of the edit at addr in another patch's edits fragment (0 if absent)."""
    if not path.exists():
        return 0
    for e in json.loads(path.read_text())['edits']:
        if int(e['addr'], 16) == addr:
            return addr + len(e['new']) // 2
    return 0


def assemble(lookmem):
    syms_in = dict(em1_set_get=SET_GET, p_get=p_get(lookmem))
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        subprocess.run([str(TC / 'mn10300-elf-as'), '-I', str(HERE.parent), str(HERE / 'cw.s'), '-o', str(t / 'o')],
                       check=True)
        subprocess.run([str(TC / 'mn10300-elf-ld'), f'--section-start=.text={CODE_AT:#x}', '-e', '_start',
                        str(t / 'o'), '-o', str(t / 'e')] + [f'--defsym={k}={v:#x}' for k, v in syms_in.items()],
                       check=True)
        subprocess.run([str(TC / 'mn10300-elf-objcopy'), '-O', 'binary', str(t / 'e'), str(t / 'b')], check=True)
        nm = subprocess.run([str(TC / 'mn10300-elf-nm'), str(t / 'e')], capture_output=True, text=True).stdout
        syms = {p[2]: int(p[0], 16) for p in (line.split() for line in nm.splitlines()) if len(p) == 3}
        return (t / 'b').read_bytes(), syms


def make_edits(lookmem=False):
    """-> (spec dict, symbols, code size); writes nothing."""
    d = BIN.read_bytes()
    assert len(SITES) == 38 and len({s for s, _ in SITES}) == 38
    for site, sid in SITES:
        assert PRODUCER[0] <= site < PRODUCER[1]
        assert call_to(d, site) == SET_GET, f'{site:#x} does not call the setting getter'
        assert d[site - 3 - B:site - B] == b'\x2c' + struct.pack('<H', sid), f'id {sid} not loaded before {site:#x}'
    for at, sid in SHARED_TAIL:
        assert d[at - B:at + 3 - B] == b'\x2c' + struct.pack('<H', sid), f'id {sid} not at {at:#x}'
        assert d[at + 3 - B] == 0xCC and (at + 3 + struct.unpack('<h', d[at + 4 - B:at + 6 - B])[0]) == 0x6097A44B
    code, syms = assemble(lookmem)
    # Gap neighbours: look memory (sd_loader EM1_LOOKMEM) and look WB end before us; 16-byte guards.
    lower = max(gap_end_of(HERE.parent / 'sd_loader' / 'edits_lookmem.json', 0x612F0800),
                gap_end_of(HERE.parent / 'look_wb' / 'edits.json', 0x612F1000))
    assert lower and lower + 16 <= CODE_AT, f'color wheel at {CODE_AT:#x} overlaps a gap neighbour ending {lower:#x}'
    assert CODE_AT + len(code) <= GAP_END - 16, 'code runs past the gap'
    assert d[CODE_AT - 16 - B:CODE_AT + len(code) + 16 - B] == b'\xff' * (len(code) + 32), 'code area not 0xFF'
    e = lambda a, old, new, why: dict(kind='0x100', addr=f'{a:#x}', expect=old.hex(), new=new.hex(), why=why)
    edits = [e(CODE_AT, d[CODE_AT - B:CODE_AT + len(code) - B], code,
               f'colour wheel: cw_get ({len(code)} B, p_get {p_get(lookmem):#x}); needs the halation gap load')]
    for site, sid in SITES:
        old = d[site + 1 - B:site + 5 - B]
        new = struct.pack('<i', syms['cw_get'] - site)
        edits.append(e(site + 1, old, new, f'colour wheel: producer read of setting {sid} at {site:#x} -> cw_get'))
    spec = {'patch': 'color_wheel', 'lookmem': lookmem, 'edits': edits}
    return spec, syms, len(code)


def build():
    lookmem = os.environ.get('EM1_LOOKMEM') == '1'
    spec, syms, size = make_edits(lookmem)
    (HERE / 'edits.json').write_text(json.dumps(spec, indent=1) + '\n')
    print(f'color_wheel: {size} B at {CODE_AT:#x} (cw_get {syms["cw_get"]:#x}), {len(SITES)} sites, '
          f'{"look memory" if lookmem else "default"} sd_loader')


if __name__ == '__main__':
    build()
