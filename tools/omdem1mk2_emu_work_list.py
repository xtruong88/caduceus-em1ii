#!/usr/bin/env python3
"""Locate Soft Focus Blend Setup in the E-M1 II's still-capture work list.

    python3 tools/omdem1mk2_emu_work_list.py

Run the stock capture entry 0x6041ec04 on request/capture fixtures. Firmware fills
the stack params, constructs the job and chooses its builder. The Art Filter
control with an additional effect stops after the primary list is finalized,
before the secondary setup needs camera services. The single-item dispatch test
sets only the work-list cursor. Image processing and ISP completion are outside
this harness. The only firmware stubs are the job allocator and capture logger.
"""
import struct

import omdem1mk2_emu_job_marker as M
import omdem1mk2_emu_validator as V
from penf_emulator import Region, execute

CAPTURE, CAPTURE_STATE = 0x18100000, 0x18110000
JOB_AUX = 0x19010000
CAPTURE_ENTRY, JOB_PUBLISHED = 0x6041EC04, 0x6041EC4B
PRIMARY_LIST_READY = 0x6038F56B
TRACE_LOG = 0x604182DF
PLAIN_BUILDER = 0x603A63F4
BLEND_LOAD, BLEND_IMMEDIATE, BLEND_STORE = 0x60393A69, 0x60393A6B, 0x60393B9C
BLEND, REDIRECTED_BLEND = 0x60398EE1, 0x18050000
RUNNER, SETUP_DISPATCH = 0x6038FAE5, 0x6038FB5F
LIST_OFFSET, CURSOR_OFFSET, COUNT_OFFSET = 10984, 11312, 11314
ITEM = struct.Struct('<III')
PLAIN_LIST = (0x603A5D7D, 0x603A5D96, 0x603A5DF6, 0x60391A9B)
SOFT_FOCUS_ONLY_LIST = (0x60392DF2, 0x6039276E, 0x60398E6F, 0x6039905E, 0x60391A9B)
SOFT_FOCUS_EXTRA_LIST = (0x60392DF2, 0x6039276E, 0x60398E6F, BLEND, 0x603976EB, 0x60391A9B)
STAGE_2_SPEC = V.ROOT / 'releases/em1mk2/v0.4c18t/edits.json'


def image(spec=None):
    img = bytearray(V.image(spec))
    # malloc(15484) for the job and malloc(5764) for its auxiliary state.
    # Use distinct allocations, and fail any unmodelled size.
    malloc = (b'\xfa\xc8\x7c\x3c\xc8\x0d'  # cmp 15484,d0; beq job
              b'\xfa\xc8\x84\x16\xc8\x10'  # cmp 5764,d0; beq aux
              b'\x90\x00\xdf\x00\x04'      # mov 0,a0; ret [],4
              b'\xfc\xdc' + struct.pack('<I', M.JOB) + b'\xdf\x00\x04'
              b'\xfc\xdc' + struct.pack('<I', JOB_AUX) + b'\xdf\x00\x04')
    off = M.MALLOC - V.B
    img[off:off + len(malloc)] = malloc
    off = TRACE_LOG - V.B
    img[off:off + 3] = b'\xdf\xf0\xb0'  # ret [d2,d3,a2,a3],176
    return bytes(img)


def call(img, target, mask, frame, regs, stop, regions, trace_limit=0):
    code = b'\xdd' + struct.pack('<iBB', target - M.CALLER, mask, frame) + b'\xcb'
    result = execute([Region('caller', M.CALLER, code, 'rx'), *M.common(img), *regions],
                     dict(pc=M.CALLER, sp=M.STACK + 0xF00, **regs), stop,
                     limit=2_000_000, breakpoints=[M.CALLER + 7], trace_limit=trace_limit, trace_tail=True)
    assert result['status'] == 'returned' and result['registers']['pc'] == stop, (
        hex(target), hex(stop), hex(result['registers']['pc']), result['status'], result['fault'],
        hex(result['registers']['d0']))
    return result


def capture_job(img, kind, mode, effect, stop=JOB_PUBLISHED):
    request = bytearray(0x2000)
    struct.pack_into('<I', request, 4, CAPTURE_STATE)
    struct.pack_into('<I', request, 28, CAPTURE)
    struct.pack_into('<H', request, 194, kind)
    request[294] = 1  # callback operation 13 reports an active capture
    capture = bytearray(0x7000)
    capture[24203] = mode
    capture[24951] = effect
    result = call(img, CAPTURE_ENTRY, 0x30, 56, {'a0': M.REQUEST}, stop,
                  [Region('request', M.REQUEST, bytes(request), 'rw', True),
                   Region('capture', CAPTURE, bytes(capture), 'r'),
                   Region('capture_state', CAPTURE_STATE, bytes(4), 'r'),
                   Region('job', M.JOB, bytes(M.JOB_SIZE), 'rw', True),
                   Region('job_aux', JOB_AUX, bytes(5764), 'rw', True)], trace_limit=2048)
    mem = {item['name']: bytes.fromhex(item['hex']) for item in result['memory']}
    if stop == JOB_PUBLISHED:
        assert result['registers']['d1'] == 0, result['registers']
        assert struct.unpack_from('<I', mem['request'], 36)[0] == M.JOB
    else:
        assert result['registers']['d0'] == 0, result['registers']
    job = mem['job']
    assert struct.unpack_from('<I', job, 8)[0] == M.REQUEST
    assert struct.unpack_from('<I', job, 13248)[0] == JOB_AUX
    assert struct.unpack_from('<H', job, 20)[0] == 0x1000 and job[11341] == 0
    trace = {row['pc']: row for row in result['trace']}
    return mem, trace


def work_list(job):
    count, = struct.unpack_from('<H', job, COUNT_OFFSET)
    assert 0 < count <= 16, count
    return tuple(ITEM.unpack_from(job, LIST_OFFSET + ITEM.size * i) for i in range(count))


def entries(job):
    return tuple(item[0] for item in work_list(job))


def check_dispatch(img, mem, index, target):
    # Execute the real runner's indirect CALLS and stop at the selected entry.
    job = bytearray(mem['job'])
    struct.pack_into('<H', job, CURSOR_OFFSET, index)
    result = call(img, RUNNER, 0xF0, 32, {'d0': M.JOB, 'd1': index + 1}, target,
                  [Region('job', M.JOB, bytes(job), 'rw'), Region('job_aux', JOB_AUX, mem['job_aux'], 'rw'),
                   Region('request', M.REQUEST, mem['request'], 'rw'),
                   Region('capture_state', CAPTURE_STATE, bytes(4), 'r')], trace_limit=1)
    assert result['trace'][-1]['pc'] == SETUP_DISPATCH
    assert result['registers']['a0'] == M.JOB


def main():
    stock, stage_2 = image(), image(STAGE_2_SPEC)
    for kind in (0x1000, 0x1001):
        for mode in (1, 2, 10):  # Vivid, Natural, Color Creator
            off_mem, off_trace = capture_job(stock, kind, mode, 0)
            on_mem, on_trace = capture_job(stage_2, kind, mode, 0)
            off, on = off_mem['job'], on_mem['job']
            assert struct.unpack_from('<I', off, 16)[0] == 0
            assert struct.unpack_from('<I', on, 16)[0] == 0x80
            assert work_list(off) == work_list(on) and entries(on) == PLAIN_LIST
            assert all(PLAIN_BUILDER in trace and BLEND_LOAD not in trace for trace in (off_trace, on_trace))
    print('Vivid / Natural / Color Creator, kinds 0x1000 / 0x1001: stage 2 sets 0x80; same four stock work-list items')

    mem, trace = capture_job(stock, 0x1000, 101, 0)
    only = mem['job']
    assert struct.unpack_from('<I', only, 16)[0] == 0x80
    assert entries(only) == SOFT_FOCUS_ONLY_LIST
    assert BLEND_LOAD in trace and trace[0x60393E0F]['a2'] == BLEND
    print('Art Filter 101, flag 0x80: stock Art builder returns with Blend Setup pending in a2')

    extra, trace = capture_job(stock, 0x1000, 101, 2, stop=PRIMARY_LIST_READY)
    job = extra['job']
    assert struct.unpack_from('<I', job, 16)[0] == 0x480
    assert entries(job) == SOFT_FOCUS_EXTRA_LIST
    assert trace[BLEND_STORE]['a2'] == BLEND
    index = SOFT_FOCUS_EXTRA_LIST.index(BLEND)
    check_dispatch(stock, extra, index, BLEND)

    redirected = bytearray(stock)
    off = BLEND_IMMEDIATE - V.B
    assert redirected[off - 2:off + 4] == b'\xfc\xde' + struct.pack('<I', BLEND)
    struct.pack_into('<I', redirected, off, REDIRECTED_BLEND)
    redirected = bytes(redirected)
    new, _ = capture_job(redirected, 0x1000, 101, 2, stop=PRIMARY_LIST_READY)
    expected_job = bytearray(job)
    offset = LIST_OFFSET + ITEM.size * index
    struct.pack_into('<I', expected_job, offset, REDIRECTED_BLEND)
    assert new == dict(extra, job=bytes(expected_job))
    check_dispatch(redirected, new, index, REDIRECTED_BLEND)
    print(f'Art Filter 101 + effect 2, flags 0x480: slot {index} (job+{offset}, +0) dispatches {BLEND:#x}')
    print(f'Changing only the immediate at {BLEND_IMMEDIATE:#x} redirects that slot and its dispatch')
    print('RESULT PASS')


if __name__ == '__main__':
    main()
