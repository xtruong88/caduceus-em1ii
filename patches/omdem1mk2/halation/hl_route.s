/* E-M1 Mark II halation step 4: route marked colour stills through the Art work list and run the pass there.
 * docs/OMD-EM1-II/HALATION.md "Step 4"; reports plans/reports/research-261123-0838-em1ii-halation-job-marker.md and
 * research-261123-1709-em1ii-art-route.md.
 *
 * The job marker is job+35 (= params+31, written by hl_flag): 0xA0 | (tint - 1) << 2 | stage, stage 1..3, tint 1..4.
 * Stock never writes or reads that byte (tools/omdem1mk2_emu_job_marker.py), so a job without our mark keeps stock paths.
 *
 *   hl_route  the colour-builder call at 0x603900ec now calls here (frame [],4, a0 = job): a marked job gets the Soft
 *             Focus flag 0x80 in its flag word (job+16) here, the only place the patch sets it, and goes to the Art
 *             builder 0x60391c1c, which with that flag builds the Soft Focus list; all others go to the stock 0x603a3c70.
 *   hl_ob     the work-list word for the Soft Focus blur 0x60398e6f (immediate at 0x60393a54) now names this. It runs as
 *             a `calls` item with a0 = job, right after development has written and waited for the full-size 0x0302
 *             record 0x1000; for a marked job it runs hl_pass on that record, then continues into 0x60398e6f with sp, the
 *             return slot and a0 exactly as on entry.
 *   hl_c11 /  combiner 11 / 12 table words (0x6053e164 / 0x6053e16c): for a marked job (request - 11329 = job+35) the
 *   hl_c12    blend is neutral (w = 1024: 11 -> A 1024 / B 0, 12 -> A 0 / B 1024), so the blend output is record 0x1000
 *             with the halation; any other job runs the stock handler. "Marked" needs the marker with a stage 1..3 and
 *             flag 0x80 at job+16 (request - 11348), which only hl_route sets on a marked job.
 */
 .am33_2
 .text

hl_route:
 movbu (35,a0),d0
 and 0xf0,d0
 cmp 0xa0,d0
 beq 1f
 jmp PLAIN_BUILDER
1:
 mov (16,a0),d0                   /* flag word: add Soft Focus for this job only */
 or 0x80,d0
 mov d0,(16,a0)
 jmp ART_BUILDER

hl_ob:
.if NO_PASS                       /* diagnostic build: Art route + neutral blend, no pass (camera A/B of the route) */
 jmp BLUR
.endif
 movm [d2,d3,a2,a3],(sp)
 add -8,sp
 mov a0,(4,sp)
 movbu (35,a0),d2                 /* marker */
 mov d2,d0
 and 0xf0,d0
 cmp 0xa0,d0
 bne 9f
 mov 4096,d0                      /* record 0x1000 */
 call BUFIDX,[d2],4
 exthu d0
 cmp 48,d0
 bcc 9f
 mov 88,d1
 mul d1,d0
 mov (4,sp),a0
 add 6592,a0
 add d0,a0                        /* the record */
 mov d2,d1                        /* d0 = tint << 4 | stage */
 lsr 2,d1
 and 3,d1
 inc d1
 asl 4,d1
 mov d2,d0
 and 3,d0
 or d1,d0
 call hl_pass,[d2,d3,a2,a3],96
9:
 mov (4,sp),a0
 add 8,sp
 movm (sp),[d2,d3,a2,a3]
 jmp BLUR

/* combiner stubs: a2 = ctx, the dispatcher's frame [d2,d3,a2,a3],20 live */
hl_c11:
 call hl_marked,[],4
 cmp 0,d0
 bne 1f
 mov C11,a0
 jmp (a0)
1:
 call hl_bank,[],4
 mov 0x04000400,d1
 mov d1,(92,a2)
 mov 1024,d1
 mov d1,(96,a2)
 clr d0
 mov d0,(136,a2)
 mov TAIL,a0                      /* stock tail: mov d0,(140,a2); ret [d2,d3,a2,a3],20 */
 jmp (a0)

hl_c12:
 call hl_marked,[],4
 cmp 0,d0
 bne 1f
 mov C12,a0
 jmp (a0)
1:
 call hl_bank,[],4
 clr d1
 mov d1,(92,a2)
 mov d1,(96,a2)
 mov 0x04000400,d0
 mov d0,(136,a2)
 mov 1024,d0
 mov TAIL,a0
 jmp (a0)

/* hl_marked: `call hl_marked,[],4`, a2 = ctx -> d0 = 1 when the job behind ctx+4 is marked, else 0. Uses d0, a0 */
hl_marked:
 mov (4,a2),a0
 cmp 0,a0
 beq 1f
 movbu (-11329,a0),d0             /* request = job+11364, so job+35 */
 btst 3,d0                        /* stage 1..3 */
 beq 1f
 and 0xf0,d0
 cmp 0xa0,d0
 bne 1f
 movbu (-11348,a0),d0             /* job+16, low byte of the flag word */
 btst 0x80,d0
 bne 2f
1:
 clr d0
 ret [],4
2:
 mov 1,d0
 ret [],4

/* hl_bank: `call hl_bank,[],4`: the stock handlers' stores before their weights; a2 := bank = (8,ctx) + 7364 */
hl_bank:
 mov (8,a2),d0
 mov 7364,a2
 add d0,a2
 mov a2,a0
 call BANK_INIT,[d2,d3],8
 mov 0x00200001,d0
 mov d0,(4,a2)
 mov 3822,d0
 mov d0,(8,a2)
 mov 0x002a0000,d0
 mov d0,(88,a2)
 mov d0,(132,a2)
 ret [],4
