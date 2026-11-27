/* Caduceus E-M1 Mark II: the active look's S/H/L in the dormant COLOR-wheel polygon (plans/261127-1641-em1ii-color-wheel,
 * phase 02; research plans/reports/research-261127-1557-em1ii-color-wheel-osd.md).
 *
 * cw_get replaces the setting getter 0x602da802 at the 38 calls of the wheel producer 0x6097a1b5 (request kind 5):
 * profile 906, cursor 1089 / 1094 / 1095 and the 36 sector reads 925..960 (3 profiles x 12; 936 / 948 / 960 share the
 * call at 0x6097a44b). Each site keeps its 7-byte `call <rel32>,[],4`; only the rel32 points here, so we enter with the
 * getter's frame and contract:  d0 = setting id  ->  d0 = value.
 *
 * Override only when P is valid (p_get) and P_WON == 1 (the Wheel page draws, set by the page code):
 *   906                  -> 1 (profile 1: the producer then reads cursor 1089 and sectors 925..936)
 *   1089 / 1094 / 1095   -> P_WCUR (1..12 = sector, 255 = no cursor; 0 and 13..15 are rejected by the builder)
 *   925 + 12 p + k       -> sector k of axis P_WAXIS: 0 = S from P_SAT (already strength-scaled and chroma-offset as
 *                           the pipeline applies it), clamp -5..5; 1 = H (P_HUE) / 2 = L (P_LIGHT), +-15 -> round(v / 3)
 *                           (half away from zero; v / 3 never ends in .5), clamp -5..5. Sector k of the read order is
 *                           P_* index k (the producer stores read k at buffer +k, drawn at angle -30 k).
 * Anything else (P missing, P_WON != 1, another id, P_WAXIS > 2) tail-jumps into the stock getter with d0, d1, a0, a1 and
 * the stack exactly as at entry, so its own `ret [],4` returns to the site. The override returns with d1 / a0 / a1 as at
 * entry (the producer does not read them after these calls: emulator, tools/omdem1mk2_emu_color_wheel_probe.py).
 * Stores: stack only. No mul / div / setlb. Peak stack: 16 B + p_get's call.
 * Symbols from build.py: em1_set_get (0x602da802), p_get (per sd_loader build).
 */
 .am33_2
.include "p_layout.inc"

.equ SID_PROFILE, 906
.equ SID_SECT0,   925               /* profile 1 sector 0; 3 profiles x 12 ids, contiguous */
.equ N_SECT_IDS,  36
.equ SID_CUR1,    1089              /* cursor of profile 1 / 2 / 3 */
.equ SID_CUR2,    1094
.equ SID_CUR3,    1095

 .text
 .global _start
 .global cw_get
_start:
cw_get:
 add -16,sp                         /* (0,sp) = p_get's call slot; entry d1 / a0 / a1 at 4 / 8 / 12 */
 mov d1,(4,sp)
 mov a0,(8,sp)
 mov a1,(12,sp)
 call p_get,[d2,d3],12              /* a0 = P or 0; keeps d0, d1, a1 */
 cmp 0,a0
 beq cw_pass
 movbu (P_WON,a0),d1
 cmp 1,d1
 bne cw_pass
 cmp SID_PROFILE,d0
 bne 1f
 mov 1,d0
 bra cw_ret
1:
 cmp SID_CUR1,d0
 beq 2f
 cmp SID_CUR2,d0
 beq 2f
 cmp SID_CUR3,d0
 bne 3f
2:
 movbu (P_WCUR,a0),d0
 bra cw_ret
3:
 mov d0,d1
 add -SID_SECT0,d1
 cmp N_SECT_IDS,d1
 bcc cw_pass                        /* unsigned: below 925 or past 960 */
4:
 cmp 12,d1                          /* k = (id - 925) mod 12 */
 bcs 5f
 add -12,d1
 bra 4b
5:
 mov d1,a1
 movbu (P_WAXIS,a0),d1
 add a1,a0                          /* a0 = P + k */
 cmp 0,d1
 beq cw_s
 cmp 1,d1
 beq cw_h
 cmp 2,d1
 beq cw_l
 bra cw_pass                        /* d0 is still the id */
cw_s:
 movbu (P_SAT,a0),d0
 extb d0
 bra cw_clamp
cw_h:
 movbu (P_HUE,a0),d0
 bra cw_div3
cw_l:
 movbu (P_LIGHT,a0),d0
cw_div3:
 extb d0
 mov d0,d1                          /* sign */
 cmp 0,d0
 bge 6f
 not d0
 inc d0                             /* |v| */
6:
 inc d0                             /* (|v| + 1) / 3 by subtraction */
 mov 0,a1
7:
 cmp 3,d0
 blt 8f
 add -3,d0
 inc a1
 bra 7b
8:
 mov a1,d0
 cmp 0,d1
 bge cw_clamp
 not d0
 inc d0
cw_clamp:
 cmp 5,d0
 ble 9f
 mov 5,d0
9:
 cmp -5,d0
 bge cw_ret
 mov -5,d0
cw_ret:
 mov (4,sp),d1
 mov (8,sp),a0
 mov (12,sp),a1
 add 16,sp
 ret [],4

cw_pass:
 mov (4,sp),d1
 mov (8,sp),a0
 mov (12,sp),a1
 add 16,sp
 jmp em1_set_get
