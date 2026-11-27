/* Emulator-only fwOpe API and stock-handler boundaries for the Color Creator wheel pages
 * (tools/omdem1mk2_emu_color_wheel_page.py).
 *
 * fw_iface replaces 0x6082602c (call [],4) and returns a0 = fw_obj, whose vtable has the three slots the wheel pages
 * use: +28 startVariousDraw, +32 stopVariousDraw, +48 drawC3dAsync. Each slot stub and the two stock record
 * handlers (+36 0x60e8cc69, +40 0x60e8ce8c, patched to jump here) append (id, d0, d1) to the log at FWLOG
 * (FWLOG+0 = next free entry, entries from FWLOG+16) and return with `rets` (they are entered with `calls`). */
.am33_2
.text
.global _start
_start:
    nop

.global fw_iface
fw_iface:
    mov fw_obj,a0
    ret [],4

.macro FWSTUB name, id
.global \name
\name:
    mov (FWLOG),a1
    mov \id,a0
    mov a0,(a1)
    mov d0,(4,a1)
    mov d1,(8,a1)
    add 12,a1
    mov a1,(FWLOG)
    rets
.endm

    FWSTUB fw_start, 28
    FWSTUB fw_stop, 32
    FWSTUB fw_draw, 48
    FWSTUB stock_page, 0x36
    FWSTUB stock_ok, 0x40
    FWSTUB child_cmd, 0x0C          /* a child's vtable slot 0 (sync_children_and_view sends 0x900c) */

/* em1_child_sync 0x60e4a59c is entered with `call ...,[d2,d3,a2,a3],76` (the call saves the registers and makes
 * the frame), so it returns with the matching ret. Logged as id 0x5C. */
.global child_sync
child_sync:
    mov (FWLOG),a1
    mov 0x5C,a0
    mov a0,(a1)
    mov d0,(4,a1)
    mov d1,(8,a1)
    add 12,a1
    mov a1,(FWLOG)
    ret [d2,d3,a2,a3],76

/* a child widget for the parent's +124 / +128 slots: (child) -> vtable, (vtable) -> handler */
.balign 4
.global child_obj
child_obj:
    .long child_vt
child_vt:
    .long child_cmd

.balign 4
fw_obj:
    .long fw_vtable
fw_vtable:
    .long 0, 0, 0, 0, 0, 0, 0
    .long fw_start              /* +28 */
    .long fw_stop               /* +32 */
    .long 0, 0, 0
    .long fw_draw               /* +48 */
