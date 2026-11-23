/* Emulator-only boundaries for the E-M1 II bus-address mapper 0x6006888f (tools/omdem1mk2_emu_mapper.py).
 * Each stub replaces a stock routine's entry (jmp) and returns with that routine's caller frame, counting calls in
 * the word array at COUNTS: +0 lock 0x6006e9d0, +4 unlock 0x6006ea19, +8 flush 0x60068709, +12 log 0x60023188.
 * lock returns the token 0x1234 (what unlock must get back in d0); unlock records the token it got at +16.
 */
.am33_2
.text
.global _start
_start:

lock:                       /* call [d2],8 */
    mov (COUNTS),d0
    inc d0
    mov d0,(COUNTS)
    mov 0x1234,d0
    ret [d2],8

unlock:                     /* call [d2],8, d0 = token */
    mov d0,(COUNTS+16)
    mov (COUNTS+4),d0
    inc d0
    mov d0,(COUNTS+4)
    ret [d2],8

flush:                      /* call [d2,d3],16 */
    mov (COUNTS+8),d0
    inc d0
    mov d0,(COUNTS+8)
    ret [d2,d3],16

log:                        /* call [d2,a2],24: the "[exad]change_addr_err!!" print */
    mov (COUNTS+12),d0
    inc d0
    mov d0,(COUNTS+12)
    ret [d2,a2],24
