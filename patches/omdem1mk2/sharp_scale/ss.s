/* E-M1 Mark II: Sharpness as a linear scale (-2 off, -1 25 %, 0 50 %, +1 75 %, +2 100 % = stock +2).
 *
 * Both stubs run inside the ISP sharpening-gain helper (stock 0x603e8b..0x603e8c97, same shape as the E-P7's
 * 0x603ab8fe, docs/SHARPENING_OFF.md). Its frame: (16,sp) = request (Sharpness = signed byte +1795),
 * (44,sp) -> job key word, (40,sp) -> output record, (50,sp)/(51,sp) = output bytes 0/1. Both stubs are reached
 * by jmp (sp unchanged) and jump back, so the frame offsets are the helper's own.
 *
 * Flat / Log jobs (key 2000 / 2001) keep the stock behaviour in every path: the helper already gives them
 * index = Sharpness + 4 on its main path, and on its alternate-table path stock adds the real Sharpness.
 *
 * ss_index replaces `movbu (1795,a0),d1; extb d1` at 0x603e8bfa (a0 = request, d0 = base[class] live):
 *   d1 = 2 for every other job, so the gain is computed as at Sharpness +2.
 * ss_scale replaces `mov (40,sp),a0; movbu (50,sp),d0` at 0x603e8c83 (d1 = final gain 0..255):
 *   d1 = d1 * k / 4 with k = Sharpness + 2 (k <= 0 -> 0, k >= 4 -> unchanged). No mul/div (audit rule).
 * Scratch: a1 in ss_index, d0/a0 in ss_scale; all three are dead or reloaded at both return points.
 */
.am33_2
.text
.global _start
_start:

ss_index:
    mov (44,sp),a1
    mov (a1),d1
    add -2000,d1
    cmp 1,d1
    bls 1f                    /* key 2000 / 2001 */
    mov 2,d1
    jmp INDEX_BACK
1:
    movbu (1795,a0),d1        /* the replaced instructions */
    extb d1
    jmp INDEX_BACK

ss_scale:
    mov (44,sp),a0
    mov (a0),d0
    add -2000,d0
    cmp 1,d0
    bls ss_done               /* Flat / Log: stock gain */
    mov (16,sp),a0
    movbu (1795,a0),d0
    extb d0
    add 2,d0                  /* k */
    cmp 4,d0
    bge ss_done               /* +2 or more: stock */
    cmp 3,d0
    bne 2f
    mov d1,d0                 /* 3/4 */
    add d1,d0
    add d1,d0
    mov d0,d1
    lsr 2,d1
    bra ss_done
2:
    cmp 2,d0
    bne 3f
    lsr 1,d1                  /* 1/2 */
    bra ss_done
3:
    cmp 1,d0
    bne 4f
    lsr 2,d1                  /* 1/4 */
    bra ss_done
4:
    clr d1                    /* -2 or less: off */
ss_done:
    mov (40,sp),a0            /* the replaced instructions */
    movbu (50,sp),d0
    jmp SCALE_BACK
