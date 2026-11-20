/* Emulator-only UI and property boundaries for the Color Creator controller. */
.am33_2
.text
.global _start
_start:
    calls (a1)
ui_return:
    nop

ui_noop:
    rets

ui_scp_format:
    ret [d2,d3,a2,a3],136

ui_scp_text:
    add 48,a0
1:
    movhu (a1),d0
    movhu d0,(a0)
    cmp 0,d0
    beq 2f
    add 2,a0
    add 2,a1
    bra 1b
2:
    ret [d2,d3,a2,a3],24

ui_get_mode:
    mov 0x80000000,d0
    ret [d2,d3],12

ui_facade:
    mov MODEL,a0
    ret [],4

ui_set:
    asl 2,d0
    mov MODEL+16,a0
    add d0,a0
    mov a1,(a0)
    clr d0
    rets

ui_get:
    asl 2,d0
    mov MODEL+16,a0
    add d0,a0
    mov (a0),d0
    mov d0,(a1)
    clr d0
    rets
