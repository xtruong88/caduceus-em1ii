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
.global hl_live
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
    call hl_stage,[d2,d3],12  /* d0 = Halo stage 0..3 (0 = Off) */
    cmp 0,d0
    beq hl_done
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

/* hl_stage: `call hl_stage,[d2,d3],12` -> d0 = the Halo stage 1..3, or 0 for Off. Uses d1, a0, a1 (the getter's).
 * The only read of the stage: hl_flag (marking) and hl_live (every hook that acts on a marker) both use it. */
hl_stage:
.if FORCE_STAGE
    mov FORCE_STAGE,d0
.else
    mov STAGE_KEY,d0          /* property getter(key, index 0, a0 = 0), as stock 0x604226d2 calls it */
    clr d1
    mov 0,a0
hl_stage_get:                 /* label only: route harnesses replace this 7-byte call with a fixed stage */
    call GETTER,[d2,d3],12
    cmp 3,d0
    bls 1f
    clr d0                    /* SetValue does not range-check: anything above 3 (or negative) is Off */
1:
.endif
    ret [d2,d3],12

/* hl_live: `call hl_live,[d2,d3],24` with d0 = a job's marker byte (job+35) -> d0 = 1 when it is a halation marker
 * (0xA0 | (tint - 1) << 2 | stage, stage 1..3) whose stage equals the current Halo stage, else 0. Keeps d1, a0, a1.
 * Every hook that acts on a marker asks this, so with Halo Off no job leaves the stock paths, whatever byte its
 * constructor left at params+31: constructor 0x6035d6e4 never writes it (stack garbage) and 0x60d19672 copies a
 * byte of another record there; neither passes hl_flag. Frame: (0) call slot, (4) d1, (8) a0, (12) a1. */
hl_live:
    mov d0,d2
    and 0xf0,d0
    cmp 0xa0,d0
    bne 8f
    mov d2,d3
    and 3,d3
    beq 8f
    mov d1,(4,sp)
    mov a0,(8,sp)
    mov a1,(12,sp)
    call hl_stage,[d2,d3],12
    mov (4,sp),d1
    mov (8,sp),a0
    mov (12,sp),a1
    cmp d3,d0
    bne 8f
    mov 1,d0
    ret [d2,d3],24
8:
    clr d0
    ret [d2,d3],24
