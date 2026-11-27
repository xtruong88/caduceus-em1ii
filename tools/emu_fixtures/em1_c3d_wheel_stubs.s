/* Emulator-only boundaries for the E-M1 II C3d COLOR-wheel probe (tools/omdem1mk2_emu_color_wheel_probe.py).
 *
 * Each LOG stub records (id, d0, d1, a0, a1) and, when COPY is set, 108 bytes from a0, into the LOG ring, then
 * returns with the caller's own register list and frame (d0 as at entry, or 0 when ZERO is set). Used for the
 * OpenVG API (0x6139xxxx), trace helpers, RTOS calls and the C3d client entries, so the stock code under test
 * runs with its real arguments visible.
 * Entry layout (128 bytes): +0 id, +4 d0, +8 d1, +12 a0, +16 a1, +20..+127 copy of (a0) when COPY.
 * LOG+0 holds the next free entry address (starts at LOG+32); LOG+4..+15 is scratch; LOG+16 counts dly_tsk.
 *
 * Task boundaries (no RTOS): `task_rcv` replaces the mailbox receive 0x600513e9. It logs (id 0x513e9, d0 = the C3d
 * API state word STATE, d1 = the next queued command) and copies the next 16-byte message from the queue at QUEUE
 * (+0 read pointer, entries from +16, a word -1 ends the queue) into the task's buffer (*(a0)). An empty queue
 * jumps to task_idle, the harness stop address. `task_dly` replaces dly_tsk 0x60051a36: the fifth wait in a row
 * logs id 0xb10c4ed (blocked: the task polls a state nobody else will change) and stops at task_idle. */
.am33_2
.text
.global _start
_start:
    calls (a1)
probe_return:
    nop

.global task_idle
task_idle:
    nop
    bra task_idle

.macro STUB name, id, regs, frame, copy, zero=0
.global \name
\name:
    mov d0,(SAVE)
    mov d1,(SAVE+4)
    mov a0,(SAVE+8)
    mov a1,(SAVE+12)
    mov (LOG),a1
    mov \id,d0
    mov d0,(a1)
    mov (SAVE),d0
    mov d0,(4,a1)
    mov (SAVE+4),d0
    mov d0,(8,a1)
    mov (SAVE+8),d0
    mov d0,(12,a1)
    mov (SAVE+12),d0
    mov d0,(16,a1)
.if \copy
    mov (SAVE+8),a0
    add 20,a1
    mov 27,d1
1:
    mov (a0),d0
    mov d0,(a1)
    add 4,a0
    add 4,a1
    add -1,d1
    bne 1b
    mov (LOG),a1
.endif
    add 128,a1
    mov a1,(LOG)
    mov (SAVE),d0
.if \zero
    clr d0
.endif
    ret \regs,\frame
.endm

/* Setting getter 0x602da802 (call [],4): d0 = id -> MODEL word id. */
.global get_setting
get_setting:
    exthu d0
    asl2 d0
    mov MODEL,a0
    add d0,a0
    mov (a0),d0
    ret [],4

/* mailbox receive 0x600513e9 (call [d2,d3,a2,a3],24): a0 -> {buffer, size} */
.global task_rcv
task_rcv:
    mov (a0),a0
    mov (QUEUE),a1
    mov (8,a1),d1
    mov (LOG),a2
    mov 0x513e9,d0
    mov d0,(a2)
    mov (STATE),d0
    mov d0,(4,a2)
    mov d1,(8,a2)
    add 128,a2
    mov a2,(LOG)
    clr d0
    mov d0,(LOG+16)
    mov (a1),d0
    cmp -1,d0
    beq task_idle
    mov 4,d1
2:
    mov (a1),d0
    mov d0,(a0)
    add 4,a0
    add 4,a1
    add -1,d1
    bne 2b
    mov a1,(QUEUE)
    clr d0
    ret [d2,d3,a2,a3],24

/* dly_tsk 0x60051a36 (call [d2],8) */
.global task_dly
task_dly:
    mov (LOG+16),d0
    inc d0
    mov d0,(LOG+16)
    cmp 5,d0
    bge 3f
    clr d0
    ret [d2],8
3:
    mov (LOG),a1
    mov 0xb10c4ed,d0
    mov d0,(a1)
    mov (STATE),d0
    mov d0,(4,a1)
    add 128,a1
    mov a1,(LOG)
    bra task_idle

/* memcpy 0x4700106b (call [d2,d3,a2,a3],28): d0 = n, a0 = dst, a1 = src */
.global k_memcpy
k_memcpy:
    cmp 0,d0
    beq 5f
4:
    movbu (a1),d1
    movbu d1,(a0)
    inc a0
    inc a1
    add -1,d0
    bne 4b
5:
    ret [d2,d3,a2,a3],28

/* memset 0x47001177 (call [d2,a2],8): a0 = dst, d0 = byte, d1 = n */
.global k_memset
k_memset:
    cmp 0,d1
    beq 7f
6:
    movbu d0,(a0)
    inc a0
    add -1,d1
    bne 6b
7:
    ret [d2,a2],8
