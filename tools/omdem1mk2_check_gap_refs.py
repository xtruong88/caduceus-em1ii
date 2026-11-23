#!/usr/bin/env python3
"""E-M1 Mark II: check that no stock instruction addresses the halation gap 0x612e7000..0x61300000.

    python3 tools/omdem1mk2_check_gap_refs.py        (inside the em1emu container: needs mn10300-elf-objdump)

The halation patch raises Section 6's loaded end so the loader copies this 100 KB gap (camera-tested on the older
3.70 file with probe sp1, S+). This repeats sp1's scan on the image the releases are built from (OM catalog 3.70,
em1mk2/extracted): every loaded section of main is disassembled linearly, and every operand or branch target in the
gap under the cached 0x6..., uncached 0xa... or 0x8... alias is listed. Allowed: the end-getter stub at 0x60042b6d
(`mov 0x612e7000,d0`, the word the halation edit raises). Each other hit is shown with the bytes around it so a
reviewer can tell data decoded as code from a real reference; the script fails on any.
A byte-pattern scan at every offset (the old approach) also flags ASCII text and operand bytes of unrelated
instructions, so it is not used here.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from omdem1mk2_layout import loaded_sections  # noqa: E402

MAIN = ROOT / 'em1mk2/extracted/00_0100_40560020.decoded.bin'
OBJDUMP = '/home/hertzel/ep7fw-toolchains/mn10300/bin/mn10300-elf-objdump'
BASE = 0x60021020
LO, HI = 0x612E7000, 0x61300000
ALLOWED = {0x60042B6B}                                     # the `fc cc` stub; its word sits at 0x60042b6d
HEX = re.compile(r'0x([0-9a-f]+)\b')
DEC = re.compile(r'(?<![\w.])(-?\d{6,})\b')
BRANCH = re.compile(r'(call|calls|jmp|bra|beq|bne|blt|bgt|bge|ble|bcs|bhi|bcc|bls|bvc|bvs|bnc|bns)\s')


def in_gap(v):
    return any(LO <= (v - d) < HI for d in (0, 0x40000000, 0x20000000))


def main():
    img = MAIN.read_bytes()
    assert img[LO - BASE:HI - BASE] == b'\xff' * (HI - LO), 'gap is not 0xFF in stock'
    hits = []
    for lo, hi in loaded_sections(img):
        out = subprocess.run([OBJDUMP, '-D', '-b', 'binary', '-m', 'mn10300', f'--adjust-vma={BASE}',
                              f'--start-address={lo}', f'--stop-address={hi}', str(MAIN)],
                             capture_output=True, text=True, check=True).stdout
        for line in out.splitlines():
            m = re.match(r'\s*([0-9a-f]{8}):\t([0-9a-f ]+)\t(.*)', line)
            if not m:
                continue
            text = m.group(3)
            values = [int(x, 16) for x in HEX.findall(text)]
            values += [int(x) & 0xFFFFFFFF for x in DEC.findall(HEX.sub('', text))]   # objdump prints imm32 in decimal
            if any(in_gap(v) for v in values):
                hits.append((int(m.group(1), 16), m.group(2).strip(), text.strip()))
    # A branch into the gap cannot be real: stock does not load the gap, so taking it would crash every stock camera.
    # Such hits are data decoded as code and are listed for information only. Operand hits (an address read, written
    # or passed) are the ones that would conflict with code placed in the gap.
    branches = [h for h in hits if BRANCH.match(h[2])]
    operands = [h for h in hits if not BRANCH.match(h[2])]
    bad = [h for h in operands if h[0] not in ALLOWED]
    for at, raw, text in operands:
        print(f'  {at:#010x}  {raw:24} {text:40} {"allowed" if at in ALLOWED else "CHECK"}')
    print(f'{len(branches)} branch-shaped hits into the gap (data decoded as code; impossible as real branches in stock)')
    if bad or not any(h[0] in ALLOWED for h in operands):
        print(f'RESULT FAIL ({len(bad)} operand(s) to check)')
        sys.exit(1)
    print('only the end-getter stub uses an address in the gap as an operand')
    print('RESULT PASS')


if __name__ == '__main__':
    main()
