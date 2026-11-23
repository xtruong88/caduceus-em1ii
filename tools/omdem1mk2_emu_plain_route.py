#!/usr/bin/env python3
"""Find where a CPU pass can see the developed image of an ordinary E-M1 II colour still (plain route).

    python3 tools/omdem1mk2_emu_plain_route.py

Report: plans/reports/research-261123-1123-em1ii-plain-route-completion.md.
The class-0 colour-still builder 0x603a63f4 publishes 0x603a5d7d, 0x603a5d96, 0x603a5df6 (development 0x603a44ca)
and the common last item 0x60391a9b, which every list gets from the immediate at 0x6039011f (`mov imm32,d2` at
0x6039011d). The output table (job+4756, 5 x 56 B) is built by the capture code: main JPEG 0x0702 at 0x60421bb4
(+42 = 4), EXIF thumbnail 0x0702 160x120 at 0x60421e76 (+42 = 0x208). 0x603a573d routes a JPEG entry through a
0x0302 intermediate record (id 5, or id 4 for the last step) only when its +42 has bit 3 and the aspect index
job+23 (request+283) is not 1.
Checks, on a job built by the real capture entry 0x6041ec04 (omdem1mk2_emu_work_list.py):
  1. changing only the immediate at 0x6039011f changes only the last work-list word; the runner calls it, a0 = job;
  2. stock, 4:3 and 3:2: the development request writes the main JPEG entry itself; the only 0x0302 record is the
     160x120 thumbnail intermediate; no record 0x1000 and no full-size record exist at any point;
  3. main entry +42 = 0x208 (as the thumbnail), 3:2: the development request writes a full-size record 5 (0x0302,
     5184x3456, window offsets 0), the item waits for it and leaves nothing pending; 0x60391a9b encodes that record
     into the main JPEG entry; the thumbnail's record (also id 5) is left unencoded;
  4. the same on 4:3 needs the aspect test at 0x603a590c to fail (byte 0x603a590d 01 -> 7f, emulator only);
  5. after 4, waiting for the main encode, dropping the main record and calling 0x60391a9b again encodes the
     thumbnail record into the first JPEG entry with bit 3 (the main one!); with the main entry's +42 set back to 4
     it goes to the thumbnail entry, leaving one pending request as stock.
Fixture boundaries: RAW record 0x01000002 and the two JPEG entries are fabricated (real capture fills them through
the job's +36 block); submit 0x60390536, wait 0x603901f3, release 0x6038beea and the job callback 0x60380399 are
logging stubs (STUBS below); the buffer fill 0x6038ce2d returns 0; check 5 drops the main record by clearing its
id in Python. No image data is processed.
"""
import struct

import omdem1mk2_emu_job_marker as M
import omdem1mk2_emu_validator as V
import omdem1mk2_emu_work_list as W
from penf_emulator import Region, execute

APPEND_INSN, APPEND_IMM = 0x6039011D, 0x6039011F
OUTPUT_ITEM, DEV_ITEM, REDIRECT = 0x60391A9B, 0x603A5DF6, 0x18050000
ASPECT_CMP = 0x603A590C            # cmp 1,d0 on job+23 inside 0x603a573d
SUBMIT, WAIT, RELEASE, CALLBACK, FILL = 0x60390536, 0x603901F3, 0x6038BEEA, 0x60380399, 0x6038CE2D
STUB_BASE, LOG = 0x18060000, 0x18070000
STUB_AT = {SUBMIT: 0x00, WAIT: 0x50, RELEASE: 0x80, CALLBACK: 0xA0}
# Assembled from (mn10300-elf-as, linked at 0x18060000):
#   +0x00 submit: copy 1 KB of the request (a1, or job+11364) to LOG+0x10000+1K*n; token = LOG+0x1000+64*n,
#         token+0 = request, +28 = dependency (28,sp), +16 = 1; *d1 = token; n++ at LOG+0; d0 = 0; ret [d2,d3,a2,a3],24
#   +0x50 wait: log a0 at LOG+0x800+4*k and n at LOG+0xa00+4*k; k++ at LOG+4; d0 = 0; ret [d3,a2,a3],28
#   +0x80 release: log d0 at LOG+0x400+4*k; k++ at LOG+8; ret [a2,a3],12
#   +0xa0 job callback: op 19 (allocate) writes record+64 = 0x8a000000 + 32 MB * k; d0 = 1; ret [a2,a3],12
STUBS = bytes.fromhex(
    'b500c90791fad1642cfca6000007188bf8c30afcc300000818f1ee972c00017f6e535228ffc9fa8bf8c306fcc300100718f1eef016'
    '581cf8121c8001f81210f1e4f01848fc890000071800dff0180000fca704000718f1eef17af17afcd200080718f012fca400000718fa'
    '1200024cfc8d0400071800df701c00000000000000fca508000718f1e6f17af17afcd2000407186244fc8508000718df300c000000a0'
    '13c923fca50c000718fcc10000008af81540fcc100000076fcc100000002fc850c0007188001df300c')
RAW_BUS, JPEG_BUS, THUMB_BUS, FIRST_ALLOC = 0xA1000000, 0xA3000000, 0xA4000000, 0x8A000000
SIZES = {1: (5184, 3888), 2: (5184, 3456)}                     # aspect index (job+23) -> main JPEG size
TOKEN0, TOKEN1 = LOG + 0x1000, LOG + 0x1040


def patched(img, force_record5=False):
    m = bytearray(img)
    for at, off in STUB_AT.items():
        m[at - V.B:at - V.B + 5] = b'\xdc' + struct.pack('<i', STUB_BASE + off - at)    # jmp stub
    m[FILL - V.B:FILL - V.B + 4] = bytes([0x00, 0xDF, 0xF0, 56])                       # clr d0; ret [..],56
    if force_record5:
        assert m[ASPECT_CMP - V.B:ASPECT_CMP - V.B + 2] == b'\xa0\x01'
        m[ASPECT_CMP - V.B + 1] = 0x7F
    return bytes(m)


def make_job(base, aspect, main_flag=4):
    job = bytearray(base)
    o = 6592                                                   # record slot 0: RAW input 0x01000002
    struct.pack_into('<IIHHHHHH', job, o, RAW_BUS, 0, 0x0101, 5248, 5240, 3912, 5240, 3912)
    struct.pack_into('<I', job, o + 64, RAW_BUS)
    struct.pack_into('<II', job, o + 72, 5248 * 3912 * 2, 0x01000002)
    w, h = SIZES[aspect]
    for k, bus, (ew, eh), flag in ((0, JPEG_BUS, (w, h), main_flag), (1, THUMB_BUS, (160, 120), 0x208)):
        e = 4756 + 56 * k
        struct.pack_into('<IIHHHH', job, e, bus, 0, 0x0702, (ew + 31) & ~31, ew, eh)
        struct.pack_into('<H', job, e + 42, flag)
    job[23] = aspect
    return job


def run(img, job, entry, cursor, mem):
    job = bytearray(job)
    struct.pack_into('<H', job, W.CURSOR_OFFSET, cursor)
    code = b'\xfc\xff' + struct.pack('<i', entry - M.CALLER) + b'\xcb'                # calls (work-list item)
    r = execute([Region('caller', M.CALLER, code, 'rx'), *M.common(img),
                 Region('job', M.JOB, bytes(job), 'rw', True), Region('job_aux', W.JOB_AUX, mem['job_aux'], 'rw'),
                 Region('request', M.REQUEST, mem['request'], 'rw'),
                 Region('capture_state', W.CAPTURE_STATE, bytes(4), 'r'),
                 Region('stubs', STUB_BASE, STUBS, 'rx'), Region('log', LOG, bytes(0x20000), 'rw', True),
                 Region('events', 0x6226A000, bytes(0x1000), 'rw')],
                dict(pc=M.CALLER, sp=M.STACK + 0xF00, a0=M.JOB), M.CALLER + 6, limit=20_000_000)
    assert r['status'] == 'returned' and not r['fault'], (hex(entry), r['status'], r['fault'])
    assert r['registers']['d0'] & 0xFFFF == 0, hex(r['registers']['d0'])
    out = {c['name']: bytes.fromhex(c['hex']) for c in r['memory']}
    log = out['log']
    n, nw = struct.unpack_from('<II', log, 0)
    submits = [log[0x10000 + 1024 * i:0x10000 + 1024 * (i + 1)] for i in range(n)]
    waits = [(struct.unpack_from('<I', log, 0x800 + 4 * i)[0], struct.unpack_from('<I', log, 0xA00 + 4 * i)[0])
             for i in range(nw)]
    return out['job'], submits, waits


def desc(q, off):                                              # bus, format, stride, width, rows
    return struct.unpack_from('<I4xHHHH', q, off)


def records(job):
    found = []
    for s in range(48):
        o = 6592 + 88 * s
        ident = struct.unpack_from('<I', job, o + 76)[0]
        if ident:
            found.append((s, ident, desc(job, o), struct.unpack_from('<4H', job, o + 16),
                          struct.unpack_from('<I', job, o + 72)[0]))
    return found


def pending(job):
    return [struct.unpack_from('<I', job, 10992 + 12 * i)[0] for i in range(4)]


def main():
    stock = W.image()
    assert stock[APPEND_INSN - V.B:APPEND_INSN - V.B + 6] == b'\xfc\xce' + struct.pack('<I', OUTPUT_ITEM)
    mem, _ = W.capture_job(stock, 0x1000, 1, 0)
    assert W.entries(mem['job']) == W.PLAIN_LIST

    redirected = bytearray(stock)
    struct.pack_into('<I', redirected, APPEND_IMM - V.B, REDIRECT)
    redirected = bytes(redirected)
    new, _ = W.capture_job(redirected, 0x1000, 1, 0)
    expected = bytearray(mem['job'])
    struct.pack_into('<I', expected, W.LIST_OFFSET + 12 * 3, REDIRECT)
    assert new == dict(mem, job=bytes(expected))
    W.check_dispatch(redirected, new, 3, REDIRECT)
    print(f'1. immediate {APPEND_IMM:#x}: only item 3 (job+{W.LIST_OFFSET + 36}) changes; the runner calls it, a0 = job')

    img = patched(stock)
    for aspect, rec_id, window in ((1, 4, (160, 120, 0, 0)), (2, 5, (160, 106, 0, 7))):
        job, subs, waits = run(img, make_job(mem['job'], aspect), DEV_ITEM, 2, mem)
        assert desc(subs[0], 84)[:2] == (RAW_BUS, 0x0101) and desc(subs[0], 916) == (JPEG_BUS, 0x0702, 5184, *SIZES[aspect])
        assert waits[0] == (TOKEN0, 1)
        recs = records(job)
        assert [(r[1], r[2][1:], r[3]) for r in recs[1:]] == [(rec_id, (0x0302, 160, 160, 120), window)], recs
        if aspect == 1:                          # last step (record 4): 0x603a42fb encodes it inside the item
            assert len(subs) == 2 and desc(subs[1], 20)[1] == 0x0302 and desc(subs[1], 340)[:2] == (THUMB_BUS, 0x0702)
            assert pending(job) == [0, 0, TOKEN1, 0]
        job, subs, _ = run(img, job, OUTPUT_ITEM, 3, mem)
        assert len(subs) == (0 if aspect == 1 else 1)
        if subs:
            assert desc(subs[0], 20)[2:] == (160, 160, 120) and desc(subs[0], 340)[:2] == (THUMB_BUS, 0x0702)
    print('2. stock 4:3 / 3:2: the development request writes the main JPEG entry; the only 0x0302 record is the '
          '160x120 thumbnail intermediate (id 4 / id 5); no 0x1000 or full-size record')

    def main_via_record5(img, aspect):
        job, subs, waits = run(img, make_job(mem['job'], aspect, main_flag=0x208), DEV_ITEM, 2, mem)
        w, h = SIZES[aspect]
        recs = records(job)
        assert recs[1][1:] == (5, (FIRST_ALLOC, 0x0302, w, w, h), (w, h, 0, 0), w * h * 2), recs
        assert recs[2][1] == 5 and recs[2][2][3:] == (160, 120)
        assert len(subs) == 1 and desc(subs[0], 916) == (FIRST_ALLOC, 0x0302, w, w, h)
        assert waits == [(TOKEN0, 1)] and pending(job) == [0, 0, 0, 0]
        job, subs, _ = run(img, job, OUTPUT_ITEM, 3, mem)
        assert len(subs) == 1 and desc(subs[0], 20)[:2] == (FIRST_ALLOC, 0x0302)
        assert desc(subs[0], 340) == (JPEG_BUS, 0x0702, w, w, h) and pending(job)[3] == TOKEN0
        return job

    main_via_record5(img, 2)
    print('3. main +42 = 0x208, 3:2: development -> full-size record 5 (offsets 0), waited, nothing pending; '
          '0x60391a9b encodes it into the main JPEG; the thumbnail record (also id 5) stays unencoded')
    job, subs, _ = run(img, make_job(mem['job'], 1, main_flag=0x208), DEV_ITEM, 2, mem)
    assert desc(subs[0], 916)[:2] == (JPEG_BUS, 0x0702)
    forced = patched(stock, force_record5=True)
    job = main_via_record5(forced, 1)
    print('4. 4:3: the same only with the aspect test at 0x603a590c failed (stock 4:3 writes the main JPEG directly)')

    job = bytearray(job)
    struct.pack_into('<I', job, 10992 + 36, 0)                  # the wrapper waited for the main encode ...
    main_slot = records(job)[1][0]
    struct.pack_into('<I', job, 6592 + 88 * main_slot + 76, 0)  # ... and released the main record
    second, subs, _ = run(forced, job, OUTPUT_ITEM, 3, mem)
    assert len(subs) == 1 and desc(subs[0], 20)[2:] == (160, 160, 120)
    assert desc(subs[0], 340)[:2] == (JPEG_BUS, 0x0702)        # first JPEG entry with bit 3: the main one
    struct.pack_into('<H', job, 4756 + 42, 4)                  # so the main entry's +42 must go back to 4 first
    job, subs, _ = run(forced, job, OUTPUT_ITEM, 3, mem)
    assert len(subs) == 1 and desc(subs[0], 20)[2:] == (160, 160, 120)
    assert desc(subs[0], 340)[:2] == (THUMB_BUS, 0x0702) and pending(job)[3] == TOKEN0
    print('5. a second 0x60391a9b call encodes the thumbnail record into the first bit-3 JPEG entry: the main one, '
          'unless its +42 is set back to 4 first; then thumbnail -> thumbnail entry, one request pending as stock')
    print('RESULT PASS')


if __name__ == '__main__':
    main()
