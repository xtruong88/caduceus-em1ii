/* Emulator-only allocator for the halation pass harness (tools/omdem1mk2_emu_halation_pass.py).
 * Replaces the E-M1 class allocators 0x600231fe (malloc, `call [],4`, d0 = size -> a0) and 0x6002323d (free, a0).
 * CTL words: +0 fail on the n-th malloc (0 = never), +4 mallocs, +8 frees, +12 next free address (bump, 16-aligned).
 */
.am33_2
.text
.global _start
_start:

malloc:
    mov (CTL+4),d1
    inc d1
    mov d1,(CTL+4)
    mov (CTL),a0
    mov a0,d0
    cmp d0,d1
    bne 1f
    mov 0,a0                /* the n-th malloc fails */
    ret [],4
1:
    mov (CTL+12),a0
    mov a0,d1
    add 16384,d1            /* every block takes the class-2 maximum, as a worst case for the heap */
    mov d1,(CTL+12)
    ret [],4

free:
    mov (CTL+8),d0
    inc d0
    mov d0,(CTL+8)
    ret [],4
