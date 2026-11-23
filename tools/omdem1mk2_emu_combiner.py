#!/usr/bin/env python3
"""Run the E-M1 Mark II combiner dispatcher (Soft Focus combiners 11 / 12) in the MN103 emulator.

    python3 tools/omdem1mk2_emu_combiner.py [releases/em1mk2/<VERSION>/edits.json]

The dispatcher 0x603dcd0c inits the bank at (ctx+8)+7364, asks the selector 0x603f1653 for a combiner id and jumps
through table 0x6053e108. For a kind-3 request the selector reads the effect code at request+656: 0x0402 -> 11,
0x0403 -> 12 (as on the E-P7). Combiners 11 / 12 write constant weights (no weight getter on this body):
  11: +92 = 600|600<<16, +96 = 600, +136 = 424|424<<16, +140 = 424;  12: the same with A and B swapped.
Checks:
  1. stock (and the given release) select 11 / 12 and write exactly those banks;
  2. the halation neutral-blend design (docs/OMD-EM1-II/HALATION.md): with table words 0x6053e164 / 0x6053e16c
     repointed to the prototype stubs in tools/emu_fixtures/em1_combiner_neutral.s, gate off gives the stock bank byte
     for byte, gate on gives w = 1024 (11: A = 1024, B = 0; 12: A = 0, B = 1024) and every other bank byte unchanged;
  3. other effects (0x0200 -> 9, 0x0300 -> 10) are untouched by the repointed words.
A release with the halation patch already has the table words on hl_c11 / hl_c12: the zeroed bytes below the request
(the job; its marker job+35 = request - 11329 is 0) make it an unmarked job, which must give the stock banks in 1; the
prototype stubs of 2 / 3 then do not apply, and marked jobs are checked by tools/omdem1mk2_emu_halation_route.py (C).
"""
import argparse
import struct

import omdem1mk2_emu_sdload as SD
import omdem1mk2_emu_validator as V
from penf_emulator import Region, execute

DISPATCH, SELECTOR = 0x603DCD0C, 0x603F1653
TABLE_WORD = {11: 0x6053E164, 12: 0x6053E16C}
STOCK_HANDLER = {11: 0x603DD06F, 12: 0x603DD0B8}
CALLER, STACK, CTX, REQUEST, BASE = 0x18020000, 0x18010000, 0x18030000, 0x18040000, 0x18100000
STUBS, GATE = 0x18060000, 0x18070000
BANK = 7364
WEIGHTS = (92, 96, 136, 140)


def word(a, b):
    return a | a << 16, a, b | b << 16, b


STOCK_WEIGHTS = {0x402: word(600, 424), 0x403: word(424, 600)}
NEUTRAL_WEIGHTS = {0x402: word(1024, 0), 0x403: word(0, 1024)}


def dispatch(img, effect, stub_code=None, gate=0, entry=DISPATCH, mask=0xF0, frame=20):
    ctx = bytearray(0x100)
    struct.pack_into('<II', ctx, 4, REQUEST, BASE)
    request = bytearray(0x800)
    request[16] = 3
    struct.pack_into('<H', request, 656, effect)
    code = b'\xdd' + struct.pack('<i', entry - CALLER) + bytes([mask, frame]) + b'\xcb'
    regions = [Region('caller', CALLER, code, 'rx'), *V.main_regions(img), Region('stack', STACK, bytes(0x1000), 'rw'),
               Region('ctx', CTX, bytes(ctx), 'r'), Region('request', REQUEST, bytes(request), 'r'),
               Region('job', REQUEST - 0x3000, bytes(0x3000), 'r'),
               Region('bank', BASE, bytes(0x2000), 'rw', capture=True), Region('gate', GATE, struct.pack('<I', gate), 'r')]
    if stub_code:
        regions.append(Region('stubs', STUBS, stub_code, 'rx'))
    r = execute(regions, {'pc': CALLER, 'sp': STACK + 0xF00, 'a0': CTX, 'a2': 0x5A5A5A5A, 'a3': 0x3C3C3C3C}, CALLER + 7,
                limit=20000)
    if r['fault'] or r['registers']['pc'] != CALLER + 7:
        raise SystemExit(f'effect {effect:#x}: stopped at {r["registers"]["pc"]:#x}: {r["fault"]}')
    regs = r['registers']
    assert (regs['sp'], regs['a2'], regs['a3']) == (STACK + 0xF00, 0x5A5A5A5A, 0x3C3C3C3C), regs
    return regs['d0'], bytes.fromhex(r['memory'][0]['hex'])[BANK:BANK + 0x100]


def weights(bank):
    return tuple(struct.unpack_from('<I', bank, o)[0] for o in WEIGHTS)


def selector(img, effect):
    return dispatch(img, effect, entry=SELECTOR, mask=0xA0, frame=12)[0] & 0xFF


def with_stubs(img, syms):
    m = bytearray(img)
    for cid, name in ((11, 'stub11'), (12, 'stub12')):
        a = TABLE_WORD[cid] - V.B
        assert struct.unpack_from('<I', m, a)[0] == STOCK_HANDLER[cid], hex(TABLE_WORD[cid])
        struct.pack_into('<I', m, a, syms[name])
    return bytes(m)


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('spec', nargs='?')
    a = p.parse_args()
    for label, img in (('stock', V.image(None)), *((('patched', V.image(a.spec)),) if a.spec else ())):
        stock_banks = {}
        for effect, cid in ((0x402, 11), (0x403, 12)):
            assert selector(img, effect) == cid, (label, effect)
            _, bank = dispatch(img, effect)
            assert weights(bank) == STOCK_WEIGHTS[effect], (label, effect, [hex(w) for w in weights(bank)])
            stock_banks[effect] = bank
        print(f'{label}: effect 0x402 -> combiner 11 (600/424), 0x403 -> combiner 12 (424/600)')
        if any(struct.unpack_from('<I', img, TABLE_WORD[c] - V.B)[0] != STOCK_HANDLER[c] for c in (11, 12)):
            print(f'{label}: table words on the halation hooks; unmarked job = stock banks (marked: emu_halation_route C)')
            continue

        code, syms = SD.assemble_fixture(SD.ROOT / 'tools/emu_fixtures/em1_combiner_neutral.s', STUBS, GATE=GATE,
                                         BANK_INIT=0x603DCA05, C11=STOCK_HANDLER[11], C12=STOCK_HANDLER[12],
                                         TAIL=0x603DD518)
        hooked = with_stubs(img, syms)
        for effect in (0x402, 0x403):
            _, off = dispatch(hooked, effect, code, gate=0)
            assert off == stock_banks[effect], (label, effect, 'gate off differs from stock')
            _, on = dispatch(hooked, effect, code, gate=1)
            assert weights(on) == NEUTRAL_WEIGHTS[effect], (label, effect, [hex(w) for w in weights(on)])
            rest = [o for o in range(0, 0x100, 4) if o not in WEIGHTS]
            assert all(on[o:o + 4] == stock_banks[effect][o:o + 4] for o in rest), (label, effect, 'other bank words')
        print(f'{label}: repointed table words -> gate off = stock bank, gate on = neutral w=1024, rest unchanged')
        for effect, cid in ((0x200, 9), (0x300, 10)):
            assert selector(img, effect) == cid
            assert dispatch(hooked, effect, code, gate=1)[1] == dispatch(img, effect)[1], (label, effect)
        print(f'{label}: effects 0x200 / 0x300 (combiners 9 / 10) unchanged with the stubs in place')
    print('RESULT PASS')


if __name__ == '__main__':
    main()
