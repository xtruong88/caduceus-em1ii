/* E-M1 Mark II halation step 3: Soft Focus flag gate for ordinary colour stills (docs/OMD-EM1-II/HALATION.md).
 *
 * Hooked at the entry of the Art Effect -> job-flag converter 0x6042285e (jmp + nop over its first 7 bytes).
 * There a0 = source request (+194 capture kind, +28 -> capture record) and a1 = the job-flag word. The caller's
 * `call ...,[a2,a3],20` already saved a2/a3, and the stock code overwrites both next, so they are free here.
 *
 * Gate (owner decisions, HALATION.md): the stage (sid 961, key 0xF709[0], 0..3; anything else = Off) is not Off,
 * the shot has no Art Effect (capture+24951 == 0, so the stock Soft Focus effect keeps its own route), the picture
 * mode (capture+24203, pipeline enum) is a colour mode: < 100 (no Art Filter) and not 5 (Monotone) or 12 (MONO),
 * as the stock mono test 0x60342c32; and the capture kind is one of the two emulated ordinary-still kinds 0x1000 /
 * 0x1001 (an allow list: High Res, HDR, bracketing, Live Composite and the other kinds stay stock).
 * Only the job marker is written here. The flag word keeps its stock value: the Soft Focus flag 0x80 is set by
 * hl_route, and only for a marked job that reaches the colour-builder call it hooks, so no other builder branch of
 * the job constructor ever sees 0x80 from this patch. When the gate is closed, stock conversion proceeds.
 *
 * Built with FORCE_STAGE = 1..3 (as --defsym, test builds only) the stage is that constant instead of sid 961.
 */
.am33_2
.text
.global _start
_start:

hl_entry:
    mov a0,a3                 /* request */
    mov a1,a2                 /* flag word: the stock `mov a1,a2` */
    mov (28,a3),a0            /* capture record */
    movbu (24951,a0),d0       /* Art Effect */
    cmp 0,d0
    bne hl_done
    movbu (24203,a0),d0       /* picture mode */
    cmp 100,d0
    bcc hl_done               /* >= 100: Art Filter */
    cmp 5,d0
    beq hl_done               /* Monotone */
    cmp 12,d0
    beq hl_done               /* MONO profile mode */
    movhu (194,a3),d0         /* capture kind: 0x1000 / 0x1001 only */
    and 0xfffe,d0
    cmp 0x1000,d0
    bne hl_done
.if FORCE_STAGE
    mov FORCE_STAGE,d0
.else
    mov STAGE_KEY,d0          /* property getter(key, index 0, a0 = 0), as stock 0x604226d2 calls it */
    clr d1
    mov 0,a0
hl_stage_get:                 /* label only: route harnesses replace this 7-byte call with a fixed stage */
    call GETTER,[d2,d3],12
.endif
    cmp 0,d0
    beq hl_done
    cmp 3,d0
    bhi hl_done               /* SetValue does not range-check: anything above 3 (or negative) is Off */
    mov d0,d1                 /* job marker: params+31 -> job+35 = 0xA0 | (tint - 1) << 2 | stage, red first */
    or 0xa0,d1
    movbu d1,(19,a2)          /* a2 = params+12 */
    /* Tint from the active look (LOOKS.BIN record +47: 1 red, 2 amber, 3 warm, 4 cool); anything else keeps red.
     * The record is found as color_creator_wheel's look_rec does: card buffer when the editor applied the card,
     * else the built-in table. p_get (sd_loader) only reads memory. */
    call P_GET,[d2,d3],12     /* a0 = P or 0 */
    cmp 0,a0
    beq 7f
    movbu (30,a0),d0          /* P_ACTIVE: a colour look drives the COLOR engine */
    cmp 1,d0
    bne 7f
    movhu (16,a0),d0          /* P_LOOK */
    movhu (20,a0),d1          /* P_INIT: 2 = card */
    cmp 2,d1
    bne 5f
    mov (8,a0),a1             /* P_BUF */
    cmp 0,a1
    beq 5f
    movhu (28,a0),d1          /* P_NLOOKS */
    cmp d1,d0
    bcc 5f
    asl 6,d0
    add 64,d0
    add d0,a1
    bra 6f
5:
    and 15,d0
    asl 6,d0
    mov BUILTIN,a1
    add d0,a1
6:
    movbu (47,a1),d0          /* tint */
    add -1,d0
    cmp 4,d0
    bcc 7f
    asl 2,d0
    movbu (19,a2),d1
    or d0,d1
    movbu d1,(19,a2)
7:
hl_done:
    mov (28,a3),a3            /* replay `mov (28,a0),a3` (a3 = request) */
    mov 24951,a1              /* replay `mov 24951,a1` */
    jmp BACK                  /* 0x60422865: `add a3,a1` */
