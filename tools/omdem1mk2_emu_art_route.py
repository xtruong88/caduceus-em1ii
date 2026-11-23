#!/usr/bin/env python3
"""Send a marked E-M1 II colour still through the Art work-list builder and compare it with the plain route.

    python3 tools/omdem1mk2_emu_art_route.py

Report: plans/reports/research-261123-1709-em1ii-art-route.md.
The dispatcher 0x6039009a picks the Art builder 0x60392e0d (wrapper 0x60391c1c) when the key class job+12 is 1, or
job+11308 == 12; else the colour-still builder via `call 0x603a3c70,[],4` at 0x603900ec (dd 84 3b 01 00 00 04).
Two emulator-only ways to route a job that hl_flag gated (flag 0x80):
  mark:  marker 0xa5 at params+31 (-> job+35, as planned) and the call at 0x603900ec repointed to `route`, which
         jumps to 0x60391c1c for marked jobs and to 0x603a3c70 otherwise (job key unchanged);
  class: params+8 (key class byte -> job+12, job+11308 = 0x01000000 | picture mode) set to 1 (no code hook).
Checks, on jobs built by the real capture entry 0x6041ec04 (fixtures as omdem1mk2_emu_work_list.py):
  1. plain v0.4c18t Vivid/Natural/Color Creator: colour-still list; mark/class: the Soft-Focus-only Art list
     0x60392df2, 0x6039276e, 0x60398e6f, 0x6039905e, 0x60391a9b (Blend Setup 0x60398ee1 not in it); the mark job
     equals the plain job except job+35 and the list; class also changes job+12 and the key; stock flags + mark
     stubs = stock plain job byte for byte;
  2. development request (first submit; job+36 block filled with a pattern, identical in both routes, 4:3 and 3:2):
     mark vs plain differ only in the output list (req+916..+1027) and req+1838 (0 -> 0x0400, written by the Art
     development callback 0x6039271b); key bytes req+8..+11 equal; class also changes req+8 (0 -> 1) and drops
     req+1858 (block+5556, 0x60390a08);
  3. Art items on 4:3 and 3:2: development writes record 0x1000 (0x0302, full 5184x3888, offsets 0, 2*W*H) and
     0x1060 (0x0305, 160x120), and waits; nothing pending after it; 0x60398e6f leaves 0x1061 (full size) pending;
     0x6039905e submits the blend (stage 0xf005, effect 0x0402: 0x1000 + 0x1061 -> record 3, full-size 0x0302;
     the selector maps it to combiner 11), then record 3 -> main JPEG (rows 3888 / 3456), then the thumbnail; the CPU
     waits only on the main encode; no CPU point between blend and encode.
Fixture boundaries as omdem1mk2_emu_plain_route.py (logging stubs for submit/wait/release/job callback, fabricated
RAW record and JPEG entries, no pixels). The Art secondary setup 0x60391c2e runs (class-1 jobs only) inside the
capture entry and writes nothing on these fixtures; the destructor is not run. The fabricated RAW record is full
frame, so on 3:2 the main encode takes rows 0..3455 of record 3 (offset 0); the real crop comes from the real RAW
record. The development's combiner 13 (selected by req+1838 = 0x0400) and the colour stage are not run.
"""
import struct

import omdem1mk2_emu_blend_setup as B
import omdem1mk2_emu_job_marker as M
import omdem1mk2_emu_plain_route as P
import omdem1mk2_emu_validator as V
import omdem1mk2_emu_work_list as W
from penf_emulator import Region, execute

CTOR_CALL, DISPATCH_CALL = 0x6041EC3E, 0x603900EC      # call 0x6038f173 / call 0x603a3c70 (dd rel32 regs frame)
ROUTE_BASE = 0x180A0000
# mn10300-elf-as, linked at 0x180A0000 (--defsym CTOR=0x6038f173 ARTB=0x60391c1c PLAINB=0x603a3c70):
#   +0x00 ctor_mark  (a0 = params): if (12,a0) & 0x80: movbu 0xa5,(31,a0); clr d0; jmp CTOR
#   +0x20 ctor_class (a0 = params): the same, and movbu 1,(8,a0) (key class byte -> Art); clr d0; jmp CTOR
#   +0x40 route      (a0 = job):    movbu (35,a0),d0; cmp 0xa5,d0; bne +; jmp ARTB; +: jmp PLAINB
ROUTE_STUBS = bytes.fromhex(
    'f8000cf8ec80c8082ca500f8501f00dc64f12e48000000000000000000000000f8000cf8ec80c80d2ca500f8501f8001f8500800dc3ff12e48'
    '00000000000000f84023fac8a500c907dcd31b2f48dc223c3048')
CTOR_MARK, CTOR_CLASS, ROUTE = ROUTE_BASE, ROUTE_BASE + 0x20, ROUTE_BASE + 0x40
ART_DEV, REDUCE, FINAL_BLEND = 0x6039276E, 0x60398E6F, 0x6039905E
OUT_LIST = range(916, 1028)                             # req+916: two 56-byte output descriptors
EFFECT = 1838                                           # req+1838: development effect code (0x0400 = Art)
REQ_BYTES = 2048


def repoint(img, site, target):
    m = bytearray(img)
    assert m[site - V.B] == 0xDD
    struct.pack_into('<i', m, site - V.B + 1, target - site)
    return bytes(m)


def variant(kind, base=None):
    img = base or W.image(W.STAGE_2_SPEC)
    if kind == 'mark':
        img = repoint(repoint(img, CTOR_CALL, CTOR_MARK), DISPATCH_CALL, ROUTE)
    elif kind == 'class':
        img = repoint(img, CTOR_CALL, CTOR_CLASS)
    return img


def capture_job(img, mode):
    request = bytearray(0x2000)
    struct.pack_into('<I', request, 4, W.CAPTURE_STATE)
    struct.pack_into('<I', request, 28, W.CAPTURE)
    struct.pack_into('<H', request, 194, 0x1000)
    request[294] = 1
    capture = bytearray(0x7000)
    capture[24203] = mode
    code = b'\xdd' + struct.pack('<iBB', W.CAPTURE_ENTRY - M.CALLER, 0x30, 56) + b'\xcb'
    r = execute([Region('caller', M.CALLER, code, 'rx'), *M.common(img),
                 Region('request', M.REQUEST, bytes(request), 'rw', True), Region('capture', W.CAPTURE, bytes(capture), 'r'),
                 Region('capture_state', W.CAPTURE_STATE, bytes(4), 'r'),
                 Region('job', M.JOB, bytes(M.JOB_SIZE), 'rw', True), Region('job_aux', W.JOB_AUX, bytes(5764), 'rw', True),
                 Region('route', ROUTE_BASE, ROUTE_STUBS, 'rx')],
                dict(pc=M.CALLER, sp=M.STACK + 0xF00, a0=M.REQUEST), W.JOB_PUBLISHED, limit=2_000_000,
                breakpoints=[M.CALLER + 7])
    assert r['status'] == 'returned' and r['registers']['pc'] == W.JOB_PUBLISHED, (r['status'], r['fault'])
    return {c['name']: bytes.fromhex(c['hex']) for c in r['memory']}


def diff(a, b):
    return [i for i in range(len(a)) if a[i] != b[i]]


def check_route():
    list_bytes = set(range(W.LIST_OFFSET, W.LIST_OFFSET + 16 * 12)) | {W.COUNT_OFFSET, W.COUNT_OFFSET + 1}
    jobs = {}
    for mode in (1, 2, 10):                                         # Vivid, Natural, Color Creator
        plain, mark, cls = (capture_job(variant(k), mode) for k in ('plain', 'mark', 'class'))
        assert W.entries(plain['job']) == W.PLAIN_LIST
        for m in (mark, cls):
            assert W.entries(m['job']) == W.SOFT_FOCUS_ONLY_LIST and m['job'][35] == 0xA5
            assert struct.unpack_from('<I', m['job'], 16)[0] == 0x80
        # besides the list and the marker, only the builder's hook job+11304 (-> job+11339 at job start) differs:
        # colour-still 0x603a3c79 (block+5524 == 2) vs Art 0x60391c3f (four Art Filter keys only)
        assert set(diff(plain['job'], mark['job'])) <= list_bytes | {35, 11304, 11305, 11306, 11307}
        assert struct.unpack_from('<2I', plain['job'], 11300) == (0x6039189E, 0x603A3C79)
        assert struct.unpack_from('<2I', mark['job'], 11300) == (0x6039189E, 0x60391C3F)
        assert diff(mark['job'], cls['job']) == [12, 11311] and cls['job'][12] == 1
        assert struct.unpack_from('<I', cls['job'], 11308)[0] == 0x01000000 | mode
        stock = W.image()
        assert capture_job(variant('mark', stock), mode) == capture_job(stock, mode)
        jobs[mode] = plain, mark, cls
    print('1. plain: colour-still list; mark / class: Soft-Focus-only Art list (0x60398ee1 not in it); mark job = plain '
          'job except job+35 and the list; class also job+12 = 1, key 0x010000pm; no 0x80 -> stock job')
    return jobs[1]


def fill(job):
    job = bytearray(job)
    for o in [*range(164, 4752), *range(4756 + 5 * 56, 6592)]:     # job+36 block, not job+4752 (pointer) or outputs
        job[o] = (o * 37 + 5) & 0xFF
    return job


def first_request(img, job, entry, cursor, mem):
    job = bytearray(job)
    struct.pack_into('<H', job, W.CURSOR_OFFSET, cursor)
    code = b'\xfc\xff' + struct.pack('<i', entry - M.CALLER) + b'\xcb'
    r = execute([Region('caller', M.CALLER, code, 'rx'), *M.common(img),
                 Region('job', M.JOB, bytes(job), 'rw', True), Region('job_aux', W.JOB_AUX, mem['job_aux'], 'rw'),
                 Region('request', M.REQUEST, mem['request'], 'rw'), Region('capture_state', W.CAPTURE_STATE, bytes(4), 'r'),
                 Region('stubs', P.STUB_BASE, P.STUBS, 'rx'), Region('log', P.LOG, bytes(0x20000), 'rw'),
                 Region('events', 0x6226A000, bytes(0x1000), 'rw')],
                dict(pc=M.CALLER, sp=M.STACK + 0xF00, a0=M.JOB), M.CALLER + 6, limit=20_000_000, breakpoints=[P.SUBMIT])
    assert r['status'] == 'breakpoint' and r['registers']['a1'] == 0, (r['status'], r['fault'])
    job = bytes.fromhex(next(c['hex'] for c in r['memory'] if c['name'] == 'job'))
    return job[11364:11364 + REQ_BYTES]                    # submit with a1 = 0: the job's request at +11364


def check_development(img, plain, mark, cls):
    for aspect in (1, 2):
        qp, qm, qc = (first_request(img, fill(P.make_job(m['job'], aspect)), entry, cur, m)
                      for m, entry, cur in ((plain, P.DEV_ITEM, 2), (mark, ART_DEV, 1), (cls, ART_DEV, 1)))
        d = diff(qp, qm)
        assert d and set(d) <= set(OUT_LIST) | {EFFECT, EFFECT + 1}, d
        assert struct.unpack_from('<H', qp, EFFECT)[0] == 0 and struct.unpack_from('<H', qm, EFFECT)[0] == 0x0400
        assert qp[8:12] == qm[8:12] == plain['job'][12:16]          # job key bytes, copied by the request init
        assert P.desc(qp, 916)[:2] == (P.JPEG_BUS, 0x0702) and P.desc(qm, 916)[1:] == (0x0302, 5184, 5184, 3888)
        assert P.desc(qm, 972)[1:] == (0x0305, 160, 160, 120)
        assert diff(qm, qc) == [8, 1858] and qc[8] == 1 and qc[1858] == 0   # class 1 also skips req+1858 = block+5556
    print('2. development request, same job+36 block, 4:3 and 3:2: Art differs from plain only in the output list '
          '(0x1000 0x0302 5184x3888 + 0x1060 0x0305 160x120 instead of main JPEG + thumbnail) and req+1838 0 -> 0x0400; '
          'key req+8..11 equal (class: req+8 = 1)')


def check_items(img, mark):
    for aspect, rows in ((1, 3888), (2, 3456)):
        job = P.make_job(mark['job'], aspect)
        job, subs, waits = P.run(img, job, 0x60392DF2, 0, mark)
        assert not subs
        job, subs, waits = P.run(img, job, ART_DEV, 1, mark)
        recs = {r[1]: r for r in P.records(job)}
        dev = recs[0x1000]
        assert dev[2][1:] == (0x0302, 5184, 5184, 3888) and dev[3] == (5184, 3888, 0, 0) and dev[4] == 2 * 5184 * 3888
        assert recs[0x1060][2][1:] == (0x0305, 160, 160, 120)
        assert len(subs) == 1 and waits == [(P.TOKEN0, 1)] and P.pending(job) == [0, 0, 0, 0]
        job, subs, waits = P.run(img, job, REDUCE, 2, mark)
        assert struct.unpack_from('<HH', subs[0], 12)[0] == 0xF005 and struct.unpack_from('<H', subs[0], 656)[0] == 0x0401
        assert P.records(job)[-1][1] == 0x1061 and P.pending(job)[2] == P.TOKEN0
        job, subs, waits = P.run(img, job, FINAL_BLEND, 3, mark)
        blend, main = subs[0], subs[1]
        assert struct.unpack_from('<H', blend, 12)[0] == 0xF005 and struct.unpack_from('<H', blend, 656)[0] == 0x0402
        assert P.desc(blend, 20)[0] == dev[2][0] and P.desc(blend, 84)[1:] == (0x0302, 5184, 5184, 3888)
        out = P.desc(blend, 340)
        assert out[1:] == (0x0302, 5184, 5184, 3888)
        assert B.selector_on(img, blend.ljust(0x800, b'\0')) == 11
        rec3 = {r[1]: r for r in P.records(job)}[3]
        assert rec3[2] == out and rec3[3] == (5184, 3888, 0, 0)
        assert P.desc(main, 20) == out and P.desc(main, 340) == (P.JPEG_BUS, 0x0702, 5184, 5184, rows)
        assert len(subs) == 3 and waits == [(P.TOKEN1, 2)] and P.pending(job)[3] == P.LOG + 0x1080
        job, subs, _ = P.run(img, job, 0x60391A9B, 4, mark)
        assert len(subs) == (0 if aspect == 1 else 1)
    print('3. Art items, 4:3 / 3:2: development -> 0x1000 (0x0302 5184x3888, offsets 0) + 0x1060, waited, nothing '
          'pending; 0x60398e6f -> 0x1061 pending; 0x6039905e: blend 0x1000 + 0x1061 -> record 3 (full-size 0x0302, '
          'combiner 11), chained main encode record 3 -> JPEG (rows 3888 / 3456), CPU waits on the main encode only')


def main():
    plain, mark, cls = check_route()
    img = P.patched(W.image(W.STAGE_2_SPEC))
    check_development(img, plain, mark, cls)
    check_items(img, mark)
    print('RESULT PASS')


if __name__ == '__main__':
    main()
