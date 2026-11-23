/* Emulator-only prototype of the halation neutral-blend stubs for E-M1 II combiners 11 / 12.
 *
 * The combiner dispatcher 0x603dcd35 jumps through table 0x6053e108 ({id, handler} pairs) with a2 = ctx and the
 * dispatcher's own frame [d2,d3,a2,a3],20 live. Repointing the table words for ids 11 (0x6053e164) and 12 (0x6053e16c)
 * to these stubs is a 4-byte data edit each. A stub either jumps to the stock handler (gate word 0) or writes the same
 * bank as the stock handler with a neutral blend (gate word != 0): w = 1024, i.e. A = 1024, B = 0 for combiner 11
 * and A = 0, B = 1024 for combiner 12 (combiner 12 swaps A and B, docs/BLOOM_HALATION.md). The real gate (the job
 * halation marked) belongs to the halation patch; here it is one word at GATE so the harness can flip it.
 * Symbols from the harness: GATE, BANK_INIT (0x603dca05), C11 (0x603dd06f), C12 (0x603dd0b8), TAIL (0x603dd518).
 */
.am33_2
.text
.global _start
_start:

stub11:
    mov (GATE),d0
    cmp 0,d0
    bne 1f
    mov C11,a0
    jmp (a0)
1:
    call neutral_bank,[],4
    mov 0x04000400,d1
    mov d1,(92,a2)
    mov 1024,d1
    mov d1,(96,a2)
    clr d0
    mov d0,(136,a2)
    mov TAIL,a0            /* stock tail: mov d0,(140,a2); ret [d2,d3,a2,a3],20 */
    jmp (a0)

stub12:
    mov (GATE),d0
    cmp 0,d0
    bne 1f
    mov C12,a0
    jmp (a0)
1:
    call neutral_bank,[],4
    clr d1
    mov d1,(92,a2)
    mov d1,(96,a2)
    mov 0x04000400,d0
    mov d0,(136,a2)
    mov 1024,d0
    mov TAIL,a0
    jmp (a0)

/* Same stores as the stock handlers before their weights: a2 := bank = (8,ctx) + 7364, bank init, mode words. */
neutral_bank:
    mov (8,a2),d0
    mov 7364,a2
    add d0,a2
    mov a2,a0
    call BANK_INIT,[d2,d3],8   /* the frame the stock handlers use; the routine ends in ret [d2,d3],8 */
    mov 0x00200001,d0
    mov d0,(4,a2)
    mov 3822,d0
    mov d0,(8,a2)
    mov 0x002a0000,d0
    mov d0,(88,a2)
    mov d0,(132,a2)
    ret [],4
