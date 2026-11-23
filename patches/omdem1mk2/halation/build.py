#!/usr/bin/env python3
"""Build the E-M1 Mark II Soft Focus flag gate (docs/OMD-EM1-II/HALATION.md).

    python3 patches/omdem1mk2/halation/build.py               -> edits.json (stage from sid 961)
    EM1_HL_FORCE_STAGE=1 python3 patches/omdem1mk2/halation/build.py   -> test build: stage fixed at 1..3

Edits:
  1. Section 6 loaded end 0x612e7000 -> 0x61300000 (end-getter stub word 0x60042b6d), so the loader copies the 100 KB
     gap 0x612e7000..0x61300000 from the package: the same edit as the camera-tested space probe sp1 (S+).
  2. hl_flag.s at 0x612e7000 (the gap, 0xFF in the catalog stock).
  3. Hook: the first 7 bytes of the flag converter 0x6042285e (`mov (28,a0),a3; mov a1,a2; mov 24951,a1`, all
     absolute, no branch lands inside) -> `jmp hl_entry; nop; nop`; hl_flag replays them and returns to 0x60422865.
  4. Hardware watchdog timeout 10 s -> 30 s at its two run-time settings (as E-P7 v0.31b): `mov 10,d0` at 0x600792c4
     (SYS_WDT on, before the setter wrapper 0x60079282) and at 0x6005aecc (restore after a flash operation, before the
     setter 0x600226fd). The setter writes the 6-bit seconds field of 0x98e0008c (max 63). The deliberate settings
     (0 / 1, and the 10 before the `bra .` at 0x600cdfb5) stay stock.
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
END_IMM, OLD_END, NEW_END = 0x60042B6D, 0x612E7000, 0x61300000
HALO_PAGE_AT = 0x612F0000              # color_creator_wheel's Halo page, the next block in the gap
CODE_AT = OLD_END
HOOK, HOOK_STOCK, BACK = 0x6042285E, bytes.fromhex('f82c1c96257761'), 0x60422865
GETTER, STAGE_KEY = 0x6005E6CF, 0xF709
# step 4: route, pass, neutral blend (docs/OMD-EM1-II/HALATION.md "Step 4")
ROUTE_CALL, ROUTE_STOCK = 0x603900EC, bytes.fromhex('dd843b01000004')       # call 0x603a3c70,[],4 (a0 = job)
BLUR_WORD, BLUR = 0x60393A54, 0x60398E6F                                     # mov 0x60398e6f,d1 at 0x60393a52
C11_WORD, C11, C12_WORD, C12 = 0x6053E164, 0x603DD06F, 0x6053E16C, 0x603DD0B8
WDT_SITES, WDT_STOCK, WDT_SECONDS = (0x600792C4, 0x6005AECC), bytes.fromhex('800a'), 30   # mov 10,d0 -> mov 30,d0
SYMS = dict(GETTER=GETTER, STAGE_KEY=STAGE_KEY, BACK=BACK, PLAIN_BUILDER=0x603A3C70, ART_BUILDER=0x60391C1C,
            BUFIDX=0x6038C01C, BLUR=BLUR, C11=C11, C12=C12, TAIL=0x603DD518, BANK_INIT=0x603DCA05,
            LOCK=0x6006E9D0, UNLOCK=0x6006EA19, FLUSH=0x60068709, MAPPER=0x6006888F, MODEGET=0x60068B78,
            MODESET=0x60068B88, MALLOC=0x600231FE, FREE=0x6002323D,
            # look tint (step 4e): sd_loader's p_get and color_creator_wheel's built-in look table
            P_GET=int(json.loads((HERE.parent / 'sd_loader/exports.json').read_text())['p_get'], 16),
            BUILTIN=0x60BC8150)


def env_int(name, lo, hi):
    value = int(os.environ.get(name, '0'))
    if not lo <= value <= hi:
        raise SystemExit(f'{name} must be {lo}..{hi}')
    return value


def force_stage():
    return env_int('EM1_HL_FORCE_STAGE', 0, 3)


def assemble(force, no_pass=0):
    """hl_flag + hl_route + hl_pass linked as one block at CODE_AT (hl_flag first: its hl_entry is the hook target)."""
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        objs = []
        for name in ('hl_flag', 'hl_route', 'hl_pass'):
            subprocess.run([str(TC / 'mn10300-elf-as'), f'--defsym=FORCE_STAGE={force}', f'--defsym=NO_PASS={no_pass}',
                            str(HERE / f'{name}.s'), '-o', str(t / f'{name}.o')], check=True)
            objs.append(str(t / f'{name}.o'))
        subprocess.run([str(TC / 'mn10300-elf-ld'), f'--section-start=.text={CODE_AT:#x}', '-e', '_start', *objs,
                        '-o', str(t / 'e')] + [f'--defsym={k}={v:#x}' for k, v in SYMS.items()], check=True)
        subprocess.run([str(TC / 'mn10300-elf-objcopy'), '-O', 'binary', str(t / 'e'), str(t / 'b')], check=True)
        nm = subprocess.run([str(TC / 'mn10300-elf-nm'), str(t / 'e')], capture_output=True, text=True).stdout
        syms = {p[2]: int(p[0], 16) for p in (line.split() for line in nm.splitlines()) if len(p) == 3}
        return (t / 'b').read_bytes(), syms


def make_edits(force, no_pass):
    """-> (spec dict, symbols, code size) for the given stage override and pass switch; writes nothing."""
    d = BIN.read_bytes()
    assert d[END_IMM - 2 - B:END_IMM + 4 - B] == b'\xfc\xcc' + struct.pack('<I', OLD_END), 'end-word stub changed'
    assert d[HOOK - B:HOOK + 7 - B] == HOOK_STOCK, 'converter entry changed'
    for addr, stock in ((ROUTE_CALL, ROUTE_STOCK), (BLUR_WORD, struct.pack('<I', BLUR)),
                        (C11_WORD, struct.pack('<I', C11)), (C12_WORD, struct.pack('<I', C12))):
        assert d[addr - B:addr - B + len(stock)] == stock, f'stock bytes changed at {addr:#x}'
    for addr in WDT_SITES:
        assert d[addr - B:addr - B + 2] == WDT_STOCK, f'watchdog site changed at {addr:#x}'
    code, syms = assemble(force, no_pass)
    assert d[CODE_AT - B:CODE_AT + len(code) - B] == b'\xff' * len(code), 'code area not 0xFF'
    assert CODE_AT + len(code) <= HALO_PAGE_AT, 'code runs into the Color Creator Halo page'
    jump = b'\xdc' + struct.pack('<i', syms['hl_entry'] - HOOK) + b'\xcb\xcb'
    route = b'\xdd' + struct.pack('<i', syms['hl_route'] - ROUTE_CALL) + b'\x00\x04'      # regs none, frame 4
    assert len(route) == len(ROUTE_STOCK)
    e = lambda a, old, new, why: dict(kind='0x100', addr=f'{a:#x}', expect=old.hex(), new=new.hex(), why=why)
    stage = f'stage fixed at {force} (TEST BUILD)' if force else 'stage from sid 961'
    word = lambda a, v, why: e(a, d[a - B:a - B + 4], struct.pack('<I', v), why)
    edits = [
        e(END_IMM, d[END_IMM - B:END_IMM + 4 - B], struct.pack('<I', NEW_END),
          'halation: section 6 loaded end 0x612e7000 -> 0x61300000 (as space probe sp1)'),
        e(CODE_AT, d[CODE_AT - B:CODE_AT + len(code) - B], code,
          f'halation: hl_flag + hl_route + hl_pass ({len(code)} B, {stage}{", NO PASS" if no_pass else ""})'),
        e(HOOK, HOOK_STOCK, jump, 'halation: flag converter entry -> hl_flag (jmp; nop; nop)'),
        e(ROUTE_CALL, ROUTE_STOCK, route, 'halation: colour-builder call -> hl_route (marked jobs take the Art builder)'),
        word(BLUR_WORD, syms['hl_ob'], 'halation: Soft Focus blur work-list word -> hl_ob (pass on record 0x1000)'),
        word(C11_WORD, syms['hl_c11'], 'halation: combiner 11 -> hl_c11 (neutral blend for marked jobs)'),
        word(C12_WORD, syms['hl_c12'], 'halation: combiner 12 -> hl_c12 (neutral blend for marked jobs)'),
    ] + [e(a, WDT_STOCK, bytes([0x80, WDT_SECONDS]), f'halation: watchdog timeout 10 -> {WDT_SECONDS} s '
           f'({"SYS_WDT on" if a == WDT_SITES[0] else "restore after a flash operation"})') for a in WDT_SITES]
    spec = {'patch': 'halation', 'force_stage': force, 'no_pass': no_pass, 'edits': edits}
    return spec, syms, len(code)


def build():
    force, no_pass = force_stage(), env_int('EM1_HL_NO_PASS', 0, 1)
    spec, syms, size = make_edits(force, no_pass)
    stage = f'stage fixed at {force} (TEST BUILD)' if force else 'stage from sid 961'
    (HERE / 'edits.json').write_text(json.dumps(spec, indent=1) + '\n')
    print(f'halation: {size} B at {CODE_AT:#x} (hl_route {syms["hl_route"]:#x}, hl_ob {syms["hl_ob"]:#x}, '
          f'hl_pass {syms["hl_pass"]:#x}), {stage}{", no pass" if no_pass else ""}')


if __name__ == '__main__':
    build()
