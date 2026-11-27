#!/usr/bin/env python3
"""Run the halation step 4 route (patches/omdem1mk2/halation: hl_flag + hl_route + hl_pass) end to end in the emulator.

    python3 tools/omdem1mk2_emu_halation_route.py [SPEC] [--no-pass]

SPEC: a release edits.json that holds the stage-2 halation edits (default: v0.4c17 + those edits built here);
--no-pass: the EM1_HL_NO_PASS build, where hl_ob goes straight to the stock blur (B then checks that instead).

The patch is built with the stage fixed at 2 (as a test build would be) and applied on top of v0.4c17; jobs come from
the real capture entry 0x6041ec04 with the fixtures of tools/omdem1mk2_emu_work_list.py / _plain_route.py.
  A  route: Vivid, Natural and Color Creator stills get marker 0xA2 at job+35 and the Soft Focus Art list with the blur item
     replaced by hl_ob; Monotone (5) and the same modes with the stage off stay byte for byte stock;
  B  hl_ob on the Art list after development: a marked job reaches hl_pass with a0 = the record of 0x1000 and
     d0 = 0x12 (red, stage 2), then continues into the stock blur with the same submits, waits and job bytes as stock
     (hl_pass replaced by an empty fixture); an unmarked job never reaches hl_pass and equals stock;
  C  combiners: a marked job (request - 11329 = job+35) gets the neutral blend (11: A 1024 / B 0, 12: A 0 / B 1024) with
     every other bank word as stock; an unmarked job gets the stock 600 / 424.
hl_pass itself is checked against its model by tools/omdem1mk2_emu_halation_pass.py; the ISP and the camera's colour
result (combiner 13 during the Art development, docs/OMD-EM1-II/HALATION.md) are not emulated.
"""
import argparse
import importlib.util
import json
import struct
import tempfile

import omdem1mk2_emu_art_route as A
import omdem1mk2_emu_combiner as C
import omdem1mk2_emu_job_marker as M
import omdem1mk2_emu_plain_route as P
import omdem1mk2_emu_validator as V
import omdem1mk2_emu_work_list as W
from penf_emulator import Region, execute

STAGE = 2
MARK = 0xA0 | STAGE
BASE_SPEC = V.ROOT / 'releases/em1mk2/v0.4c17/edits.json'


def load_build():
    spec = importlib.util.spec_from_file_location('hl_build', V.ROOT / 'patches/omdem1mk2/halation/build.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def spec_files(spec=None, no_pass=0, setting=False):
    """(patched spec path, symbols): SPEC, or v0.4c17 + the halation edits with the stage fixed at 2 (or, with
    `setting`, read from sid 961)."""
    build = load_build()
    hl, syms, _ = build.make_edits(0 if setting else STAGE, no_pass)
    if spec:
        have = json.load(open(spec))['edits']
        missing = [e['addr'] for e in hl['edits'] if e not in have]
        if missing:   # a look memory spec: halation is linked against that sd_loader build's p_get
            hl, syms, _ = build.make_edits(0 if setting else STAGE, no_pass, True)
            missing = [e['addr'] for e in hl['edits'] if e not in have]
        assert not missing, f'{spec} lacks these halation edits (setting={setting}, no_pass={no_pass}): {missing}'
        return spec, syms
    base = json.load(open(BASE_SPEC))
    base['edits'] = hl['edits'] + base['edits']
    f = tempfile.NamedTemporaryFile('w', suffix='.json', delete=False)
    json.dump(base, f)
    f.close()
    return f.name, syms


def check_off(stock, patched, syms):
    """Halo Off (sid 961 = 0, the default after flashing): every capture job is the stock job byte for byte, except
    that a Soft Focus list (Art Filter) names hl_ob where stock names the blur; hl_ob on an unmarked job is the stock
    blur (check_ob / check_ob_no_pass). MONO (12) is left out: the capture fixture faults on it in stock too."""
    off = fix_stage(patched, syms, 0)
    ob, blur = struct.pack('<I', syms['hl_ob']), struct.pack('<I', A.REDUCE)
    cases = [(mode, 0x1000) for mode in (1, 2, 5, 10, 101)] + [(1, kind) for kind in (0x1001, 0x2001, 0x1008)]
    renamed = 0
    for mode, kind in cases:
        got, want = capture_job(off, mode, kind), capture_job(stock, mode, kind)
        assert got.keys() == want.keys()
        for name in got:
            if got[name] != want[name]:
                assert got[name].count(ob) == 1 and got[name].replace(ob, blur) == want[name], (mode, hex(kind), name)
                renamed += 1
    print(f'Off: stage 0 -> {len(cases)} capture jobs (Vivid, Natural, Monotone, Color Creator, Art Filter 101; kinds '
          f'0x1001 / 0x2001 / 0x1008) byte for byte stock, except hl_ob for the blur in {renamed} Soft Focus list(s)')


def fix_stage(img, syms, stage=STAGE):
    """A build that reads the stage from sid 961: replace hl_flag's own getter call (7 bytes, hl_stage_get) with
    `mov STAGE,d0` + nops. Only the patch's code changes; the sid-961 read itself is checked by emu_halation_flag."""
    m = bytearray(img)
    o = syms['hl_stage_get'] - V.B
    assert m[o] == 0xDD and m[o + 5:o + 7] == b'\xc0\x0c', m[o:o + 7].hex()
    m[o:o + 7] = bytes([0x80, stage]) + b'\xcb' * 5
    return bytes(m)


def capture_job(img, mode, kind=0x1000):
    """A.capture_job without the emulator-only route stubs: the image carries the real patch."""
    request = bytearray(0x2000)
    struct.pack_into('<I', request, 4, W.CAPTURE_STATE)
    struct.pack_into('<I', request, 28, W.CAPTURE)
    struct.pack_into('<H', request, 194, kind)
    request[294] = 1
    capture = bytearray(0x7000)
    capture[24203] = mode
    code = b'\xdd' + struct.pack('<iBB', W.CAPTURE_ENTRY - M.CALLER, 0x30, 56) + b'\xcb'
    r = execute([Region('caller', M.CALLER, code, 'rx'), *M.common(img),
                 Region('request', M.REQUEST, bytes(request), 'rw', True), Region('capture', W.CAPTURE, bytes(capture), 'r'),
                 Region('capture_state', W.CAPTURE_STATE, bytes(4), 'r'),
                 Region('job', M.JOB, bytes(M.JOB_SIZE), 'rw', True), Region('job_aux', W.JOB_AUX, bytes(5764), 'rw', True),
                 # hl_flag's tint lookup reads the P handle (0x621e24ae): none here, so the tint stays red
                 Region('p_handle', 0x621E2000, bytes(0x1000), 'r')],
                dict(pc=M.CALLER, sp=M.STACK + 0xF00, a0=M.REQUEST), W.JOB_PUBLISHED, limit=2_000_000,
                breakpoints=[M.CALLER + 7])
    assert r['status'] == 'returned' and r['registers']['pc'] == W.JOB_PUBLISHED, (r['status'], r['fault'])
    return {c['name']: bytes.fromhex(c['hex']) for c in r['memory']}


def check_route(stock, patched, syms):
    art_list = tuple(syms['hl_ob'] if f == A.REDUCE else f for f in W.SOFT_FOCUS_ONLY_LIST)
    marked = {}
    for mode in (1, 2, 10):
        job = capture_job(patched, mode)
        assert job['job'][35] == MARK and struct.unpack_from('<I', job['job'], 16)[0] & 0x80, mode
        assert W.entries(job['job']) == art_list, [hex(x) for x in W.entries(job['job'])]
        marked[mode] = job
    for mode in (5,):
        assert capture_job(patched, mode) == capture_job(stock, mode), mode
    for kind in (0x1002, 0x2000, 0x2001, 0x1008):
        assert capture_job(patched, 1, kind) == capture_job(stock, 1, kind), hex(kind)
    print(f'A route: Vivid / Natural / Color Creator -> marker {MARK:#x}, flag 0x80 set at the route, Art list with hl_ob '
          'for the blur; Monotone and Vivid of kinds 0x1002 / 0x2000 / 0x2001 / 0x1008 byte for byte stock')
    return marked[1]


PLAIN_BUILDER, ART_BUILDER = 0x603A3C70, 0x60391C1C


def route_target(img, syms, marker):
    """Run hl_route from a `call ...,[],4` like the hooked site 0x603900ec, with job+35 = marker -> the builder it
    jumps to. d1, a0, a1, MDR and sp must reach the builder as the call left them."""
    job = bytearray(0x100)
    job[35] = marker
    code = b'\xdd' + struct.pack('<i', syms['hl_route'] - M.CALLER) + bytes([0x00, 4]) + b'\xcb'
    regs = dict(pc=M.CALLER, sp=M.STACK + 0xF00, a0=M.JOB, d1=0x11223344, a1=0x55667788)
    r = execute([Region('caller', M.CALLER, code, 'rx'), *V.main_regions(img),
                 Region('stack', M.STACK, bytes(0x1000), 'rw'), Region('job', M.JOB, bytes(job), 'rw', True)],
                regs, 0xFFFFFFF0, limit=20000, breakpoints=[PLAIN_BUILDER, ART_BUILDER])
    g = r['registers']
    assert r['status'] == 'breakpoint' and not r['fault'], (r['status'], r['fault'])
    assert (g['a0'], g['d1'], g['a1'], g['mdr'], g['sp']) == (M.JOB, 0x11223344, 0x55667788, M.CALLER + 7,
                                                              M.STACK + 0xF00 - 4), {k: hex(v) for k, v in g.items()}
    return g['pc']


def check_live(patched, syms, off=None):
    """Only a marker of the current Halo stage acts: a stray 0xAx byte left at params+31 by a constructor that never
    writes it (0x6035d6e4) or copies another record's byte there (0x60d19672) keeps the stock builder."""
    other = (MARK & 0xFC) | (1 if STAGE != 1 else 3)
    assert route_target(patched, syms, MARK) == ART_BUILDER
    for marker in (other, MARK & 0xFC, 0xA0 | 0x0C | (MARK & 3) ^ 3, 0x5A, 0):
        assert route_target(patched, syms, marker) == PLAIN_BUILDER, hex(marker)
    line = f'hl_route at stage {STAGE}: {MARK:#x} -> Art builder; {other:#x} (other stage), stage 0, other bytes -> stock'
    if off is not None:
        for marker in range(0xA0, 0xB0):
            assert route_target(off, syms, marker) == PLAIN_BUILDER, hex(marker)
        line += '; Halo Off: every 0xA0..0xAF -> stock builder'
    print(line + ' (d1, a0, a1, MDR and sp as the call left them)')


def check_ob_no_pass(stock, patched, syms, mark):
    image, reference = P.patched(patched), P.patched(stock)
    dev_job = P.run(reference, P.make_job(mark['job'], 1), A.ART_DEV, 1, mark)[0]
    assert P.run(image, dev_job, syms['hl_ob'], 2, mark) == P.run(reference, dev_job, A.REDUCE, 2, mark)
    print('B hl_ob (no-pass build): marked job -> the stock blur with identical submits, waits and job')


def check_ob(stock, patched, syms, mark):
    hollow = bytearray(patched)                         # hl_pass -> `ret [d2,d3,a2,a3],96` (checked separately)
    o = syms['hl_pass'] - V.B
    hollow[o:o + 3] = b'\xdf\xf0\x60'
    hollow = P.patched(bytes(hollow))
    reference = P.patched(stock)
    job = P.make_job(mark['job'], 1)
    job, subs, _ = P.run(reference, job, A.ART_DEV, 1, mark)
    dev_job = job
    # the pass entry: stop there and read its arguments
    jb = bytearray(dev_job)
    struct.pack_into('<H', jb, W.CURSOR_OFFSET, 2)
    code = b'\xfc\xff' + struct.pack('<i', syms['hl_ob'] - M.CALLER) + b'\xcb'
    r = execute([Region('caller', M.CALLER, code, 'rx'), *M.common(hollow), Region('job', M.JOB, bytes(jb), 'rw', True),
                 Region('job_aux', W.JOB_AUX, mark['job_aux'], 'rw'), Region('request', M.REQUEST, mark['request'], 'rw'),
                 Region('capture_state', W.CAPTURE_STATE, bytes(4), 'r'), Region('stubs', P.STUB_BASE, P.STUBS, 'rx'),
                 Region('log', P.LOG, bytes(0x20000), 'rw'), Region('events', 0x6226A000, bytes(0x1000), 'rw')],
                dict(pc=M.CALLER, sp=M.STACK + 0xF00, a0=M.JOB), M.CALLER + 6, limit=2_000_000,
                breakpoints=[syms['hl_pass']])
    assert r['status'] == 'breakpoint', (r['status'], r['fault'])
    recs = {rec[1]: rec for rec in P.records(dev_job)}
    slot = next(s for s in range(48) if struct.unpack_from('<I', dev_job, 6592 + 88 * s + 76)[0] == 0x1000)
    assert r['registers']['a0'] == M.JOB + 6592 + 88 * slot and r['registers']['d0'] == 0x10 | STAGE, \
        (hex(r['registers']['a0']), hex(r['registers']['d0']))
    assert 0x1000 in recs
    got = P.run(hollow, dev_job, syms['hl_ob'], 2, mark)
    want = P.run(reference, dev_job, A.REDUCE, 2, mark)
    assert got == want, 'hl_ob then blur differs from the stock blur'
    unmarked = bytearray(dev_job)
    unmarked[35] = 0
    assert P.run(hollow, bytes(unmarked), syms['hl_ob'], 2, mark) == P.run(reference, bytes(unmarked), A.REDUCE, 2, mark)
    print(f'B hl_ob: marked job -> hl_pass(record of 0x1000 in slot {slot}, d0 = {0x10 | STAGE:#x}), then the stock blur '
          'with identical submits, waits and job; unmarked job = stock blur')


def check_ob_off(stock, off, syms, mark):
    """Halo Off with a job that still carries a full marker (as a stray byte would): hl_ob must not enter hl_pass
    (its entry is made a fault here) and must equal the stock blur."""
    trap = bytearray(off)
    o = syms['hl_pass'] - V.B
    trap[o:o + 4] = b'\xff\xff\xff\xff'
    reference = P.patched(stock)
    dev_job = P.run(reference, P.make_job(mark['job'], 1), A.ART_DEV, 1, mark)[0]
    assert dev_job[35] == MARK
    assert P.run(P.patched(bytes(trap)), dev_job, syms['hl_ob'], 2, mark) == P.run(reference, dev_job, A.REDUCE, 2, mark)
    print(f'B hl_ob, Halo Off: a job carrying {MARK:#x} skips hl_pass and equals the stock blur')


def check_combiners(stock, patched, syms):
    cases = ((MARK, 0x80, 'marked', True), (0, 0x80, 'unmarked (stock Soft Focus)', False),
             (MARK, 0, 'marker without flag 0x80', False), (MARK & 0xFC, 0x80, 'marker with stage 0', False),
             ((MARK & 0xFC) | (1 if STAGE != 1 else 3), 0x80, 'marker of another stage', False),
             (0x5A, 0x80, 'other byte', False))
    for marker, flag, label, neutral in cases:
        for effect, want in ((0x402, C.NEUTRAL_WEIGHTS if neutral else C.STOCK_WEIGHTS),
                             (0x403, C.NEUTRAL_WEIGHTS if neutral else C.STOCK_WEIGHTS)):
            banks = []
            for img in (stock, patched):
                job = bytearray(M.JOB_SIZE)
                job[35] = marker
                job[16] = flag
                request = M.JOB + 11364
                job[11364 + 16] = 3
                struct.pack_into('<H', job, 11364 + 656, effect)
                ctx = struct.pack('<II', 0, request) + struct.pack('<I', C.BASE)
                code = b'\xdd' + struct.pack('<i', C.DISPATCH - C.CALLER) + bytes([0xF0, 20]) + b'\xcb'
                r = execute([Region('caller', C.CALLER, code, 'rx'), *V.main_regions(img),
                             Region('stack', C.STACK, bytes(0x1000), 'rw'),
                             Region('ctx', C.CTX, ctx.ljust(0x100, b'\0'), 'r'), Region('job', M.JOB, bytes(job), 'r'),
                             Region('bank', C.BASE, bytes(0x2000), 'rw', True)],
                            {'pc': C.CALLER, 'sp': C.STACK + 0xF00, 'a0': C.CTX}, C.CALLER + 7, limit=20000)
                assert not r['fault'] and r['registers']['pc'] == C.CALLER + 7, (label, hex(effect), r['fault'])
                banks.append(bytes.fromhex(r['memory'][0]['hex'])[C.BANK:C.BANK + 0x100])
            s_bank, p_bank = banks
            assert C.weights(s_bank) == C.STOCK_WEIGHTS[effect]
            assert C.weights(p_bank) == want[effect], (label, hex(effect), [hex(w) for w in C.weights(p_bank)])
            rest = [o for o in range(0, 0x100, 4) if o not in C.WEIGHTS]
            assert all(p_bank[o:o + 4] == s_bank[o:o + 4] for o in rest), (label, hex(effect))
    print('C combiners 11 / 12: marked job (marker, stage 1..3 and flag 0x80) -> neutral blend, other bank words stock; '
          'unmarked, marker without 0x80, stage 0 or another byte -> stock 600 / 424')


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('spec', nargs='?')
    p.add_argument('--no-pass', action='store_true')
    p.add_argument('--stage-setting', action='store_true',
                   help='the spec reads the stage from sid 961; run with that read fixed at 2 (fix_stage)')
    a = p.parse_args()
    path, syms = spec_files(a.spec, int(a.no_pass), a.stage_setting)
    stock, patched = W.image(BASE_SPEC), W.image(path)
    combined = V.image(path)
    off = None
    if a.stage_setting:
        check_off(stock, patched, syms)
        off = fix_stage(patched, syms, 0)
        patched = fix_stage(patched, syms)
        combined = fix_stage(combined, syms)
        print(f'stage read from sid 961; hl_stage getter call at {syms["hl_stage_get"]:#x} fixed to stage {STAGE}')
    check_live(patched, syms, off)
    mark = check_route(stock, patched, syms)
    (check_ob_no_pass if a.no_pass else check_ob)(stock, patched, syms, mark)
    if off is not None and not a.no_pass:
        check_ob_off(stock, off, syms, mark)
    check_combiners(V.image(BASE_SPEC), combined, syms)          # every hook asks hl_live for the current stage
    print('RESULT PASS')


if __name__ == '__main__':
    main()
