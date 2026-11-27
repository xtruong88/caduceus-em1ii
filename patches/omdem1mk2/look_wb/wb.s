/* Caduceus E-M1 Mark II: WB fine-tune from the active Color Creator look (docs/OMD-EM1-II/ARCHITECTURE_AND_MEMORY_MAP.md
 * §7.8; E-P7 design: docs/WB_PATCH.md).
 *
 * wb_get replaces the property getter 0x6005e6cf at the 14 image-pipeline reads of the WB fine-tune arrays (A-B key
 * 0x84F9, G-M key 0x9679): 12 in the capture block 0x6033a209..0x6033a58a and the compact slot pair 0x60343734/47.
 * The RAW-development pair stays stock. Each site keeps its 7-byte `call <rel32>,[d2,d3],12`; only the rel32 points
 * here, so we enter with the getter's frame and contract:  d0 = key, d1 = idx, a0 = 0  ->  d0 = value.
 *
 * The look's value is returned only when ALL hold (wb_val):
 *   - key is A-B or G-M;
 *   - P is valid, a colour look is active (P_ACTIVE) and the live picture mode (raw 0x9481) equals P_CCMODE, the
 *     same gate as cc_sel;
 *   - WB category (key 0x8121) is not 3 (CWB): a colour temperature the user chose stays as set, as on the E-P7;
 *   - the look's record (built-in table or the loaded LOOKS.BIN) has wb flag +25 bit0 set and bit7 clear, and both
 *     a_b (+26) and g_m (+27) are in -7..7.
 * Otherwise wb_pass tail-jumps into the stock getter with the original d0/d1/a0 on the site's frame, so the stock path
 * is the stock getter on an identical frame (its own `ret [d2,d3],12` returns to the site).
 *
 * Registers: the getter returns the array's s8 sign-extended; so does the override. The override leaves d1 = idx like
 * the getter; a0 is the record pointer instead of the property data pointer (every site rewrites a0 before reading
 * it: the capture sites run natively to the segment's join in tools/omdem1mk2_emu_look_wb.py, the compact slot pair
 * reloads `mov 0,a0` right after each call); a1 and MDR equal stock because wb_val's last call is a real getter call
 * (the getter leaves a1 / MDR independent of the key, emulator 2026-11-27). No mul/div/setlb.
 * Peak stack: +28 B over stock (wb_val's 16-B frame + the nested getter call's 12-B frame).
 * Symbols from build.py: em1_getter, p_get (per sd_loader build), builtin_looks.
 */
 .am33_2
.include "p_layout.inc"

.equ KEY_A,      0x84F9
.equ KEY_G,      0x9679
.equ KEY_PMODE,  0x9481             /* live picture mode (sid 111), raw */
.equ KEY_WBCAT,  0x8121             /* WB category (sid 9): 1 preset, 2 one-touch, 3 CWB, 4, other = Auto */
.equ WB_CWB,     3
.equ N_BUILTIN,  16
.equ R_WBFLAG,   25                 /* look record: wb flag, a_b, g_m (make_looks_bin.py) */
.equ R_AB,       26
.equ R_GM,       27

 .text
 .global _start
 .global wb_get
_start:
wb_get:
 mov d0,d2                          /* key (d2/d3 are saved in the site's frame) */
 mov d1,d3                          /* idx */
 cmp KEY_A,d0
 beq 1f
 cmp KEY_G,d0
 bne wb_pass
1:
 call wb_val,[d2,d3,a2],16          /* d0 = key -> d1 = 1 and d0 = value, or d1 = 0 */
 cmp 0,d1
 beq wb_pass
 mov d3,d1                          /* d1 = idx, as the stock getter leaves it */
 ret [d2,d3],12

wb_pass:
 mov d2,d0                          /* original key */
 mov d3,d1                          /* original idx */
 mov 0,a0                           /* every redirected site passes a0 = 0 (§7.8) */
 jmp em1_getter                     /* stock getter on the site's frame */

/* wb_val: d0 = key (A-B or G-M), `call wb_val,[d2,d3,a2],16`.
 * -> d1 = 1, d0 = the look's value (-7..7, sign-extended); or d1 = 0 when the look does not apply. */
wb_val:
 mov d0,d3                          /* key */
 call p_get,[d2,d3],12
 cmp 0,a0
 beq 9f
 mov a0,a2                          /* a2 = P (uncached; the getter keeps a2) */
 movbu (P_ACTIVE,a2),d0
 cmp 0,d0
 beq 9f
 mov (P_CCMODE,a2),d0
 cmp 0,d0
 beq 9f
 mov KEY_PMODE,d0
 clr d1
 mov 0,a0
 call em1_getter,[d2,d3],12
 mov (P_CCMODE,a2),d1
 cmp d1,d0
 bne 9f
 mov KEY_WBCAT,d0
 clr d1
 mov 0,a0
 call em1_getter,[d2,d3],12
 cmp WB_CWB,d0
 beq 9f
 movhu (P_LOOK,a2),d0
 movhu (P_INIT,a2),d1
 cmp LOOK_SOURCE_CARD,d1
 beq 2f
 cmp 1,d1                           /* built-in */
 bne 9f
 cmp N_BUILTIN,d0
 bcc 9f
 asl 6,d0
 mov builtin_looks,a0
 add d0,a0
 bra 3f
2:
 movhu (P_SD_STATE,a2),d1
 cmp 1,d1                           /* LOOKS.BIN loaded */
 bne 9f
 movhu (P_NLOOKS,a2),d1
 cmp d1,d0
 bcc 9f
 asl 6,d0
 add 64,d0
 mov (P_BUF,a2),a0
 add d0,a0                          /* card record: buf + 64 + 64 i */
3:
 movbu (R_WBFLAG,a0),d0
 and 0x81,d0
 cmp 1,d0                           /* bit0 = shift on, bit7 must be 0 (0xFF = erased) */
 bne 9f
 movbu (R_AB,a0),d0
 add 7,d0
 extbu d0
 cmp 15,d0
 bcc 9f                             /* a_b outside -7..7 */
 movbu (R_GM,a0),d1
 add 7,d1
 extbu d1
 cmp 15,d1
 bcc 9f                             /* g_m outside -7..7 */
 cmp KEY_A,d3
 beq 4f
 mov d1,d0
4:
 add -7,d0                          /* -7..7, sign-extended like the getter's s8 */
 mov 1,d1
 ret [d2,d3,a2],16
9:
 clr d1
 ret [d2,d3,a2],16
