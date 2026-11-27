# Research: E-P7-style COLOR wheel (hue ring + 12-vertex polygon) on E-M1 II 3.70

Date 2026-11-27 · branch docs/huong-dan-em1ii · context: `brainstorm-261127-1557-em1ii-color-wheel.md`
Labels: [V] run in emulator, [S] static reading (objdump), [I] inference. Nothing on camera. No patch/webapp/look-format edits.

## Verdict: FEASIBLE (the complete stock path exists as dead code; needs a trigger + value feed, no new drawing code)

The E-M1 II 3.70 image has the whole E-P7 Color-Profile wheel pipeline: producer (reads profile + 12 sector settings),
C3d client builder (-5..+5 → codes 0..10), C3d API command, draw task message and the OpenVG polygon/tick renderer,
geometry byte-identical in size/constants to E-P7/PEN-F. It is unreachable only because the GUI screen→C3d type
table has no entry for type 4 (kind 5). Producer, builder and renderer were run in the emulator and draw a 12-vertex
polygon whose radii follow the sector values. The OSD-bitmap fallback is not needed for the polygon itself.

Supporting context [I]: the user's reference photo is from an E-M10 Mark I (2014, no stock COLOR profiles), so a mod
draws this wheel on an older body. That fits the finding that the service is a shared platform component (it was
found independently here, so this only supports the verdict).

## Chain (E-M1 II addresses; E-P7 equivalents from docs)

| Stage | E-M1 II 3.70 | E-P7 1.1 (docs) | Label |
|---|---|---|---|
| GUI screen → C3d type table (6 entries × 8 B: u16 screen, u32 type) | **0x612c373c**, read by 0x60f09d63 (loop `cmp 6`), calls API slot +28 | – | [S] |
|  entries | 0xfff8→0, 0xfff4→1, 0xfff5→2, 0xfff6→3, 0xffea→6, 0xffeb→7. **No 4 (COLOR wheel) and no 5** | – | [S] |
| fwOpe API "start various draw" (vtable 0x60afa050 slot 7 = +28, id 0x10308) | 0x60826587 → **0x607db538** (type 0..7 → fwOpe+424 kind 1..8; **type 4 → kind 5**) | dispatcher 0x60798348 types 0–13 | [S] |
| `fwOpe::drawC3dAsync` (string 0x60acaede) | 0x607dc8f4 (only type 5 accepted) → 0x607dc9a5 (kinds 1..8 incl. 5) → posts GUI msg **12987 (0x32bb)** via ctor 0x607b7920 (call at 0x607dce28) | 0x60798348 / 0x607989a0 | [S] |
| GUI message handler | 0x60941de7: msg 12987 → view vtable slot **+1040** (0x60941e2e) | – | [S] |
| Producer (E-P7 "receiver"/+4972 analog; switch on request kind) | **0x6097a1b5**, in 10 view vtables (0x60b68cf0, 0x60b6b4d8, 0x60b76874, 0x60b79100, 0x60b7c96c, 0x60b7f258, 0x60b81be4, 0x60b84e0c, 0x60b8770c, 0x60b8be1c) | 0x609394be at vtable +1056; 10 vtables | [S] |
|  kind 1 (Color Creator) | reads 617 hue, 618 vivid (4 B) | – | [S] |
|  **kind 5 (COLOR wheel)** | profile = setting **906** (1..3); profile 1: cursor 1089 + sectors 925..936; 2: 1094 + 937..948; 3: 1095 + 949..960; buffer 12 × s8 + cursor byte; cursor fixup 0x607ac89e | setting 1648, row table 0x60b40c4c (4 profiles) | [V] |
| C3d client (kind → builder → API command) | 0x6031629a (async; 0x60316110 sync): kind 1→cmd 6 (0x60310221), 2–4→cmd 1, **5→cmd 11 (0x603103ea)**, 6→16, 7→21, 8→26 | 0x60835016 → 0x602e251a → 0x602dd8aa (kind 1) | [S] |
| Value-code converter | **0x603103ea**: s8 −5..+5 → code 0..10 (loop at 0x6031046a, jump table 0x604fa9e8), cursor via table 0x604fa968 | 0x602dcdb3 / range_wheel_encode 0x602dce4c | [V] |
| C3d API task (mailbox 0x60041124, jump table 0x61004780, 29 cmds) | 0x60cae1bf; cmd 10 opens state 3, **cmd 11 = copy 13 B → draw msg 5** (0x60cae3a6), cmd 5/6 = Color Creator (state 2, 4 B → draw msg 4) | – | [S] |
| C3d draw task (mailbox 0x6004130e) | 0x60cac29b: msg 1 open (sub 1..6 alloc), 3→0x60cad03b, **4→0x60cad14f (Color Creator ring+cursor)**, **5→0x60cad39d (COLOR polygon)**, 6→0x60cad723, 7→0x60cad928, 8→0x60cada3a | – | [S] |
| Polygon/tick renderer | **0x60cad39d** (frame add −368 at 0x60cad39d, unframe 0x60cad71c, span 0x37f = E-P7) | 0x60c50ce3..0x60c51062 | [V] |

Geometry bytes (E-P7 → E-M1 II, constant shift +0x5c6ba inside the renderer): draw_frame 0x60c50ce3→**0x60cad39d**
`fafe90fe`; polygon_step 0x60c50dcb→**0x60cad485** `f90009`; polygon_origin 0x60c50dd6→**0x60cad490** `fccc0000b841`;
ticks_step 0x60c50f54→**0x60cad60e** `fccc00001041`; ticks_origin 0x60c50f62→**0x60cad61c**; ticks_y 0x60c50f7d→0x60cad637
`fac0ec00`; tangent_x →0x60cad640 `fac01801`; tangent_y →0x60cad649 `fac04401`; draw_y →0x60cad69b `fad0ec00`; selected_y
→0x60cad6f7 `fad1ec00`; unframe 0x60c51062→0x60cad71c `fafe7001` [S]. `range_wheel_encode` bytes `a0fbc040a005…` do not
match (same logic, long-branch encoding `a0fbc205…` at 0x6031046d) [S].

Renderer is OpenVG (lib strings `vguPolygon`/`vguLine`/… at 0x613b9ae0): vgSetfv 0x61396936 (clear colour 0x1121),
vgClear 0x613970dd, vgSeti 0x6139691a (matrix mode 0x1100/0x1400/0x1401), vgLoadIdentity 0x6139683a, vgTranslate
0x61396898, vgRotate 0x613968e6, point transform 0x61396868, path append 0x613971ff (13 pts), vgSetPaint 0x6139738e,
vgDrawPath 0x613972fd (fill|stroke), stroke width vgSetf 0x613968fe(0x1110); labels/marks via 0x60cadf96 [S, names I].
Handles at 0x626537b0..0x626537ec.

## Emulator evidence [V] — `tools/omdem1mk2_emu_color_wheel_probe.py` (fixture `tools/emu_fixtures/em1_c3d_wheel_stubs.s`)

Run: `wsl -d Ubuntu-24.04 -u root --cd /mnt/d/em1_ii/caduceus -- python3 tools/omdem1mk2_emu_color_wheel_probe.py`
(stock image only; ends `OK`). Each stage was run on two inputs, and the output follows the input:

1. Producer 0x6097a1b5, request kind 5: profile 1 / all 0 / cursor 3 → client kind 5, buffer `0×12 + 3`; profile 2 /
   `[5,-5,3,-3,1,-1,0,2,-2,4,-4,5]` / cursor 7 → the same 12 values + 7. It reads exactly 906, the profile's 12 sector ids
   and cursor id (getter stub serves only what is asked).
2. Builder 0x603103ea: `[0]*12`, cursor 255 → codes `5×12`, 255; the mixed vector → `[10,0,8,2,6,4,5,7,3,9,1,10]`,
   cursor 3→2; err 0.
3. Renderer 0x60cad39d: codes `5×12`/cursor 255 → 12 vertices all r=68, 30° apart, path-append 13 pts, cursor/tick
   branch **skipped** (109 calls); mixed codes/cursor 3 → radii `113,23,95,41,77,59,68,86,50,104,32,113` (= 23 + 9·code),
   tick branch **taken** (11 tick marks 0x61397280, 161 calls). Vertices on a 256×256 canvas, centre (128,128).

[V] also: the validator (`omdem1mk2_emu_validator.py --sid …`) has 906 = 0..3 and 925..960 = −5..+5 (36 = 3 profiles × 12).
Cursor ids 1089/1094/1095 have no list values (count 0).

Emulator limits (stated plainly):
- Fixture boundaries: OpenVG API, C3d trace helpers, error log 0x60062a37, label/flush 0x60cadf96/0x60cac8fc, setting
  getter 0x602da802, client entry 0x6031629a (stage 1). No pixels: the VG calls are logged, not rasterised.
- Soft-float helpers use UDF coprocessor ops the engine does not model; the harness stops on each and performs it in
  Python: udf02/03/04/05 = fadd/fsub/fmul/fdiv, f9e040 = int→float [S from use: constants 23.0, 30.0],
  `udf00 9,d0` at 0x60cad485 = ×9 [I, E-P7 map name "polygon_step"]. Rounding 0x60cae052 is stubbed to identity.
  The 23 + 9·code radius and 30° step therefore rest partly on that model; the branch structure, value→vertex order,
  13-point path and cursor branch are stock code.
- Not emulated: the RTOS mailboxes (fwOpe → GUI msg 12987 → view → client → API task → draw task), the GUI table
  path 0x60f09d63, surface open/allocation, and compositing to the screen [S only].

## Fallback (OSD bitmap + 12 dots): not needed

Kept only if the C3d surface can't be shown over Color Creator. ASPECT.md's bitmap-table mechanism could show a static
ring plus 12 icon dots, but there are no lines between vertices. `OSDControl::drawLine`/`drawRect`/`drawDot` exist
(strings 0x60aaba37..0x60aaba60, table ref 0x60277628) but are unmapped [S]. Lines would come from that or from the C3d path.

## Implementation sketch + effort/risk

1. Trigger [S]: from the Caduceus Color Creator page code, call fwOpe API slot +28 (0x60826587, d0 = type 4, d1 as
   0x60f09dfb passes 1/2, a1 = arg) on a "Sector" page, and type 0 again to go back. Or repoint/extend the table at
   0x612c373c (no free room after it: strings follow; the count is an immediate `cmp 6` at 0x60f09e12).
   Color Creator already uses this service (type 0 → kind 1 → draw msg 4), so the BGr surface is on screen there [I].
2. Value feed [S]: hook the producer's getter calls (0x602da802 for 906/925..960/cursor), like E-P7 test13 `ed_poly`,
   to serve the look's S/H/L from P. Or write the dormant settings 906/925..960 (validator accepts them [V]).
3. Cursor: the byte → table 0x604fa968 (1..11 valid?) [S]. Mapping to sector index needs one more emulator pass.
4. Hue ring / labels: msg 5 draws polygon + 12 labels (0x60cadf96 ids 0xd3..) + ticks. Whether the hue ring is drawn by
   the same message or by the surface background is not established; on the E-M1 II's Color Creator the ring is msg 4.

Effort (rough): 2–4 sessions of firmware work plus emulator harness extension (fwOpe → draw-task flow), and 2–3 camera
builds. Risk is medium: the drawing is stock, but the open/close state machine (API state 2 vs 3: cmd 5/10 open, state
checks `0xa26da4f4`), surface placement over Color Creator's OSD, and redraw timing are camera-only questions. Low
risk of drawing glitches from geometry, because it is unmodified stock code.

## Open questions
- Where does the type-4 surface appear (position/size), and does the Color Creator OSD cover it? Camera-only.
- Can kind 5 run while Color Creator's kind 1 surface is open (state 2 vs 3), or does it need a close/open in sequence?
  This needs fwOpe 0x607db538 / 0x607daf0a / 0x607dc7e4 and API task state emulation.
- Does msg 5 draw the coloured hue ring (E-P7 look), or only polygon + labels + ticks? Check the 0x60cadf96 label ids
  0xd3..0xde and bitmap resources.
- Meaning of the 3 E-M1 II profiles (906 = 1..3, 3×12 sectors) vs E-P7's 4. Are they dormant or used by any stock mode?
- Exact UDF semantics (the ×9 step); confirm with one camera draw or with the IDA notes in `external/oly_fw_analysis/docs/tooling/ida`.

(Answers to the open questions above are in Phase 01 results below.)

## Phase 01 results (2026-11-27)

Harness: `tools/omdem1mk2_emu_color_wheel_probe.py` (stages 1–7), fixture `tools/emu_fixtures/em1_c3d_wheel_stubs.s`
(new: mailbox receive `task_rcv` with a command queue, `dly_tsk` with blocked detection, memcpy/memset at
0x4700106b/0x47001177, RTOS send/post loggers). Stock image only. It ends `OK: phase 01 flow checks`.

### GATE: CONTINUE, with a strict stop-then-start sequence

Opening the wheel while Color Creator's surface is open **hangs the C3d API task** [V]. The stock GUI never does this:
it always stops the old type before it starts a new one [S]. The safe sequence, which emulates cleanly at API-task
level [V], is:

1. **Enter the Wheel page:** fwOpe `stopVariousDraw(type 0)` (API vtable 0x60afa050 slot +32 = 0x60826201, id
   0x10309) closes kind 1 (API cmd 7). Then `startVariousDraw(type 4)` (slot +28 = 0x60826587) opens kind 5 (cmd 10).
   Then a draw request (`drawC3dAsync`, slot +48, d0 = 5) runs the producer and sends cmd 11 (draw msg 5).
2. **Leave the Wheel page:** `stopVariousDraw(type 4)` sends cmd 12, then `startVariousDraw(type 0)` sends cmd 5,
   then a draw request sends cmd 6 (draw msg 4).
3. **d1:** pass the same value the GUI passes (1, or 2 on the screens tested at 0x60f09dc3/0x60f09e8d).

### (a) Kind 5 opened while kind 1 is open

- **API task** [V, stage 6, scenario 1]: cmd 5 → state 2 (draw msg 1 sub 2), cmd 6 → draw msg 4, then cmd 10 →
  **blocked**. Every open command (0/5/10/15/20/25) polls `dly_tsk(1)` until state 0xa26da4f4 = 0. Only this task
  clears the state (all 30 references to the word are inside 0x60cae1bf [S]), and the close it would need is queued
  behind the blocked open, so the wait never ends. The C3d API stops serving. Whether the GUI/fwOpe caller also hangs
  depends on whether the client send 0x602f9583 waits for a reply [S: not followed].
- **fwOpe** [S]: `startVariousDraw` 0x607db538 writes the new kind to fwOpe+424 and sends the open (0x60315f3f). It
  never closes the old kind. Its 8 cases call 0x607daf0a, 0x607dc7e4, 0x607dcfa8 and 0x60315f3f, and none of them
  reaches the close client 0x603164de (whose only caller is 0x607dbc15).
- **After the overwrite** [V, scenario 1b]: a later close sends cmd 12 while the state is 2. The API task logs a
  state-mismatch error and keeps state 2. Draw cmd 11 is silently ignored. Only cmd 7 (the kind-1 close) clears the
  state. Since fwOpe+424 no longer says kind 1, fwOpe can't send that close. **A close of kind 1 is required first.**

### (b) Close and reopen calls

| Step | fwOpe entry | Client | API cmd → effect | Label |
|---|---|---|---|---|
| stop current | slot +32 0x60826201 → 0x607daddc(type) → 0x607db66a → **0x607dbc05** (close by fwOpe+424) | 0x603164de: kind 1→7, 2–4→2, 5→12, 6→17, 7→22, 8→27 | 7/12: state → 0; post mbx 0x8e (arg 5) and draw mbx (arg 2) | [V] 0x607dbc05 sends cmd 7 for +424 = 1 and cmd 12 for +424 = 5, then sets +424 = 0xffff; API task [V]; the 0x607daddc → 0x607db66a part [S] |
| start new | slot +28 0x60826587 → **0x607db538**(type): 0→kind 1 … **4→kind 5** … 7→8 | 0x60315f3f: kind 1→5, 2–4→0, 5→10, 6→15, 7→20, 8→25 | 5/10: wait for state 0, then state = 2/3 and draw msg 1 (sub = state) | [V] client and API task; [S] 0x607db538 |
| draw | slot +48 0x6082664f → 0x607dc8f4(type 5) → GUI msg 12987 → view +1040 → producer 0x6097a1b5 → 0x6031629a | kind 1→cmd 6, kind 5→cmd 11 | 6 → msg 4 (4 B); 11 → msg 5 (13 B) | [V] producer/builder/API; [S] message delivery |

Scenario 2 [V] (cmds 5, 6, 7, 10, 11, 12, 5, 6): states 0→2→2→**0**→3→3→**0**→2→2, with draw msgs 1(sub 2), 4, 1(sub 3),
5 (payload exact), 1(sub 2), 4, and no block or error.

The stock GUI does the same stop-then-start [S]: 0x60f09d40 compares the screen with 0x61fbfbf4, calls 0x60f09e18
(slot +32 with the old type, clears 0x61fbfbf4), and then calls slot +28 with the new type from table 0x612c373c.

### (c) Cursor byte → sector [V, stage 4]

The cursor setting (1089/1094/1095) holds the sector **1..12**. The builder sends code = sector − 1 (0..11). 255
means no cursor: the renderer skips the tick scale and the selected-sector marker [V]. A value of 0 or 13..15 goes to
the error handler 0x60310680, which logs an error and does not write byte 12 [V/S]. Table 0x604fa968 has 16 entries
of (value, handler): 1..12 and 0xff valid, 0 and 13–15 invalid.

### (d) Hue ring source

Both messages draw through 0x60cadf96 (image set, id). It looks up atlas rectangles: set table 0x61003b38, rects at
0x61003250 (all in atlas 0, 512×512).

| Message | Images drawn [V, stage 7] | Atlas rects [S] |
|---|---|---|
| msg 4 (Color Creator 0x60cad14f, hue 12, vivid 2) | 188, 190 ×7, 189 | 187/188 = 256×256 at (0,0)/(0,256): the two CC ring bitmaps; 190 = 8×8 dots; 189 = 32×32 cursor |
| msg 5 (wheel 0x60cad39d) | **210**, then 211..222, then 235 ×11, then 226 | **210 = 256×256 at (256,0)**: its own wheel background; 211–222 = 12 per-sector 16×16 icons; 235 = 8×8 tick dot; 223..234 = 16×16 selected-sector marker (224 + code; 226 for code 2) |

- **Answer:** msg 5 draws its own 256×256 background bitmap (id 210) before the polygon, plus 12 sector icons, ticks
  and a selected marker. The hue ring is therefore a **bitmap**, not vector code, as in Color Creator (187/188).
- **Not checked:** whether atlas 0 actually holds wheel artwork at (256,0) in the E-M1 II resources. The atlas pixels
  are loaded when the surface opens (draw task, not followed) [I]. If that area is blank on the camera, the polygon,
  icons and ticks still draw; only the ring background would be missing.

### (e) Are 906 / 925..960 dormant? [S]

I scanned every `mov imm16,d0` followed within 9 bytes by a call into the settings API 0x602da700..0x602db200
(getter and setter wrappers). Only two places use these ids:
- producer 0x6097a1b5: 906, 925..960, 1089/1094/1095 (948 and 960 through the shared tail call);
- 906 again at 0x607dce7f, in fwOpe's drawC3dAsync kind-5 branch, which is the same path.

No stock code writes them. The 3 profiles × 12 sectors are dormant on the E-M1 II (validator ranges exist [V]).
Caveat: settings that are only reached through id tables (backup/restore, generic menus) are not covered by this scan.

### UDF ×9 step

`external/oly_fw_analysis/docs/tooling/ida/README.md` has no UDF semantics; it says `udf00` names alone don't
explain them. Supporting evidence [S]: the PEN-F/E-P7 range-extension edits change, together, `f90009 → f90006`
(polygon step), origin 23.0 → 26.0 and the **float** tick step 9.0 → 6.0. A ×9 integer step that matches the
float 9.0 tick spacing fits that. The radius = 23 + 9·code model stays [I+S]. The camera build confirms it.

### What phase 01 did not emulate

- fwOpe `startVariousDraw` 0x607db538 (it pulls in display-plane code 0x607daf0a/0x60315a10 and 0x607dc7e4/0x607dcfa8),
  and `stopVariousDraw` 0x607db66a beyond its final close 0x607dbc05: static.
- GUI message 12987 delivery and the 0x60941de7 handler: static.
- The draw task 0x60cac29b (msg 1 open: allocations 0x60411833 of 0x700000/0x635c00/0xc00000 by sub-state; close
  through the posted event; atlas load) and compositing on screen: static or camera-only.
- Client 0x602f9583 sync/async behaviour (does the caller wait?): not followed.
- Fixture boundaries added this phase: 0x60310ec6 (plane release after a close) and 0x60cab90c (open-time setup).

### Effect on phases 02–04 [I]

- Phase 03 trigger: call slot +32 (old type) then slot +28 (new type) then slot +48, the same order as the GUI.
  Never call +28 while a surface is open.
- Keep a "wheel active" flag so every page change and editor exit runs stop(type 4) → start(type 0). The editor
  exit matters most: if the GUI then runs its own stop through 0x60f09e18 with the type it remembers (0x61fbfbf4 =
  Color Creator's screen), it closes through fwOpe+424, which already holds kind 5, so cmd 12 matches. Leaving the
  editor while the wheel is open is therefore expected to close cleanly [I]; confirm in the camera build.

## Phase 02 results (2026-11-27): value feed

### Files

- `patches/omdem1mk2/color_wheel/cw.s`, `build.py` → `edits.json`. It is an opt-in fragment: nothing reads it yet, so
  default builds don't change. It is linked against sd_loader's `p_get` (`EM1_LOOKMEM=1` selects exports_lookmem, as
  in look_wb).
- `p_layout.inc`: P_WON 84, P_WAXIS 85, P_WCUR 86 (u8). Existing fields are not moved. P is zeroed at create
  (`p_ensure`, P_SIZE 256 bytes), so P_WON starts at 0.
- `tools/omdem1mk2_emu_color_wheel_feed.py`, which uses the probe's fixtures (`patched_image(syms, base)`).

### Code and sites [S, asserted by build.py]

- **Code:** `cw_get`, 186 bytes at **0x612f1800**, in the 100 KB gap after look memory (0x612f0800..0x612f08d8) and
  look WB (0x612f1000..0x612f10de), before 0x61300000.
- **Build asserts:** 16-byte guards against both neighbours, the gap end and 0xFF stock bytes. The gap is only
  loaded with the halation edit (end word 0x60042b6d); `omdem1mk2_check_loaded` passes on c26t + the fragment.
- **Sites:** 38 rel32 edits. Each is the 7-byte `dd <rel32> 00 04` (`call 0x602da802,[],4`) right after a
  `2c lo hi` (`mov id,d0`):
  - 906 at 0x6097a22d;
  - cursors 1094 at 0x6097a262, 1095 at 0x6097a307, 1089 at 0x6097a3ac;
  - sectors 937..947 at 0x6097a272 + 13k, 949..959 at 0x6097a317 + 13k, 925..936 at 0x6097a3bc + 13k. 0x6097a44b
    also serves 948 and 960 through `mov id,d0; jmp 0x6097a44b` at 0x6097a2fe and 0x6097a3a3.
- **Producer calls left stock:** 617/618 (Color Creator), 665, 971, 985..995.
- **Not hooked:** the separate fwOpe cursor-display API 0x607dce60 (reads 906 at 0x607dce7f). It is outside the
  producer and isn't on the draw path.
- **Rule:** P valid and P_WON == 1 → 906 returns 1. Cursor ids return P_WCUR. Sector k ((id − 925) mod 12) returns:
  - S: clamp(P_SAT[k], ±5). P_SAT already carries strength and chroma, as the pipeline gets it.
  - H/L: round(P_HUE/P_LIGHT[k] / 3), half away from zero, clamped to ±5.
  - Anything else tail-jumps to 0x602da802 with d0/d1/a0/a1 and the stack as at entry.
- **Stores:** stack only (12 bytes). Audit: 0 mul/div/loop opcodes, 0 absolute image stores, 0 frame mismatches
  (`omdem1mk2_audit_opcodes` on c26t + fragment).

### Emulator [V] (`tools/omdem1mk2_emu_color_wheel_feed.py`, ends `OK`)

Image: stock + sd_loader (lookmem) + halation + color_wheel. The producer runs to its client call; the stock run is
the reference.

- **(i) Feed off:** with no P (handle 0), P_WON = 0 or P_WON = 2, the kind-5 buffer is **byte-identical** to stock
  (model profile 2: `2×12 + cursor 4`).
- **(ii) Feed on (P_WON = 1),** asymmetric vectors, cursor 3 and 255:
  - **S:** P_SAT −10,−6,−5,−4,−1,0,1,2,4,5,6,10 → −5,−5,−5,−4,−1,0,1,2,4,5,5,5.
  - **H:** 15,−15,14,−13,7,−8,1,−1,2,−2,0,5 → 5,−5,5,−4,2,−3,0,0,1,−1,0,2.
  - **L:** −1,2,−3,4,−5,6,−7,8,−9,10,−12,13 → 0,1,−1,1,−2,2,−2,3,−3,3,−4,4.
  - The cursor byte equals P_WCUR. The profile is forced to 1, so the reads go to 925..936 and 1089.
  - The buffer then went through the builder and renderer: vertex k (angle −30k°) gets radius 23 + 9·(value + 5). P
    index k reaches buffer[k] and then vertex k, and the asymmetric vectors show no reordering.
  - An invalid P_WAXIS (3) falls back to the getter for the sectors, while profile and cursor stay overridden.
- **(iii) Kind 1 (617/618)** with P_WON = 1 matches stock (`7,0,2,0`).
- **On the full c26t release + fragment:** P_WON = 0 is identical to stock, P_WON = 1 (H) is as expected, kind 1 is
  unchanged. c26t alone with P_WON = 1 is identical to stock (no hook).

**Sector order [I]:** P_* index k (UI order Y, O, OR, R, M, V, B, BC, C, GC, G, YG) is drawn at vertex k (−30k°). This
is the same mapping E-P7 test13 `ed_poly` used (sector id k ↔ UI sector k). Whether vertex 0 sits at Y's hue on the
stock background bitmap 210 can only be seen on the camera.

### Regression (flag off)

- **Rebuilt fragments:** sd_loader (default and lookmem), color_creator_wheel (default, halo, halo + lookmem) and
  look_wb (lookmem) after the p_layout change. Git shows no content diff, only an LF/CRLF rewrite on the three default
  sd_loader files, which I reverted.
- **Harnesses** on c26t and on c26t + color_wheel, with identical results on both specs:
  - color_creator, look_memory, look_wb, halation_flag and halo_page: PASS.
  - halation_route: fails the same way on both specs ("lacks these halation edits (setting=False, no_pass=0):
    0x612e7000, 0x603900ec, …"). Its default compares against a freshly built halation fragment that doesn't match
    the c26t edits. This is an invocation/baseline mismatch that already exists, not caused by this change; it needs
    the build flags c26t was sealed with.
  - halation_pass (no spec, stock only) is not affected by this patch.

### Not emulated

- P_WON / P_WAXIS / P_WCUR are not set by anything yet; that is phase 03 (page code + fwOpe stop/start/draw).
- The producer is run from its vtable entry with a synthetic request, not through GUI message 12987.
- Draw task and screen output: as in phase 01.

## Phase 03 results (2026-11-27): one Wheel page

The first three-page variant (Wheel S / H / L as pages 1–3) passed the same checks. The user's change request replaced it with the single page below.

### Behaviour (`EM1_CC_WHEEL=1`, requires `EM1_CC_HALO=1`)

- **Pages:** Film 0 → Wheel 1 → Chroma 2 → Luminance 3 → Strength 4 → Halo 5 → Film (`PG_*`, `N_PAGES = 5 + HALO`). INFO and TRASH both step forward, as before.
- **Entering Wheel:** P_WAXIS = 0 (S), P_WCUR = 255, P_WON = 1, then stop(0) → start(4) → draw(5).
- **On Wheel:**
  - The Down arrow (record+16, `cc_down`) and TRASH (0x9016, record+36 → `cw_page`; as Delete on the E-P7 / PEN-F wheel) step P_WAXIS S → H → L → S and issue draw(5) only. TRASH on other pages still steps the page.
  - Up, Left and Right do nothing and return 1. So do both dials.
  - The dials share the arrow path [S]: `cc_dial1`/`cc_dial2` set P_DIAL = 1 around the stock loop, and the loop calls the parent's +44..+56 handlers once per detent (0x60e8bb3e/66/8e/b6). `cw_down` only acts when P_DIAL = 0.
- **Guide:** `Wheel S|H|L <look>`. The SCP label is "Color Wheel".
- **Leaving** (INFO to Chroma) and the OK and MENU/other-event exits: P_WON = 0, then stop(4) → start(0) → draw(5). OK and MENU then go to the stock handler, and P_PAGE is reset to Film.
- **cc_init** only clears P_WON. Half-press and power-off: unchanged (see Not emulated).

### Sites [S, build.py asserts]

| Site | Use |
|---|---|
| cave 0x612e6900..0x612e6f64 | 1636 B (halo+lookmem without wheel: 1776 B). The SCP page tables move to .cwui |
| record+40 0x61259c68 | stock 0x60e8ce8c → `cw_ok` 0x612f1a9c (11th pointer hook) |
| .cwui 0x612f1900..0x612f1b78 | 632 B, after cw_get (0x612f1800..0x612f18ba), < 0x61300000, 0xFF guards: `cw_fw`, `cw_enter`, `cw_leave`, `cw_next_page`, `cw_down`/`cw_axis`, `cw_page`, `cw_event`/`cw_ok`, `cw_guide`, `cw_scp_label`, tables |

fwOpe is reached as in the stock GUI:
- `call 0x6082602c,[],4` returns the API object in a0;
- the vtable slot (+32 stop, +28 start, +48 draw) is called with `calls`;
- d1 = 2 if (0x61fbfbcc) ≠ 0, else 1;
- a1 = a zeroed 32-byte block.

### Emulator [V] (`tools/omdem1mk2_emu_color_wheel_page.py`, RESULT PASS)

**Setup:** the spec is c26t + the wheel build + color_wheel. The fwOpe slots and the stock +36/+40 handlers are logging stubs (`tools/emu_fixtures/em1_cc_wheel_fw_stubs.s`). A surface model asserts:
- stop matches the open type;
- start only runs when nothing is open;
- draw only runs when a surface is open.

**Results:**
- **INFO ×6:** pages 1,2,3,4,5,0. TRASH on the non-Wheel pages steps them the same way (Film→Wheel enters, Chroma→…→Film→Wheel).
  - fwOpe calls: `stop0 start4 draw` | `stop4 start0 draw` | none ×4.
  - P_WON is 1 only on Wheel, and type 0 is open at the end.
- **Down ×4 and TRASH ×4 on Wheel:**
  - axis H, L, S, H, each with draw only;
  - P_WON stays 1 and the page stays 1;
  - the guide follows the axis;
  - INFO then leaves, and re-entering starts on S.
- **No-op keys:** Up, Left, Right and the four dial detents (P_DIAL = 1 on cc_up/down/left/right) cause no fwOpe call and no setting or P change, and return 1.
- **Exits from S, H and L:**
  - OK and MENU: `stop4 start0 draw`, then the stock handler with the original event; P_WON = 0 and page 0.
  - cc_init: no call; P_WON = 0.
  - On Film, OK and MENU go straight to stock.
- **Other record+36 events** (0x972b, 0x903e, 0x900d, 0x900e and an unknown 0x1234, which reaches the stock default
  branch), with logging child widgets at parent +124/+128: `stop4 start0 draw`, then `sync_children_and_view` (child
  sync + 0x900c to both children, as on a page step), then the stock handler with the original event. Afterwards
  P_WON = 0, page 0, type 0 open and the guide reads the Film text. OK does not refresh before the stock commit.
- **GUI flag:** with 0x61fbfbcc set, d1 = 2 on every call.
- **Other pages:** Chroma 2, Lum 3, Str 4 and Halo 5 match c26t at pages 1–4 (guide before and after a key, P values, settings, sid 961, SCP label, no fwOpe call).

### Regression

- **Flag off:** `edits.json`, `edits_halo.json`, `edits_halo_lookmem.json` and look_wb, rebuilt, are byte-identical to HEAD (`git diff --quiet`).
- **Flag-on spec:** check_loaded OK. The audit is OK (0 mul/div, 0 image stores, 0 frame mismatches).
- **Harnesses:** flag on: color_creator, look_memory, look_wb, halation_flag, color_wheel_probe, color_wheel_feed and color_wheel_page all PASS or OK. Flag off (c26t): halo_page PASS; the earlier flag-off run (color_creator, look_memory, look_wb, halation_flag PASS; halation_route fails as it already did, see Phase 02) still applies, because the c26t release is unchanged. halo_page is not run flag on: it hard-codes INFO x4 = Halo and has no fwOpe fixture. Halo on the wheel build is covered by color_wheel_page.
- **Correction on halation_route:** the earlier "failure" came from running it without the seal's flags. The v0.4c27t seal
  runs it with `--stage-setting`, as for v0.4c24–c26t, and it passes. The v0.4c27t seal ran 25 checks, all PASS
  (see `patches/omdem1mk2/CHANGELOG.md`).

### Review fixes (2026-11-27, before the final v0.4c27t seal)

- **cw_get frame [V]:** it saved d1 at (0,sp), which `call p_get` overwrites with its return address, so d1 came back
  as that address on both paths. It now reserves 16 B: (0,sp) is p_get's call slot and d1 / a0 / a1 live at 4 / 8 / 12.
  `emu_color_wheel_feed` calls cw_get as a site does with sentinels: d1 and a1 kept on the pass-through path (a0 is
  the getter fixture's), d1 / a0 / a1 kept on the override, and the getter's `ret [],4` lands on the site.
- **Other record+36 events [V]:** they now refresh the children and view after leaving the wheel (above), so the screen
  is not left reading "Wheel S" on Film.
- **Seal tool:** a shorter rebuilt expect is accepted only when the stock tail it drops is all 0xff and the patch still
  writes something. `emu_color_wheel_feed` runs on the sealed spec, not the fragments.

### Not emulated

- **Half-press and power-off** have no editor hook. They rely on the GUI's own stop at 0x60f09e18 (which closes the kind at fwOpe+424) and the cc_init reset [I]. Camera check: Wheel → half-press → reopen Color Creator.
- **Real fwOpe chain:** the run from the page handlers to the C3d task was not done end to end. Its parts were emulated in phases 01/02.
- **Dial path:** the stock dial loop itself was not run. Its per-detent calls are modelled with P_DIAL = 1 [S].
- **Screen output and the GUI dispatcher path** were not emulated.

## Phase 04 results (2026-11-27): camera-test build v0.4c27t

- **Seal:** `tools/omdem1mk2_catalog_release.py --stock stock_firmware/OLY_E_125_3700_0000_0000.BIN --version v0.4c27t`
  (WSL), after the review fixes above. It is v0.4c26t with the CC edits from `edits_halo_lookmem_wheel.json` (new
  sites: record+40 hook, .cwui) and the color_wheel fragment appended (`lookmem` checked against the sd_loader cave).
  - 294 edits, 14,134 changed payload bytes (build.json).
  - 25 checks, all pass, including `emu_halation_route --stage-setting`.
  - `emu_color_wheel_page` replaces `emu_halo_page` for this version only, because Halo is now page 5.
  - Added: `emu_color_wheel_probe`, `emu_color_wheel_feed` (on the sealed spec) and `emu_color_wheel_page`.
- **SHA-256:** `E1259999.BIN` `a525ef54bc87697308005fca8c29fecca5feddb6c28395d90d1062aad3d0a8fd`; `edits.json`
  `11a924b36be5ed08de6099334a52d38491b1197b4a96faec818911b79f617eb8`. The restore file is OM's stock (`691a8a8e…`).
- **Out build:** `caduceus.py build` / `verify` into `out/em1mk2-thu-may/7-v0.4c27t`: "All good.".
  `tools/test_caduceus_releases.py`: 6 tests OK.
- **Older releases [V]:**
  - The v0.4c24 / v0.4c25t / v0.4c26t files are unchanged (Windows git clean; `sha256sum -c` OK).
  - v0.4c26t's spec, rebuilt with the new seal tool, is byte-identical to the sealed one.
  - v0.4c24 / v0.4c25t rebuild to the same result with the HEAD and the new tool. Both differ from their sealed specs
    because their patch fragments have moved on since; that is not caused by this change.
- **Camera test:** `docs/OMD-EM1-II/thu-may-color-wheel.md` (checklist 0–7, plus an unusual-event exit). Not yet run on a
  camera. "Not emulated" above still applies.
