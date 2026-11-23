#!/usr/bin/env python3
"""E-M1 Mark II: Sharpness as a linear scale (-2 off, -1 25 %, 0 50 %, +1 75 %, +2 100 % = stock +2).

    python3 patches/omdem1mk2/sharp_scale/build.py   -> edits.json  (needs the MN10300 binutils)

Sites in the ISP sharpening-gain helper (docs/PORT_EM1MK2.md "Sharpness scale"):
  0x603e8bfa  `movbu (1795,a0),d1; extb d1` (Sharpness into the table index) -> jmp ss_index
  0x603e8c83  `mov (40,sp),a0; movbu (50,sp),d0` (after the final gain cap)  -> jmp ss_scale
Code: ss.s in the section-3 FF tail after the aspect AF/AE stubs (aspect/build.py AF_AT..AF_END).
Flat / Log jobs (key 2000 / 2001) are left stock. Settings, menus and EXIF keep the -2..+2 values.
"""
import json
import struct
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TC = Path('/home/hertzel/ep7fw-toolchains/mn10300/bin')
BIN = ROOT / 'em1mk2/extracted/00_0100_40560020.decoded.bin'
ASPECT = ROOT / 'patches/omdem1mk2/aspect/edits.json'
B = 0x60021020
CODE_AT, CODE_END = 0x605d2f94, 0x605d3000           # section 3 loaded end
INDEX_AT, INDEX_STOCK = 0x603e8bfa, bytes.fromhex('fa44030711')
SCALE_AT, SCALE_STOCK = 0x603e8c83, bytes.fromhex('5c28f8b832')
GAIN_TABLE, GAIN_STOCK = 0x6052a94c, bytes.fromhex('0000100040007000b8000001')


def assemble():
    syms = dict(INDEX_BACK=INDEX_AT + 5, SCALE_BACK=SCALE_AT + 5)
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        subprocess.run([str(TC / 'mn10300-elf-as'), str(HERE / 'ss.s'), '-o', str(t / 'o')], check=True)
        subprocess.run([str(TC / 'mn10300-elf-ld'), f'--section-start=.text={CODE_AT:#x}', '-e', '_start', str(t / 'o'),
                        '-o', str(t / 'e')] + [f'--defsym={k}={v:#x}' for k, v in syms.items()], check=True)
        subprocess.run([str(TC / 'mn10300-elf-objcopy'), '-O', 'binary', str(t / 'e'), str(t / 'b')], check=True)
        nm = subprocess.run([str(TC / 'mn10300-elf-nm'), str(t / 'e')], capture_output=True, text=True).stdout
        names = {p[2]: int(p[0], 16) for p in (line.split() for line in nm.splitlines()) if len(p) == 3}
        return (t / 'b').read_bytes(), names


def aspect_end():
    """Highest main-image byte the aspect patch writes in the section-3 tail."""
    ends = [int(e['addr'], 16) + len(e['new']) // 2 for e in json.loads(ASPECT.read_text())['edits']
            if e.get('kind', '0x100') == '0x100' and 0x605d2a6c <= int(e['addr'], 16) < CODE_END]
    return max(ends)


def build():
    d = BIN.read_bytes()
    for at, stock, what in ((INDEX_AT, INDEX_STOCK, 'Sharpness index load'), (SCALE_AT, SCALE_STOCK, 'gain store'),
                            (GAIN_TABLE, GAIN_STOCK, 'gain table')):
        assert d[at - B:at + len(stock) - B] == stock, f'{what} at {at:#x} differs from 3.70 stock'
    code, syms = assemble()
    assert aspect_end() <= CODE_AT, f'aspect stubs reach {aspect_end():#x}, past {CODE_AT:#x}'
    assert CODE_AT + len(code) <= CODE_END, f'ss stubs {len(code)} B do not fit before {CODE_END:#x}'
    assert d[CODE_AT - B:CODE_AT + len(code) - B] == b'\xff' * len(code), 'code area not 0xFF'
    jmp = lambda at, to: b'\xdc' + struct.pack('<i', to - at)
    e = lambda a, old, new, why: dict(kind='0x100', addr=f'{a:#x}', expect=old.hex(), new=new.hex(), why=why)
    edits = [
        e(CODE_AT, d[CODE_AT - B:CODE_AT + len(code) - B], code,
          f'sharpness scale stubs ss_index / ss_scale ({len(code)} B, section 3 tail)'),
        e(INDEX_AT, INDEX_STOCK, jmp(INDEX_AT, syms['ss_index']),
          'sharpness gain helper: table index from Sharpness +2 (Flat/Log keep their own) -> jmp ss_index'),
        e(SCALE_AT, SCALE_STOCK, jmp(SCALE_AT, syms['ss_scale']),
          'sharpness gain helper: final gain x (Sharpness + 2) / 4 (Flat/Log stock) -> jmp ss_scale'),
    ]
    (HERE / 'edits.json').write_text(json.dumps({'patch': 'sharp_scale', 'components': ['0x100'], 'edits': edits},
                                                indent=1) + '\n', encoding='utf-8', newline='\n')
    print(f'sharp_scale: {len(code)} B at {CODE_AT:#x} (ss_index {syms["ss_index"]:#x}, ss_scale {syms["ss_scale"]:#x})')


if __name__ == '__main__':
    build()
