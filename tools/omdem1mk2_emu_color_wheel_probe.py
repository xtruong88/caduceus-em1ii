#!/usr/bin/env python3
"""Probe the dormant E-P7-style COLOR-wheel polygon path in the stock E-M1 Mark II 3.70 image (research only).

    python3 tools/omdem1mk2_emu_color_wheel_probe.py

Runs three stock functions in the emulator, each against two inputs, and shows the output follows the input:
  1. producer 0x6097a1b5 (view vtable slot +1040, request kind 5): which settings it reads (profile 906,
     12 sector ids, cursor id) and the 13-byte buffer it hands to the C3d client 0x6031629a;
  2. payload builder 0x603103ea (C3d client kind 5 -> API command 11): 12 x s8 (-5..+5) + cursor -> 13 codes;
  3. renderer 0x60cad39d (C3d draw task message 5): 13-byte payload -> OpenVG calls; the per-vertex matrix
     calls (translate centre, rotate, translate radius) are logged and turned into the 12 polygon vertices.
  4. cursor byte -> code through the builder (table 0x604fa968).
  5. C3d client open 0x60315f3f / close 0x603164de and fwOpe close 0x607dbc05: kind -> API command.
  6. C3d API task 0x60cae1bf run on queued commands (receive/dly_tsk/send are fixtures): state word 0xa26da4f4
     and the draw-task messages, for (1) Color Creator open then wheel open directly, (1b) wheel close/draw with
     Color Creator open, (2) close CC -> open wheel -> draw -> close wheel -> reopen CC.
  7. bitmap ids drawn by draw msg 4 (Color Creator, 0x60cad14f) and msg 5 (wheel, 0x60cad39d).
Not run: the fwOpe start 0x607db538, GUI message 12987 delivery, the draw task 0x60cac29b itself (surface
open/close, atlas load) and compositing.
Boundaries (fixtures, tools/emu_fixtures/em1_c3d_wheel_stubs.s): the OpenVG API 0x6139xxxx, the C3d trace
helpers 0x602ef1xx/0x602ef4ba, the error log 0x60062a37, text/flush helpers 0x60cadf96/0x60cac8fc, the setting
getter 0x602da802 and the C3d client entry 0x6031629a. Rounding 0x60cae052 is identity; UDF float ops are
modelled in Python (see UDF). All wheel geometry and control flow run as in the image.
"""
import math
import struct
import sys
import tempfile
from pathlib import Path

import omdem1mk2_emu_sdload as SD
import omdem1mk2_emu_validator as V
from penf_emulator import Region, execute

STUB, LOG, MODEL = 0x9F100000, 0x9F200000, 0x9F300000
CALLER, STACK, SP = 0x18020000, 0x18010000, 0x18011F00
VG_RAM = 0x62653000      # C3d/OpenVG handles 0x626537b0..0x626537ec
CUR_RAM = 0x622D5000     # 0x607ac89e returns 0x622d533c (cursor record)
RECEIVER = 0x6097A1B5    # producer, view vtable slot +1040 (10 vtables 0x60b68cf0..0x60b8be1c)
BUILDER = 0x603103EA     # C3d client kind 5 payload builder (-> API command 11)
RENDER = 0x60CAD39D      # C3d draw task message 5 (polygon)

# target: (regs, frame, copy (a0) into the log)
LOGGED = {
    0x6139683A: ('[]', 4, 0), 0x61396868: ('[a2]', 8, 0), 0x61396898: ('[d2,d3]', 12, 0),
    0x613968E6: ('[d2]', 8, 0), 0x613968FE: ('[d2,d3]', 12, 0), 0x6139691A: ('[d2,d3]', 12, 0),
    0x61396936: ('[d2,d3,a2]', 16, 0), 0x613970DD: ('[d2,d3,a2,a3]', 28, 0), 0x6139713C: ('[d2,d3]', 12, 0),
    0x613971FF: ('[d2,d3,a2,a3]', 24, 1), 0x61397220: ('[d2,d3]', 12, 0), 0x61397280: ('[d2,d3,a2,a3]', 40, 0),
    0x613972FD: ('[d2,d3,a2,a3]', 32, 0), 0x6139738E: ('[d2,d3]', 12, 0),
    0x60CADF96: ('[d2,d3,a2,a3]', 36, 0), 0x60CAC8FC: ('[]', 4, 0),
    0x602EF102: ('[d2,d3,a2]', 20, 0), 0x602EF150: ('[d2,d3,a2]', 16, 0), 0x602EF4BA: ('[d2,d3,a2]', 32, 0),
    0x602EF1BA: ('[d2,d3,a2,a3]', 20, 0), 0x60062A37: ('[d2,d3,a2,a3]', 80, 0),
    0x6031629A: ('[d2,d3,a2,a3]', 64, 1),
    0x60CAE052: ('[d2,d3]', 12, 0),   # round-to-nearest: identity here (rounding redone in Python)
    # RTOS / C3d API and client boundaries (4th field: return d0 = 0)
    0x600514E5: ('[d2,d3,a2,a3]', 28, 1, 1),   # snd_mbx: logs the message block (a0)
    0x60054A86: ('[d2,d3,a2,a3]', 68, 0, 1),   # event/flag post
    0x60CAB90C: ('[]', 0, 0, 1),               # open-time display setup (not followed)
    0x602F9583: ('[d2,d3,a2,a3]', 28, 0, 1),   # client -> API mailbox send: d1 = API command
    0x602EF457: ('[d2,d3]', 12, 0),
    0x60310EC6: ('[d2,d3]', 36, 0, 1),         # client: release a display plane after a close (not followed)
}
SEND, POST, CLIENT_SEND = 0x600514E5, 0x60054A86, 0x602F9583
RCV, BLOCKED = 0x513E9, 0xB10C4ED
KERN = 0x47001000          # memcpy 0x4700106b / memset 0x47001177 live outside the main image
C3D_RAM = 0xA26D0000       # C3d API/draw shared block (state word 0xa26da4f4, draw msg 0xa26da498)
API_SAVE = 0x62331000      # API task saved request 0x62331b54..0x62331b68
QUEUE = 0x9F600000
STATE = 0xA26DA4F4
API_TASK, DRAW_TASK = 0x60CAE1BF, 0x60CAC29B
CLIENT_OPEN, CLIENT_CLOSE = 0x60315F3F, 0x603164DE
FWOPE_CLOSE = 0x607DBC05
CC_RENDER = 0x60CAD14F     # draw msg 4 (Color Creator ring + cursor)
APPEND_PATH = 0x613971FF


def build_fixture():
    src = (SD.ROOT / 'tools/emu_fixtures/em1_c3d_wheel_stubs.s').read_text()
    lines = [f'    STUB s_{t:08x}, {t:#x}, "{v[0]}", {v[1]}, {v[2]}, {v[3] if len(v) > 3 else 0}'
             for t, v in LOGGED.items()]
    with tempfile.TemporaryDirectory() as t:
        path = Path(t) / 'stubs.s'
        path.write_text(src + '\n' + '\n'.join(lines) + '\n')
        return SD.assemble_fixture(path, STUB, LOG=LOG, SAVE=LOG + 4, MODEL=MODEL, QUEUE=QUEUE, STATE=STATE)


def patched_image(syms, base=None):
    """Fixture hooks on `base` (default: the stock image; the feed harness passes a patched one)."""
    img = bytearray(base if base is not None else V.image(None))
    hooks = {t: syms[f's_{t:08x}'] for t in LOGGED}
    hooks[0x602DA802] = syms['get_setting']
    hooks[0x600513E9] = syms['task_rcv']
    hooks[0x60051A36] = syms['task_dly']
    for target, stub in hooks.items():
        img[target - V.B:target - V.B + 5] = b'\xdc' + struct.pack('<i', stub - target)
    # The engine executes some udfNN encodings as something else instead of faulting: force a stop (break)
    # on every UDF site so the Python model below always performs the operation.
    for pc, (size, _) in UDF.items():
        img[pc - V.B:pc - V.B + size] = b'\xff' + b'\xcb' * (size - 1)
    return bytes(img)


def f2w(value):
    return struct.unpack('<I', struct.pack('<f', value))[0]


def s32(word):
    return word - (1 << 32) if word & 0x80000000 else word


# The soft-float helpers use the UDF coprocessor (udfNN / mcst), which the engine does not model. The run stops
# on the instruction; Python performs the operation on d0/d1 and resumes after it (same registers and memory).
# Semantics: UDF 2/3/4/5 = add/sub/mul/div, f9e040 = int->float [S, from operand use: constants 23.0, 30.0];
# 0x60cad485 `udf00 9,d0` = d0*9 [I, the E-P7 port map names this byte "range_polygon_step"].
UDF = {
    0x600E2299: (2, lambda d0, d1: f2w(f32(d0) + f32(d1))),
    0x600E2292: (2, lambda d0, d1: f2w(f32(d0) - f32(d1))),
    0x600E22BE: (2, lambda d0, d1: f2w(f32(d0) * f32(d1))),
    0x600E22AC: (2, lambda d0, d1: f2w(f32(d0) / f32(d1))),
    0x600E2367: (3, lambda d0, d1: f2w(float(s32(d0)))),
    0x600E23B4: (3, lambda d0, d1: f2w(float(d0))),
    0x600E230A: (3, lambda d0, d1: f2w(float(s32(d0)))),
    0x600E2371: (3, lambda d0, d1: f2w(float(d0))),
    0x60CAD485: (3, lambda d0, d1: (d0 * 9) & 0xFFFFFFFF),
}
# `mcst48 d1` (f6 61) = float compare d0 with d1 -> PSW like `cmp d1,d0` (Z equal, N less) [I, from the branches
# that follow: ble / bcs]. Sites in the soft-float helpers 0x600e22a0..0x600e244f.
FCMP = (0x600E22A0, 0x600E22A7, 0x600E242F, 0x600E2434, 0x600E2439, 0x600E2448, 0x600E244F)
UDF.update({pc: (2, None) for pc in FCMP})
udf_hits = []


def fcmp_psw(psw, d0, d1):
    a, b = f32(d0), f32(d1)
    return (psw & ~0xF) | (1 if a == b else 0) | (2 if a < b else 0)


def kern_region(syms):
    k = bytearray(0x200)
    for target, name in ((0x4700106B, 'k_memcpy'), (0x47001177, 'k_memset')):
        k[target - KERN:target - KERN + 5] = b'\xdc' + struct.pack('<i', syms[name] - target)
    return Region('kern', KERN, bytes(k), 'rx')


KERN_REGION = None


def run(img, code, entry_bytes, regs, stop, *, model=b'', extra=(), c3d=b''):
    log = bytearray(0x8000)
    struct.pack_into('<I', log, 0, LOG + 32)
    regions = [*V.main_regions(img), Region('caller', CALLER, entry_bytes, 'rx'),
               Region('stub', STUB, code, 'rx'), Region('log', LOG, bytes(log), 'rw', True),
               Region('model', MODEL, model or bytes(0x1000 * 4), 'r'),
               Region('vg', VG_RAM, bytes(range(256)) * 16, 'rw', True),
               Region('cur', CUR_RAM, bytes(0x1000), 'rw', True),
               Region('stack', STACK, bytes(0x2000), 'rw', True), KERN_REGION,
               Region('c3d', C3D_RAM, c3d or bytes(0x10000), 'rw', True),
               Region('apisave', API_SAVE, bytes(0x1000), 'rw', True),
               *(Region(e.name, e.address, e.data, e.permissions, 'w' in e.permissions) for e in extra)]
    state = dict({'sp': SP, 'pc': CALLER}, **regs)
    for _ in range(2000):
        r = execute(regions, state, stop, limit=2_000_000)
        mem = {c['name']: bytes.fromhex(c['hex']) for c in r['memory']}
        pc = r['registers']['pc']
        if r['fault'] and pc in UDF:
            size, op = UDF[pc]
            state = {k: v for k, v in r['registers'].items() if not k.startswith('extra')}
            if op is None:
                state['psw'] = fcmp_psw(state['psw'], state['d0'], state['d1'])
            else:
                state['d0'] = op(state['d0'], state['d1'])
            state['pc'] = pc + size
            udf_hits.append(pc)
            regions = [Region(x.name, x.address, mem.get(x.name, x.data), x.permissions, x.capture, x.alias_of)
                       for x in regions]
            continue
        break
    if r['fault'] or pc != stop:
        raise SystemExit(f"stopped at {pc:#x}: {r['status']} {r['fault']}")
    out = mem['log']
    end = struct.unpack_from('<I', out, 0)[0] - LOG
    entries = [out[o:o + 128] for o in range(32, end, 128)]
    calls = [(struct.unpack_from('<5I', e), e[20:]) for e in entries]
    return r['registers'], calls, mem


def call_bytes(target, mask, frame):
    return b'\xdd' + struct.pack('<i', target - CALLER) + bytes([mask, frame]) + b'\xcb'


def calls_bytes(target):
    return b'\xfc\xff' + struct.pack('<i', target - CALLER) + b'\xcb'


def producer(img, code, profile, sectors, cursor):
    model = bytearray(0x4000)
    put = lambda sid, v: struct.pack_into('<i', model, 4 * sid, v)
    put(906, profile)
    first, cursor_id = {1: (925, 1089), 2: (937, 1094), 3: (949, 1095)}[profile]
    for i, v in enumerate(sectors):
        put(first + i, v)
    put(cursor_id, cursor)
    request = Region('req', 0x9F400000, struct.pack('<H', 5).ljust(64, b'\0'), 'r')
    view = Region('view', 0x9F500000, bytes(0x2000), 'rw')
    # stop right after the C3d client call returns: the rest posts the GUI completion message
    _, calls, _ = run(img, code, calls_bytes(RECEIVER), {'a0': 0x9F500000, 'a1': 0x9F400000}, 0x6097A573,
                      model=bytes(model), extra=(request, view))
    client = [(regs, data) for regs, data in calls if regs[0] == 0x6031629A]
    assert len(client) == 1, calls
    (_, kind, _, buf, _), data = client[0]
    return kind & 0xFFFF, data[:13]


def builder(img, code, payload):
    src = Region('src', 0x9F400000, bytes(payload).ljust(64, b'\0'), 'r')
    out = Region('out', 0x9F500000, bytes(64), 'rw', True)
    regs, _, mem = run(img, code, call_bytes(BUILDER, 0xF0, 60), {'a0': 0x9F500000, 'a1': 0x9F400000},
                       CALLER + 7, extra=(src, out))
    return regs['d0'], mem['out'][:13]


def f32(word):
    return struct.unpack('<f', struct.pack('<I', word))[0]


def render(img, code, payload):
    """Return the polygon vertices (from the stock per-vertex matrix calls), the path-append size and call ids."""
    msg = Region('msg', 0x9F400000, bytes(payload).ljust(64, b'\0'), 'r')
    _, calls, _ = run(img, code, call_bytes(RENDER, 0xF0, 16), {'a0': 0x9F400000}, CALLER + 7, extra=(msg,))
    ids = [c[0][0] for c in calls]
    append = ids.index(APPEND_PATH)
    count = calls[append][0][4]
    # per vertex: LoadIdentity, Translate(cx,cy), Rotate(a), Translate(0,r), transform point (0x61396868)
    verts = []
    for i in range(append):
        if ids[i:i + 5] == [0x6139683A, 0x61396898, 0x613968E6, 0x61396898, 0x61396868]:
            cx, cy = f32(calls[i + 1][0][1]), f32(calls[i + 1][0][2])
            angle = f32(calls[i + 2][0][1])
            tx, ty = f32(calls[i + 3][0][1]), f32(calls[i + 3][0][2])
            c, s_ = math.cos(math.radians(angle)), math.sin(math.radians(angle))
            verts.append((angle, ty, round(cx + c * tx - s_ * ty), round(cy + s_ * tx + c * ty)))
    cursor_branch = 0x61397280 in ids
    return verts, count, cursor_branch, ids


API_NAMES = {0: 'open S1', 5: 'open S2 (Color Creator)', 6: 'draw S2', 7: 'close S2', 10: 'open S3 (COLOR wheel)',
             11: 'draw S3', 12: 'close S3'}


def api_task(img, code, commands, c3d=b''):
    """Run the C3d API task 0x60cae1bf over queued (command, payload) messages; return events and final block.

    Events: ('rx', state_before, cmd), ('draw', msg_type, payload bytes), ('post', mbx, arg), ('blocked', state),
    ('error',). The task loop is stock; receive, dly_tsk, sends, memcpy/memset are fixtures."""
    q = bytearray(0x1000)
    struct.pack_into('<I', q, 0, QUEUE + 16)
    for i, (cmd, payload) in enumerate(commands):
        buf = QUEUE + 0x800 + 0x40 * i
        q[buf - QUEUE:buf - QUEUE + len(payload)] = payload
        struct.pack_into('<4I', q, 16 + 16 * i, 0, 0, cmd, buf)
    struct.pack_into('<4I', q, 16 + 16 * len(commands), 0xFFFFFFFF, 0, 0xFFFFFFFF, 0)
    queue = Region('queue', QUEUE, bytes(q), 'rw')
    _, calls, mem = run(img, code, b'\xcb', {'pc': API_TASK}, STUB_SYMS['task_idle'], extra=(queue,), c3d=c3d)
    events = []
    for (cid, d0, d1, a0, a1), data in calls:
        if cid == RCV:
            events.append(('rx', d0, d1))
        elif cid == BLOCKED:
            events.append(('blocked', d0))
        elif cid == SEND:
            mtype, ptr = struct.unpack_from('<II', data, 0x18)
            body = bytes(data[ptr - a0:ptr - a0 + 13]) if a0 <= ptr < a0 + 108 - 13 else b''
            events.append(('draw', mtype, body))
        elif cid == POST:
            events.append(('post', d0 & 0xFFFF, d1))
        elif cid == 0x60062A37:
            events.append(('error',))
    return events, mem['c3d']


def show_api(title, events):
    print(f'   {title}')
    for e in events:
        if e[0] == 'rx':
            name = 'queue end' if e[2] == 0xFFFFFFFF else API_NAMES.get(e[2], '?')
            print(f'      state {e[1]} <- cmd {e[2] if e[2] != 0xFFFFFFFF else "-"} ({name})')
        elif e[0] == 'draw':
            size = {4: 4, 5: 13}.get(e[1], 0)
            extra = f' payload {list(e[2][:size])}' if size else (f' sub {e[2][0]}' if e[1] == 1 and e[2] else '')
            print(f'         -> draw task msg {e[1]}{extra}')
        elif e[0] == 'post':
            print(f'         -> post mbx {e[1]:#x} arg {e[2]}')
        elif e[0] == 'blocked':
            print(f'         !! BLOCKED: open polls dly_tsk until state 0; state stays {e[1]}')
        elif e[0] == 'error':
            print('         !! error log: state mismatch, command ignored')


def states(events):
    return [e[1] for e in events if e[0] == 'rx']


def client(img, code, entry, frame, kind):
    params = Region('params', 0x9F400000, bytes(64), 'rw')
    _, calls, _ = run(img, code, call_bytes(entry, 0xF0, frame), {'d0': kind, 'a0': 0x9F400000}, CALLER + 7,
                      extra=(params,))
    return [d1 for (cid, d0, d1, a0, a1), _ in calls if cid == CLIENT_SEND]


def fwope_close(img, code, kind):
    this = bytearray(0x400)
    struct.pack_into('<H', this, 424, kind)
    obj = Region('fwope', 0x9F400000, bytes(this), 'rw', True)
    regs, calls, mem = run(img, code, call_bytes(FWOPE_CLOSE, 0xF0, 24), {'d0': 0, 'a0': 0x9F400000}, CALLER + 7,
                           extra=(obj,))
    sent = [d1 for (cid, d0, d1, a0, a1), _ in calls if cid == CLIENT_SEND]
    return sent, struct.unpack_from('<H', mem['fwope'], 424)[0]


def images(img, code, entry, frame, payload):
    msg = Region('msg', 0x9F400000, bytes(payload).ljust(64, b'\0'), 'r')
    _, calls, _ = run(img, code, call_bytes(entry, 0xF0, frame), {'a0': 0x9F400000}, CALLER + 7, extra=(msg,))
    return [(d0, d1) for (cid, d0, d1, a0, a1), _ in calls if cid == 0x60CADF96]


def main():
    global KERN_REGION, STUB_SYMS
    code, syms = build_fixture()
    STUB_SYMS = syms
    KERN_REGION = kern_region(syms)
    img = patched_image(syms)

    print('1. producer 0x6097a1b5, request kind 5')
    for profile, sectors, cursor in ((1, [0] * 12, 3), (2, [5, -5, 3, -3, 1, -1, 0, 2, -2, 4, -4, 5], 7)):
        kind, buf = producer(img, code, profile, sectors, cursor)
        print(f'   profile {profile} sectors {sectors} cursor {cursor} -> client kind {kind}, '
              f'buffer {[b - 256 if b > 127 else b for b in buf[:12]]} + cursor {buf[12]}')
        assert kind == 5 and list(buf[:12]) == [v & 0xFF for v in sectors] and buf[12] == cursor

    print('2. builder 0x603103ea (kind 5 -> API command 11)')
    for vals, cur in (([0] * 12, 255), ([5, -5, 3, -3, 1, -1, 0, 2, -2, 4, -4, 5], 3)):
        err, out = builder(img, code, [v & 0xFF for v in vals] + [cur])
        print(f'   in {vals} cursor {cur} -> codes {list(out[:12])} cursor {out[12]} (err {err & 0xffff})')
        assert list(out[:12]) == [v + 5 for v in vals]

    print('3. renderer 0x60cad39d (draw task message 5)')
    results = []
    for codes in ([5] * 12 + [255], [10, 0, 8, 2, 6, 4, 5, 7, 3, 9, 1, 10] + [3]):
        verts, count, ticks, ids = render(img, code, codes)
        print(f'   codes {codes[:12]} cursor {codes[12]} -> {len(verts)} vertices, path-append {count} points, '
              f'cursor/tick branch {"taken" if ticks else "skipped"}, {len(ids)} logged calls')
        print(f'      angle/radius {[(a, r) for a, r, _, _ in verts]}')
        print(f'      vertices (centre 128,128) {[(x, y) for _, _, x, y in verts]}')
        assert len(verts) == 12 and [r for _, r, _, _ in verts] == [23 + 9 * c for c in codes[:12]]
        assert ticks == (codes[12] != 255)
        results.append(verts)
    assert results[0] != results[1]
    print('OK: stock producer, builder and renderer drive a 12-vertex polygon from 12 sector values')

    print('4. cursor byte -> code (builder 0x603103ea, table 0x604fa968)')
    mapping = {c: builder(img, code, [0] * 12 + [c])[1][12] for c in (0, 1, 2, 6, 12, 13, 14, 255)}
    print(f'   {mapping}')
    assert all(mapping[c] == c - 1 for c in (1, 2, 6, 12)) and mapping[255] == 255

    print('5. C3d client: kind -> API command (open 0x60315f3f, close 0x603164de; fwOpe close 0x607dbc05)')
    opens = {k: client(img, code, CLIENT_OPEN, 64, k) for k in (1, 5)}
    closes = {k: client(img, code, CLIENT_CLOSE, 44, k) for k in (1, 5)}
    print(f'   open {opens}  close {closes}')
    assert opens == {1: [5], 5: [10]} and closes == {1: [7], 5: [12]}
    for kind in (1, 5):
        sent, after = fwope_close(img, code, kind)
        print(f'   fwOpe close with kind {kind} at +424 -> API cmd {sent}, +424 now {after:#x}')
        assert sent == [{1: 7, 5: 12}[kind]] and after == 0xFFFF

    print('6. C3d API task 0x60cae1bf (state word 0xa26da4f4)')
    hv = struct.pack('<HH', 12, 2)
    wheel = bytes([10, 0, 8, 2, 6, 4, 5, 7, 3, 9, 1, 10, 2])
    ev1, _ = api_task(img, code, [(5, b''), (6, hv), (10, b''), (11, wheel)])
    show_api('scenario 1: Color Creator open (S2), then open COLOR wheel directly (cmd 10)', ev1)
    assert states(ev1)[:3] == [0, 2, 2] and ev1[-1][0] == 'blocked' and ev1[-1][1] == 2
    ev1b, _ = api_task(img, code, [(5, b''), (6, hv), (12, b''), (11, wheel), (7, b'')])
    show_api('scenario 1b: S2 open, wheel close/draw without its open (what a kind overwrite leads to)', ev1b)
    assert states(ev1b)[:6] == [0, 2, 2, 2, 2, 0] and sum(e[0] == 'error' for e in ev1b) == 1
    ev2, _ = api_task(img, code, [(5, b''), (6, hv), (7, b''), (10, b''), (11, wheel), (12, b''), (5, b''),
                                  (6, hv)])
    show_api('scenario 2: close S2 -> open S3 -> draw wheel -> close S3 -> reopen S2', ev2)
    assert states(ev2)[:9] == [0, 2, 2, 0, 3, 3, 0, 2, 2] and not any(e[0] in ('blocked', 'error') for e in ev2)
    draws = [(e[1], e[2]) for e in ev2 if e[0] == 'draw']
    assert [d for d, _ in draws if d in (4, 5)] == [4, 5, 4] and dict(draws)[5] == wheel

    print('7. images drawn (0x60cadf96: set, id; atlas rects from 0x61003b38 / 0x61003250)')
    cc = images(img, code, CC_RENDER, 212, struct.pack('<HH', 12, 2))
    cw = images(img, code, RENDER, 16, [5] * 12 + [3])
    print(f'   msg 4 (Color Creator): {cc}')
    print(f'   msg 5 (COLOR wheel):  {cw}')
    assert (2, 210) in cw and all(s_ == 2 for s_, _ in cw)
    print('OK: phase 01 flow checks')


if __name__ == '__main__':
    sys.exit(main())
