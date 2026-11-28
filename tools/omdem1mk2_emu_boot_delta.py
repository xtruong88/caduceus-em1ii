#!/usr/bin/env python3
"""E-M1 Mark II: what a release changes on the boot path, stock and patched side by side in the MN103 emulator.

    python3 tools/omdem1mk2_emu_boot_delta.py SPEC [SPEC ...]

Each SPEC is a release edits.json built on the OM catalog 3.70 image (em1mk2/extracted). For stock and each spec:

1. Startup copies [emulated]: the C startup block 0x6002116f..0x6002127b runs with the copy routine 0x6002249f
   replaced by its own `ret`; every call's (source, destination, length) is read from the trace. These are the
   .data / resident ranges the camera copies from the image before any task runs.
2. Section loads [emulated]: the loader 0x60042b96 runs for sections 1..9 up to its flash request (0x60042bce,
   the call to 0x6005ae5b); (destination, source, length, type) are read from the registers.
3. Watchdog [emulated]: SYS_WDT on (0x600792bc) and the restore after a flash operation (0x6005aecc), through the
   setter to the hardware handshake, via tools/omdem1mk2_emu_watchdog.py's runner: the 6-bit timeout written.
4. Classification [static]: every byte the spec changes is placed in a startup copy, a loaded section, or nowhere
   (never reaches RAM); destinations of all loads and copies are checked for overlaps.
5. Pointer scan [static]: aligned 32-bit words in all boot-initialised data/code (cached, uncached, 0x8 alias) that
   point into the RAM the spec newly loads; any hit means stock code may use that RAM for something else.

Read-only. Needs the built engine (external/oly_fw_analysis/toolchains/mn103-gnu-build/penf-mn103).
"""
import json
import struct
import sys

import omdem1mk2_emu_validator as V
import omdem1mk2_emu_watchdog as W
from omdem1mk2_layout import BASE as B
from penf_emulator import Region, execute

STARTUP, STARTUP_END, COPY = 0x6002116F, 0x6002127B, 0x6002249F
LOADER, LOADER_REQ = 0x60042B96, 0x60042BCE
STACK = 0x9F000000
SP = STACK + 0x1000
BOOTVARS = 0x621BE000                       # 0x621beec0..d0: the startup block's copy-end words


def ram(addr):
    """Cached RAM address for a cached / uncached / 0x8 alias (0x6..., 0xa..., 0x8...)."""
    return {0x6: addr, 0xA: addr - 0x40000000, 0x8: addr - 0x20000000}.get(addr >> 28, addr)


def image_addr(flash):
    """Main image address of a flash source (component 0x100 sits at flash 0x40560020, linear)."""
    return flash - 0x40560020 + B


def startup_copies(img):
    base_end = V.loaded_sections(img)[0][1]
    code = bytearray(img[:base_end - B])
    code[COPY - B:COPY - B + 3] = b'\xdf\xf0\x20'            # ret [d2,d3,a2,a3],32
    r = execute([Region('base', B, bytes(code), 'rx'),
                 Region('vars', BOOTVARS, bytes(0x1000), 'rw'),
                 Region('stack', STACK, bytes(0x2000), 'rw')],
                {'pc': STARTUP, 'sp': SP}, STARTUP_END, limit=1000, trace_limit=1000)
    assert not r['fault'] and r['registers']['pc'] == STARTUP_END, (r['status'], r['fault'])
    copies = []
    for t in r['trace']:
        if t['pc'] == COPY:
            src = t['a0'] if t['a0'] >> 28 == 6 else image_addr(t['a0'])
            copies.append((src, ram(t['a1']), t['d1']))
    return copies


def section_loads(img):
    loads = []
    for n in range(1, 10):
        r = execute((*V.main_regions(img), Region('stack', STACK, bytes(0x2000), 'rw')),
                    {'pc': LOADER, 'sp': SP, 'd0': n}, 0xFFFFFFF0, limit=1000, breakpoints=[LOADER_REQ])
        assert r['status'] == 'breakpoint' and not r['fault'], (n, r['fault'])
        g = r['registers']
        loads.append((n, ram(g['a0']), g['a1'], g['d0'], g['d1']))
    return loads


def watchdog(img):
    return tuple(W.run(img, entry, via_call)[0] & 0x3F
                 for entry, via_call in ((W.WDT_ON, True), (W.FLASH_RESTORE, False)))


def spans(ranges):
    return sorted((s, s + n) for s, n in ranges if n)


def overlaps(ranges):
    r = spans(ranges)
    return [(a, b) for a, b in zip(r, r[1:]) if a[1] > b[0]]


def pointer_hits(img, regions, lo, hi):
    hits = []
    for s, e in regions:
        data = img[s - B:e - B]
        for off in range(0, len(data) - 3, 4):
            v = struct.unpack_from('<I', data, off)[0]
            if lo <= ram(v) < hi:
                hits.append((s + off, v))
    return hits


def main():
    stock = V.image(None)
    s_copies, s_loads, s_wdt = startup_copies(stock), section_loads(stock), watchdog(stock)
    print('stock startup copies (image source -> RAM, length):')
    for src, dst, n in s_copies:
        print(f'  {src:#010x} -> {dst:#010x}  {n:#x}')
    print('stock section loads (n: RAM dest, flash source, length, type):')
    for n, dst, src, ln, kind in s_loads:
        print(f'  S{n}: {dst:#010x}  {src:#010x}  {ln:#x}  {kind:#x}')
    print(f'stock watchdog timeouts (SYS_WDT on, after flash op): {s_wdt}')
    sources = [(src, src + n) for src, _, n in s_copies]
    for spec in sys.argv[1:]:
        img = V.image(spec)
        name = json.load(open(spec)).get('version', spec)
        copies, loads, wdt = startup_copies(img), section_loads(img), watchdog(img)
        print(f'\n== {name}')
        print('  startup copies: ' + ('identical to stock' if copies == s_copies else f'DIFFER {copies}'))
        new_ram = []
        for (n, d0, s0, l0, k0), (_, d1, s1, l1, k1) in zip(s_loads, loads):
            if (d0, s0, l0, k0) != (d1, s1, l1, k1):
                assert (d0, s0, k0) == (d1, s1, k1) and l1 > l0, (n, d1, s1, l1, k1)
                new_ram.append((d0 + l0, d1 + l1))
                print(f'  S{n}: length {l0:#x} -> {l1:#x}, newly loaded RAM {d0 + l0:#x}..{d1 + l1:#x}')
        dests = [(d, ln) for _, d, _, ln, _ in loads] + [(d, n) for _, d, n in copies]
        bad = overlaps(dests)
        print('  load/copy destinations overlap: ' + (', '.join(f'{a}/{b}' for a, b in bad) if bad else 'none'))
        print(f'  watchdog timeouts: {s_wdt} -> {wdt}')
        changed = [a + B for a in range(len(img)) if img[a] != stock[a]]
        loaded = [(d, d + ln) for _, d, _, ln, _ in loads] + [V.loaded_sections(img)[0]]
        where = {}
        for a in changed:
            tag = next((f'startup copy {s:#x}' for s, e in sources if s <= a < e), None)
            tag = tag or next((f'loaded {s:#x}..{e:#x}' for s, e in loaded if s <= a < e), 'NOT LOADED')
            where[tag] = where.get(tag, 0) + 1
        for tag, count in sorted(where.items()):
            print(f'  changed bytes in {tag}: {count}')
        boot_data = sources + [(s, e) for s, e in V.loaded_sections(stock)]
        for lo, hi in new_ram:
            hits = pointer_hits(stock, boot_data, lo, hi)
            print(f'  stock aligned words pointing into {lo:#x}..{hi:#x}: {len(hits)}'
                  + ''.join(f'\n    {at:#010x}: {v:#010x}' for at, v in hits[:12]))
    print('\nRESULT DONE')


if __name__ == '__main__':
    main()
