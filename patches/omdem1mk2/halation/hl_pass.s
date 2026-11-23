/* E-M1 Mark II halation pass (step 4d). docs/OMD-EM1-II/HALATION.md; model: tools/omdem1mk2_halation_model.py.
 *
 * The arithmetic (passes A, B, C, hl_box, hl_li, hl_gpb) is the E-P7 h1/h2 code (patches/halation/hl.s.in), instruction for
 * instruction; that version is camera-proven on the E-P7 (red / orange halo, Cb = byte 1, Cr = byte 3). What differs here:
 *   - the bus-range guard follows the E-M1 mapper 0x6006888f (tools/omdem1mk2_emu_mapper.py): 0xa0000000..0xafffffff is used
 *     directly; 0x84000000..0x9fffffff and 0xb0000000 up go through this CPU's window; anything below 0x84000000 is refused;
 *   - hl_seg opens the window itself: lock 0x6006e9d0, note the mode (0x60068b78), map (0x6006888f), work, then either restore
 *     the previous mode (0x60068b88, which flushes) or flush (0x60068709), unlock 0x6006ea19. The window is used as returned
 *     (no cached-alias trick, unlike the E-P7);
 *   - malloc / free are the E-M1 class allocators 0x600231fe / 0x6002323d (<= 16 KB per block);
 *   - one section (the 100 KB gap), so no split placements.
 *
 * hl_pass: `call hl_pass,[d2,d3,a2,a3],96`, a0 = the 88-byte record of buffer 0x1000 (+0 bus, +8 format, +10 stride in px,
 * +12 width, +14 rows, +20 / +22 zero, +72 size), d0 = tint << 4 | stage (stage 1..3, tint 1..4; else no halation / red).
 * Writes only the photo buffer, the stack and its own malloc blocks; any failed check or allocation leaves the photo untouched.
 * Locals (sp): 4 record, 8 word, 12 W, 16 H, 20 bus, 24 pitch, 28 GW, 32 GH, 36 temp, 40 grid, 44 Gp, 48 gmax, 52 tint row,
 * 56 cells / y, 60 0 = direct 1 = windowed, 64 pass (0 A, 1 C), 68 grid row / t, 72 cell row g0, 76 cell row g1.
 */
 .am33_2
 .set T_THR, 224
 .text
 .global hl_pass

hl_pass:
 mov a0,(4,sp)
 clr d1                           /* stage 1..3, tint 1..4 (else red) */
 mov d0,d2
 and 15,d2
 add -1,d2
 cmp 3,d2
 bcc 99f
 mov d0,d3
 lsr 4,d3
 add -1,d3
 cmp 4,d3
 bcs 1f
 clr d3
1:
 inc d3                           /* tint 1..4 */
 asl 4,d3
 inc d2
 or d2,d3
 mov d3,(8,sp)
 clr d0                           /* (36..44) are cleared before any exit that frees */
 mov d0,(36,sp)
 mov d0,(40,sp)
 mov d0,(44,sp)
 movhu (8,a0),d0
 cmp 0x0302,d0
 bne 99f
 movhu (20,a0),d0
 movhu (22,a0),d1
 or d1,d0
 bne 99f
 movhu (12,a0),d0
 mov d0,(12,sp)
 mov d0,d1
 add -64,d1
 cmp 8129,d1                      /* 64 <= W <= 8192, W % 4 == 0 */
 bcc 99f
 btst 3,d0
 bne 99f
 add 63,d0
 lsr 6,d0
 mov d0,(28,sp)
 movhu (10,a0),d1
 mov (12,sp),d0
 cmp d0,d1
 bcs 99f
 add d1,d1
 mov d1,(24,sp)
 movhu (14,a0),d2
 mov d2,(16,sp)
 mov d2,d0
 add -1,d0
 cmp 8192,d0                      /* 1 <= H <= 8192 */
 bcc 99f
 mov d2,d0
 add 63,d0
 lsr 6,d0
 mov d0,(32,sp)
 mul d2,d1                        /* pitch * H within the record's size */
 mov (72,a0),d0
 cmp d1,d0
 bcs 99f
 mov (a0),d0
 mov d0,(20,sp)
 add d0,d1                        /* d1 = end (exclusive) */
 cmp d0,d1
 bcs 99f                          /* wrapped */
 cmp 0x84000000,d0
 bcs 99f                          /* below the mapper's range: refuse */
 cmp 0xa0000000,d0
 bcs 2f
 cmp 0xb0000000,d0
 bcc 3f
 cmp 0xb0000001,d1                /* direct: 0xa0000000..0xafffffff */
 bcc 99f
 clr d0
 bra 4f
2:
 cmp 0xa0000001,d1                /* windowed below 0xa0000000 */
 bcc 99f
3:
 mov 1,d0                         /* windowed */
4:
 mov d0,(60,sp)
 mov (8,sp),d0                    /* gmax and tint row */
 mov d0,d1
 and 15,d0
 mov hl_gm-1,a1
 movbu (d0,a1),d0
 mov d0,(48,sp)
 lsr 4,d1
 add -1,d1
 mov d1,d0
 add d1,d1
 add d0,d1
 asl2 d1
 mov hl_tint,a1
 add d1,a1
 mov a1,(52,sp)
 mov 512,d0                       /* buffers */
 call MALLOC,[],4
 mov a0,(36,sp)
 cmp 0,a0
 beq 99f
 mov 4096,d0
 call MALLOC,[],4
 mov a0,(44,sp)
 cmp 0,a0
 beq 98f
 mov (28,sp),d0
 mov (32,sp),d3
 mul d0,d3
 mov d3,(56,sp)
 mov d3,d0
 call MALLOC,[],4
 mov a0,(40,sp)
 cmp 0,a0
 beq 98f
 jmp hl_pa
98:
 jmp hl_x98
99:
 ret [d2,d3,a2,a3],96

/* pass A */
hl_pa:                            /* a0 = grid, d3 = cells: clear it */
 clr d0
4:
 movbu d0,(a0)
 inc a0
 add -1,d3
 bne 4b
 mov d0,(64,sp)
 mov 2,d2
1:
 mov d2,d0
 lsr 6,d0
 mov (28,sp),d1
 mul d1,d0
 mov (40,sp),d1
 add d1,d0
 mov d0,(68,sp)
 mov d2,d0
 mov sp,a1
 call hl_row,[d2,d3,a2,a3],32
 cmp 0,d0
 bne 9f
 add 4,d2
 mov (16,sp),d1
 cmp d1,d2
 bcs 1b
 jmp hl_pb
9:
 jmp hl_x98

/* the common exit: free what was allocated */
hl_x98:
 mov sp,a2
 add 36,a2
 mov 3,d2
1:
 mov (a2),a0
 cmp 0,a0
 beq 2f
 call FREE,[],4
2:
 add 4,a2
 add -1,d2
 bne 1b
 ret [d2,d3,a2,a3],96

/* pass B */
hl_pb:
 clr d2                           /* rows */
1:
 mov d2,d0
 mov (28,sp),d1
 mul d1,d0
 mov (40,sp),a0
 add d0,a0
 mov (36,sp),a1
 mov 1,d1
 mov (28,sp),d0
 call hl_box,[d2,d3,a2,a3],32
 inc d2
 mov (32,sp),d0
 cmp d0,d2
 bcs 1b
 clr d2                           /* columns */
2:
 mov (40,sp),a0
 add d2,a0
 mov (36,sp),a1
 mov (28,sp),d1
 mov (32,sp),d0
 call hl_box,[d2,d3,a2,a3],32
 inc d2
 mov (28,sp),d0
 cmp d0,d2
 bcs 2b
 mov (40,sp),a0                   /* map, count */
 mov (56,sp),d3
 mov (48,sp),d2
 mov 0,a1
3:
 movbu (a0),d0
 mov d0,d1
 asl 2,d1
 add d0,d1
 asl 2,d1
 add d0,d1
 lsr 3,d1
 cmp 255,d1
 bls 4f
 mov 255,d1
4:
 mov 511,d0
 sub d1,d0
 mul d1,d0
 lsr 8,d0
 mul d2,d0
 lsr 8,d0
 cmp 16,d0
 bcs 5f
 inc a1
5:
 movbu d0,(a0)
 inc a0
 add -1,d3
 bne 3b
 mov a1,d0
 jmp hl_pc

/* hl_box: `call hl_box,[d2,d3,a2,a3],32`, a0 = u8 line, d0 = n, d1 = stride, a1 = temp (u16, n + 2): two [1 2 1] / 4 passes,
 * zero beyond the ends */
hl_box:
 mov d0,(4,sp)
 mov d1,d2
 mov 2,d0
 mov d0,(8,sp)
1:
 mov a1,a2
 clr d0
 movhu d0,(a2)
 add 2,a2
 mov a0,a3
 mov (4,sp),d3
2:
 movbu (a3),d0
 movhu d0,(a2)
 add 2,a2
 add d2,a3
 add -1,d3
 bne 2b
 clr d0
 movhu d0,(a2)
 mov a1,a2
 mov a0,a3
 mov (4,sp),d3
3:
 movhu (a2),d0
 movhu (4,a2),d1
 add d1,d0
 movhu (2,a2),d1
 add d1,d1
 add d1,d0
 add 2,d0
 lsr 2,d0
 movbu d0,(a3)
 add 2,a2
 add d2,a3
 add -1,d3
 bne 3b
 mov (8,sp),d0
 add -1,d0
 mov d0,(8,sp)
 bne 1b
 ret [d2,d3,a2,a3],32

/* hl_li: `call hl_li,[],8`, d0 = cell column (clamped to 0..GW-1), a1 = context -> d0 = (64 r0 + (r1 - r0) t) >> 6.
 * Uses d1, a0 */
hl_li:
 cmp 0,d0
 bge 1f
 clr d0
1:
 mov (28,a1),d1
 cmp d1,d0
 bcs 2f
 mov d1,d0
 add -1,d0
2:
 mov (72,a1),a0
 movbu (d0,a0),d1
 mov d1,(4,sp)
 mov (76,a1),a0
 movbu (d0,a0),d0
 sub d1,d0
 mov (68,a1),d1
 mul d1,d0
 mov (4,sp),d1
 asl 6,d1
 add d1,d0
 asr 6,d0
 ret [],8

/* hl_gpb: `call hl_gpb,[d2,d3,a2,a3],32` from hl_pass (its locals at sp + 32). Gp[p] for the pixel pairs: segment k = 0..GW
 * spans pair positions 64 k - 32 .. 64 k + 32 between cells k - 1 and k (clamped); v = 64 a + (b - a) j, step 2 (b - a) per
 * pair, g = v >> 6; 16 pairs for k = 0 (from j = 32) and k = GW, 32 otherwise: 32 GW pairs. Local (4) k. */
hl_gpb:
 mov sp,a1
 add 32,a1
 mov (44,a1),a2
 clr d0
 mov d0,(4,sp)
1:
 mov (4,sp),d0
 add -1,d0
 call hl_li,[],8
 mov d0,d3                        /* a */
 mov (4,sp),d0
 call hl_li,[],8
 sub d3,d0
 mov d0,d1
 add d1,d1                        /* step */
 asl 6,d3
 mov d3,d0                        /* v */
 mov 32,d3
 mov (4,sp),d2
 cmp 0,d2
 bne 2f
 mov d1,d2
 asl 4,d2
 add d2,d0
 mov 16,d3
 mov (4,sp),d2
2:
 mov (28,a1),a0
 cmp a0,d2
 bne 3f
 mov 16,d3
3:
 mov d0,d2
 asr 6,d2
 movbu d2,(a2)
 inc a2
 add d1,d0
 add -1,d3
 bne 3b
 mov (4,sp),d0
 inc d0
 mov d0,(4,sp)
 mov (28,a1),d1
 cmp d1,d0
 bls 1b
 ret [d2,d3,a2,a3],32

/* hl_row: `call hl_row,[d2,d3,a2,a3],32`, d0 = row, a1 = context -> d0 = 0, or 1 if a window was refused. A row that crosses a
 * 128 MB bucket edge goes in two pieces (rows and edges are 4-byte aligned, so a pixel pair never splits). */
hl_row:
 mov a1,(4,sp)
 mov (24,a1),d1
 mul d1,d0
 mov (20,a1),d1
 add d1,d0
 mov d0,(8,sp)                    /* bus */
 mov (12,a1),d2                   /* W */
 mov d0,d1
 add d2,d1
 add d2,d1
 add -1,d1
 xor d0,d1
 lsr 27,d1
 bne 1f
 mov d2,d1
 mov 0,a0
 call hl_seg,[d2,d3,a2,a3],48
 bra 9f
1:
 and 0x07ffffff,d0
 mov 0x08000000,d3
 sub d0,d3                        /* bytes to the edge */
 mov d3,(12,sp)
 lsr 1,d3
 mov d3,d1
 mov (8,sp),d0
 mov 0,a0
 call hl_seg,[d2,d3,a2,a3],48
 cmp 0,d0
 bne 9f
 mov (4,sp),a1
 mov (12,sp),d0
 mov d0,d3
 lsr 1,d3
 mov d3,a0                        /* x0 */
 mov (12,a1),d1
 sub d3,d1
 mov (8,sp),d2
 add d2,d0
 call hl_seg,[d2,d3,a2,a3],48
9:
 ret [d2,d3,a2,a3],32

/* hl_seg: `call hl_seg,[d2,d3,a2,a3],48`, d0 = bus, d1 = pixels, a0 = x0, a1 = context -> d0 = 0 / 1 (window refused).
 * Locals (4) n, (8) x0, (12) ctx, (16) token, (20) mode to restore (-1 none, -2 direct), (24) bus / window, (28) mode before */
hl_seg:
 mov d1,(4,sp)
 mov a0,(8,sp)
 mov a1,(12,sp)
 mov d0,(24,sp)
 mov (60,a1),d1
 cmp 0,d1
 bne 1f
 mov -2,d1                        /* direct: the bus address is the CPU address */
 mov d1,(20,sp)
 mov d0,a0
 bra 5f
1:
 clr d0
 call LOCK,[d2],8
 mov d0,(16,sp)
 call MODEGET,[],0
 mov d0,(28,sp)
 mov (24,sp),a0
 call MAPPER,[d2,d3,a2,a3],28
 cmp 0,a0
 bne 2f
 mov (16,sp),d0
 call UNLOCK,[d2],8
 mov 1,d0
 ret [d2,d3,a2,a3],48
2:
 mov a0,(24,sp)
 call MODEGET,[],0
 mov (28,sp),d1
 cmp d1,d0
 bne 3f
 mov -1,d1                        /* same mode as before: flush only */
3:
 mov d1,(20,sp)
 mov (24,sp),a0
5:
 mov (12,sp),a1
 mov (64,a1),d0
 cmp 0,d0
 bne 30f
 mov (68,a1),a1                   /* A: grid row; d1 = x, a2 = end x */
 mov (8,sp),d1
 mov (4,sp),a2
 add d1,a2
2:
 movbu (a0),d0
 add -T_THR,d0
 ble 3f
 lsr 2,d0
 mov d1,d2
 lsr 6,d2
 movbu (d2,a1),d3
 add d0,d3
 cmp 248,d3
 bls 4f
 mov 248,d3
4:
 movbu d3,(d2,a1)
3:
 add 4,a0
 add 2,d1
 cmp a2,d1
 bcs 2b
 bra 40f
30:
 mov (44,a1),a2                   /* C: a1 = Gp + x0 / 2, a2 = its end, a3 = tint row */
 mov (52,a1),a3
 mov (8,sp),d0
 lsr 1,d0
 mov a2,a1
 add d0,a1
 mov (4,sp),d0
 lsr 1,d0
 add a1,d0
 mov d0,a2
31:
 movbu (a1),d3
 inc a1
 cmp 0,d3
 beq 39f
 movbu (a0),d0                    /* Y0; d2 = w0 g */
 mov 255,d2
 sub d0,d2
 mul d3,d2
 mov (a3),d1
 mul d2,d1
 asr 16,d1
 add d1,d0
 movbu d0,(a0)
 movbu (2,a0),d1                  /* Y1 */
 mov 255,d0
 sub d1,d0
 mul d3,d0
 mov (a3),d1
 mul d1,d0
 asr 16,d0
 movbu (2,a0),d1
 add d0,d1
 movbu d1,(2,a0)
 mov (4,a3),d0                    /* C0 = Cb */
 mul d2,d0
 asr 16,d0
 movbu (1,a0),d1
 add d0,d1
 cmp 0,d1
 bge 32f
 clr d1
32:
 cmp 255,d1
 ble 33f
 mov 255,d1
33:
 movbu d1,(1,a0)
 mov (8,a3),d0                    /* C1 = Cr */
 mul d2,d0
 asr 16,d0
 movbu (3,a0),d1
 add d0,d1
 cmp 0,d1
 bge 34f
 clr d1
34:
 cmp 255,d1
 ble 35f
 mov 255,d1
35:
 movbu d1,(3,a0)
39:
 add 4,a0
 cmp a2,a1
 bcs 31b
40:
 mov (20,sp),d0
 cmp -2,d0
 beq 43f                          /* direct: no window, no lock */
 cmp -1,d0
 bne 41f
 call FLUSH,[d2,d3],16
 bra 42f
41:
 call MODESET,[d2,d3,a2],20       /* restore the previous mode (flushes first) */
42:
 mov (16,sp),d0
 call UNLOCK,[d2],8
43:
 clr d0
 ret [d2,d3,a2,a3],48

/* pass C */
hl_pc:                            /* d0 = cells with g >= 16: none, or 3 count > cells: no halation */
 cmp 0,d0
 beq 9f
 mov d0,d1
 add d0,d0
 add d1,d0
 mov (56,sp),d1
 cmp d1,d0
 bhi 9f
 mov 1,d0
 mov d0,(64,sp)
 clr d0
 mov d0,(56,sp)
1:
 clr d1                           /* y -> gy0, t (68), gy1; gy0 <= GH - 1 since y < H <= 64 GH */
 mov (56,sp),d0
 add -32,d0
 blt 2f
 mov d0,d1
 and 63,d1
 lsr 6,d0
 bra 3f
2:
 clr d0
3:
 mov d1,(68,sp)
 mov (32,sp),d1
 add -1,d1
 mov d0,d3
 inc d3
 cmp d1,d3
 bls 5f
 mov d1,d3
5:
 mov (28,sp),d1
 mul d1,d0
 mov (40,sp),a0
 add d0,a0
 mov a0,(72,sp)
 mul d1,d3
 mov (40,sp),a1
 add d3,a1
 mov a1,(76,sp)
 mov (28,sp),d3                   /* any glow in either cell row? */
 clr d0
6:
 movbu (a0),d1
 or d1,d0
 movbu (a1),d1
 or d1,d0
 inc a0
 inc a1
 add -1,d3
 bne 6b
 cmp 0,d0
 beq 8f
 call hl_gpb,[d2,d3,a2,a3],32
 mov (56,sp),d0
 mov sp,a1
 call hl_row,[d2,d3,a2,a3],32
 cmp 0,d0
 bne 9f
8:
 mov (56,sp),d0
 inc d0
 mov d0,(56,sp)
 mov (16,sp),d1
 cmp d1,d0
 bcs 1b
9:
 jmp hl_x98

/* tables */
 .balign 4
hl_tint:                          /* dY, dCb, dCr per tint 1..4: red, amber, warm, cool (E-P7 camera-proven order) */
 .long 48, -24, 72
 .long 56, -48, 48
 .long 56, -36, 30
 .long 48, 48, -20
hl_gm:                            /* gmax per stage 1..3 */
 .byte 112, 176, 240
