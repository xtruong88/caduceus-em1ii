#!/usr/bin/env python3
"""Build the E-M1 Mark II look WB patch (wb.s; docs/OMD-EM1-II/ARCHITECTURE_AND_MEMORY_MAP.md §7.8).

    python3 patches/omdem1mk2/look_wb/build.py                -> edits.json, linked against the default sd_loader
    EM1_LOOKMEM=1 python3 patches/omdem1mk2/look_wb/build.py  -> edits.json, linked against the look memory sd_loader

Edits:
  1. wb.s at 0x612f1000, in the 100 KB gap after look memory's .lmem. The gap is only loaded when the halation
     edits move Section 6's loaded end to 0x61300000, so this patch needs them (tools/omdem1mk2_check_loaded.py
     refuses a spec without them).
  2. The rel32 of the 14 getter calls that read the WB fine-tune for the image pipeline (capture block and compact
     slot) -> wb_get. The RAW-development pair 0x60cc3803 / 0x60cc3817 stays stock.
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
CODE_AT, GAP_END = 0x612F1000, 0x61300000
GETTER, BUILTIN = 0x6005E6CF, 0x60BC8150
KEY_A, KEY_G = 0x84F9, 0x9679
# (site, key, a0): the call `dd <rel32> c0 0c` at site; key loaded into d0 just before; `mov 0,a0` (90 00) at a0 with
# no a0 write between it and the call (objdump, §7.8). wb_pass sets a0 = 0 again, so the stock path stays stock only
# because every site already passes 0.
SITES = (
    (0x6033A209, KEY_A, 0x6033A206), (0x6033A223, KEY_G, 0x6033A221),   # capture: preset
    (0x6033A366, KEY_A, 0x6033A35C), (0x6033A37B, KEY_G, 0x6033A377),   # capture: preset 13 (Flash), index 15
    (0x6033A3F8, KEY_A, 0x6033A3F5), (0x6033A40E, KEY_G, 0x6033A40C),   # capture: one-touch
    (0x6033A475, KEY_A, 0x6033A472), (0x6033A48B, KEY_G, 0x6033A489),   # capture: CWB (wb_get keeps it stock)
    (0x6033A505, KEY_A, 0x6033A502), (0x6033A51D, KEY_G, 0x6033A50E),   # capture: category 4
    (0x6033A571, KEY_A, 0x6033A56D), (0x6033A58A, KEY_G, 0x6033A57A),   # capture: other (Auto), index 1
    (0x60343734, KEY_A, 0x60343731), (0x60343747, KEY_G, 0x60343744),   # compact slot
)
RAW_SITES = (0x60CC3803, 0x60CC3817)


def p_get(lookmem):
    """sd_loader's p_get in the build this patch ships with (the look memory build moves it)."""
    name = 'exports_lookmem.json' if lookmem else 'exports.json'
    return int(json.loads((HERE.parent / 'sd_loader' / name).read_text())['p_get'], 16)


def call_to(d, site):
    """Target of the 7-byte `call <rel32>,[d2,d3],12` at site (asserts the instruction shape)."""
    insn = d[site - B:site - B + 7]
    assert insn[0] == 0xDD and insn[5:] == b'\xc0\x0c', f'not call ..,[d2,d3],12 at {site:#x}'
    return (site + struct.unpack('<i', insn[1:5])[0]) & 0xFFFFFFFF


def assemble(lookmem):
    syms_in = dict(em1_getter=GETTER, p_get=p_get(lookmem), builtin_looks=BUILTIN)
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        subprocess.run([str(TC / 'mn10300-elf-as'), '-I', str(HERE.parent), str(HERE / 'wb.s'), '-o', str(t / 'o')],
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
    for site, key, a0 in SITES:
        assert call_to(d, site) == GETTER, f'{site:#x} does not call the getter'
        # `mov key,d0` (fc cc imm32) within the 12 bytes before the call
        assert b'\xfc\xcc' + struct.pack('<I', key) in d[site - B - 12:site - B], f'key {key:#x} not loaded before {site:#x}'
        assert d[a0 - B:a0 - B + 2] == b'\x90\x00' and site - a0 <= 16, f'no mov 0,a0 at {a0:#x} for {site:#x}'
    for site in RAW_SITES:
        assert call_to(d, site) == GETTER, f'RAW site {site:#x} changed'
    code, syms = assemble(lookmem)
    assert d[CODE_AT - B:CODE_AT + len(code) - B] == b'\xff' * len(code), 'code area not 0xFF'
    assert CODE_AT + len(code) <= GAP_END, 'code runs past the gap'
    e = lambda a, old, new, why: dict(kind='0x100', addr=f'{a:#x}', expect=old.hex(), new=new.hex(), why=why)
    edits = [e(CODE_AT, d[CODE_AT - B:CODE_AT + len(code) - B], code,
               f'look WB: wb_get ({len(code)} B, p_get {p_get(lookmem):#x})')]
    for site, key, _ in SITES:
        old = d[site + 1 - B:site + 5 - B]
        new = struct.pack('<i', syms['wb_get'] - site)
        edits.append(e(site + 1, old, new, f'look WB: {"A-B" if key == KEY_A else "G-M"} read at {site:#x} -> wb_get'))
    spec = {'patch': 'look_wb', 'lookmem': lookmem, 'edits': edits}
    return spec, syms, len(code)


def build():
    lookmem = os.environ.get('EM1_LOOKMEM') == '1'
    spec, syms, size = make_edits(lookmem)
    (HERE / 'edits.json').write_text(json.dumps(spec, indent=1) + '\n')
    print(f'look_wb: {size} B at {CODE_AT:#x} (wb_get {syms["wb_get"]:#x}), {len(SITES)} sites, '
          f'{"look memory" if lookmem else "default"} sd_loader')


if __name__ == '__main__':
    build()
