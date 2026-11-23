# E-M1 II 3.70: the stock sites behind E-P7 bloom, grain_cpu r2 and halation

Date 2026-11-20. Read-only research. Image `em1mk2/extracted/00_0100_40560020.decoded.bin`, base 0x60021020.
Tags: [S] static trace, [E] emulator run, [?] guess. **Nothing here has been run in the emulator ([E] = none).**

**Input gap.** The E-P7 1.1 image is missing from this checkout (`analysis/ep7_1100/` is absent and
`stock_firmware/` holds only `OLY_E_125_3700…`), and so is the E-P7 container. `tools/fetch_stock.sh` would download it,
which needs the user's approval. So `tools/omdem1mk2_ep7_match.py` could not be run. Each match below is anchored on
what the E-P7 side records: the stock bytes in the patch builders, the call frames (`call x,[regs],n`), struct offsets,
constants and dispatch tables in the docs. Each one was then checked on the E-M1 II disassembly.

## Site table

| E-P7 site (role) | E-M1 II proposal | How matched | Conf. |
|---|---|---|---|
| `0x603eab39` Art Effect → job-flags converter (a2 = params+12, a3 = capture) | **`0x6042285e`** (`call …,[a2,a3],20` from `0x6041dde2`, `0x60420af1`) | [S] same shape: a0 = source request, `mov (28,a0),a3` = capture, art byte → jump table **`0x60556bfc`** whose 10 cases set exactly the E-P7 flags (1 → 0x80, 2 → 0x400, 3 → 0x8000, 4 → 0x2000, 5 → 0x40, 6/7 → 0x100/0x200, 8/9 → 0x800/0x1000); preceded by the key converter `0x6042270e` as on E-P7 (`0x603eaa04`) | high |
| `0x603eabd7` flag hook (6 B `movbu (24054,a3),d0; cmp 0,d0`, back at `0x603eabdd` = bne) | **`0x604228fc`**, stock `fa438c5ea000` (`movbu (24204,a3),d0; cmp 0,d0`), then `c9 0a` bne at **`0x60422902`** | [S] same instruction pair, capture offset +150 (see §Offsets); `jmp d32; nop` (6 B) fits like on the E-P7; back address 0x60422902 | high |
| `0x6035ca31` Soft Focus blend setup (`calls`, a0 = job; 0x1000 → req+20, 0x1061 → req+84) | **`0x60398ee1`** (`movm [d2,d3,a2,a3]`) | [S] bufidx(0x1000), bufidx(0x1061), `<48` checks, stage **0xf005**, effect **0x0402** at req+656, 64-B copies to req+20 / req+84, returns 48 on failure | high |
| `0x603579b8` work-list word `mov SF,a1` (only reference) → gc_gs | **`0x60393a6b`** (in `fc de e18e3960` = `mov 0x60398ee1,a2` at 0x60393a69) | [S] the only abs32 ref to 0x60398ee1; it sits under `btst 128` on job flags (0x603939ff) and the class-0..3 branch, as on E-P7 | high |
| `0x6035caad` blend-setup hook (red probe) `f8670cf86b0e` | **`0x60398f5f`** (same 6 B), back `0x60398f65` | [S] exact bytes, same place after the two 16-word copies | high |
| `0x6035c9c1` reduce/upscale pass, `0x6035cbaa` blend cb | `0x60398e6f` (one ref, 0x60393a54), `0x6039905e` (one ref, 0x60393a76) | [S] pushed just before the blend; distances 0x72 / 0x17d vs E-P7 0x70 / 0x179 | med-high |
| `0x6035cc1b` combiner-12 entry (classes 4–8) | `0x603990cf` (cb `0x6039924a`), pushed at 0x60393a2b for class 4..8 | [S] same branch on job+11341 ∈ 4..8; distance from the blend 0x1ee vs E-P7 0x1ea | med-high |
| `0x60355fd4` request callback (bloom_w guard) | `0x60391959` (stored at record+0, 0x6039033a) | given exact by the earlier byte search; request embedded at **job+11364** (`0x60390dbe`), same as E-P7 [S] | high |
| `0x603b5200` combiner selector / `0x603b5249` key<12 hook | **`0x603f1653`** / `0x603f169c` (`aa0cc605cc5501`) | [S] stage 0xf00f/10/11/0xb004 → 18/19/20/27, then `cmp 12,d2; bcc; jmp 0x603f17f5` (default) | high |
| `0x603a013b` combiner config + bank base+7364 | dispatcher at `0x603dcd35..67`: `call 0x603f1653` → id 1..156 → table **`0x6053e108`** of {id, handler} pairs, `jmp (a0)` with **a2 = ctx**, frame `[d2,d3,a2,a3],20` | [S] the table ids include 11, 12, 135, 136, 31..39; bank = (8,ctx)+7364 | high |
| `0x603a049e` combiner 11 | **`0x603dd06f`** (table word **`0x6053e164`**) | [S] mode 0x00200001, 3822, **+92 = 0x02580258, +96 = 600, +136 = 0x01a801a8, +140 = 424** (tail `0x603dd518`) | high |
| `0x603a04f3` combiner 12 | **`0x603dd0b8`** (table word **`0x6053e16c`**) | [S] same with A/B swapped (424 / 600) | high |
| `0x6039fee8` weight getter, `0x603a04a7`/`0x603a04fc` its calls (W_HOOK, C11/C12_CALL) | **none** | [S] E-M1 combiners 11/12 have the weight as a constant (600 / 424). That is why no calls were found by bytes. `cmp 0x01010065` exists only at 0x6038f360 (job constructor), not in a getter | high (absent) |
| `0x603a04e8` combiner-11 tail hook (gain stores + `ret`) | no equivalent site | [S] the E-M1 tail `0x603dd518` (`mov d0,(140,a2); ret`) is shared with other combiners. Hook through the table word `0x6053e164` instead (data edit, ctx still in a2) | high |
| `0x603a03a6` combiner 135 (gains from req+672/674/676) | `0x603dcf77` (id 135) | [S] reads req+672/674/676 into +136/+140 | high |
| `0x60350975` bufidx (`call …,[d2],4`, a0 = job, d0 = id) | **`0x6038c01c`** | [S] job+6592, stride 88, id at +76, 48 entries, `retf [d2],4` | high |
| `0x6035b517`/`0x6035b529` shading entry / output pass; OB_WORD `0x60357b1f` (`fc cd` + OB) | entry `0x60397721`, **OB `0x60397733`**, **OB_WORD `0x60393c90`** (in `fc cd 33773960`) | [S] under `btst 0x80000` (0x60393c4c), with an attach-modifier alternative `0x603971e8`; entry→OB distance 0x12 on both bodies; one abs32 ref each | med-high |
| `0x6035749f` WL hook (`aa0cc605cc0604`), `0x6035739e` wl_final, `0x603573d3` wl_attach, `0x603578bd` wl_after, dev entry `0x60356d7b` / cb `0x60356cc6` | **no matching functions.** Builder `0x60392e0d` (list at job+10984, 12-B items) writes items inline (`mov d1,(d0,a3)`, pending entry in a2, attach = `mov x,(4,item)`) | [S] the push/attach helpers were inlined, so there is nothing to call or hook with the same shape. Dev-entry pair is [?] (`0x6039276e` / `0x6039263e` recur) | — |
| `0x60354930` wait for producing request (gc_ob only) | not located | — | — |
| `0x6006a922` lock / `0x6006a96b` unlock (`[d2],8`) | **`0x6006e9d0`** / **`0x6006ea19`** | [S] only callers of the PSW-level set/restore `0x60054ccf` / `0x60054cf0`; same 0x49 spacing as E-P7; `ret [d2],8` | high |
| `0x60066fc0` cache flush (`[d2,d3],16`) | **`0x60068709`** | [S] locks, waits on 0x8070 bit 8, touches lines 0x28a00000 / 0x28a80000, sets bit 16 of 0x98100000 + CPU stride, `ret [d2,d3],16`; modeset calls it first, as on E-P7 | med-high |
| `0x600672ee` modeget (`[],0`) / `0x600672fe` modeset (`[d2,d3,a2],20`) | **`0x60068b78`** / **`0x60068b88`** | [S] mode array **`0xa274d410`** indexed by (0x8050); set programs `0x98100058/4c` (+0x400 per CPU); spacing 0x10 on both bodies; frames match | high |
| `0x60067146` window mapper (`[d2,d3,a2,a3],28`) | **`0x6006888f`** | [S] same registers, mode array and frame. **Its ranges differ**, see notes | med (role high, contract differs) |
| `0x60022782` / `0x600227b4` malloc / free (`[],4`) | `0x600231fe` / `0x6002323d` | [S] from `ARCHITECTURE_AND_MEMORY_MAP.md` (classes ≤128 / ≤2048 / ≤16384) | high |
| WDT sites `0x6005b23a`, `0x6005bcff` (`80 0a` → `80 1e`) | **`0x6005aecc`** `800a` before `call 0x600226fd` | [S] the only `mov 10,d0` before the setter. No second immediate-10 site; other callers pass 0, 1 or a register (`0x60079283`) | high / 2nd site [?] |
| `0x600313ef` dly_tsk, `0x60054b33` SYS_WDT msg | not looked for | in `halation/build.py` syms but not used by `hl.s.in` h7 (no yields) | — |
| capture-kind mapper `0x603ea909` (+ `0x603ed45a`) | **`0x6042257f`** (+ `0x60425e48`) | [S] kinds 0x2001/0x2006 → type 0x110/0x120 ((206) == 2 → 0x20), unless the helper returns 1 → 0x1000; 0x1008/0x1006 → 0; others → 0x1000 | high |

## Capture flag word and the 0x80 flag

- The flag word is **params+12**, the converter's a1/a2 (`call 0x6042285e` with a1 = params+12; key bytes at params+8..11 from
  `0x6042270e`) [S]. **Set:** case 1 of table 0x60556bfc at `0x6042287c` (`or 128`) when capture+**24951** (Art Effect) = 1 [S].
  The converter then clears 0x4000 and 0x10000 and sets or clears 0x200000 from capture+24204 / +24205 (the flag-hook bytes) [S].
- **Test:** the work-list builder reads job+16 (`(12,sp)` = job+16) at **`0x603939ff` `btst 128`** → the Soft Focus pushes.
  Art keys get some flags stripped at `0x6038f34a` (`and ~0x20000`, `and ~0x40000` on job+16; E-P7 `0x60353b15`) [S].
- **Kind enum:** identical. The kind is source request **+194** (E-P7 too, after the gk1 fix: params+4 = request).
  0x2001, 0x2006, 0x1008 and 0x1006 are compared at `0x60422587..99` (mapper), and 0x2001/0x2006 also at `0x6042278e..94`
  and `0x60422761..67` (key converter) [S].

## Offsets that carry over (E-P7 → E-M1 II)

- Capture record: picture mode **24053 → 24203** (`0x60422715`), profile **24083 → 24233** (map doc row `0x602d24a5`),
  flag-hook byte 24054 → 24204. That is +150 here, but the Art Effect byte is 24785 → **24951** (+166), so the shift is not
  the same across the record. Check each field on its own [S].
- Job: +16 flags, +20 type, +6592 buffer records (88 B, id +76), +10984 work list, +11308 key, +11320, +11341 class and
  request at +11364 are all unchanged [S]. Other fields gr2 reads (+11314, record +0/+8/+10/+12/+14/+72) are [?].
- The CPU id is at (0x8050) on both bodies [S].
- Picture-mode codes: <100 colour/mono modes, ≥100 art filters (`cmp 100` at `0x60422743`). 11 = COLOR and 12 = MONO in
  the 0x9481 reader [S]. Monotone's value is [?] and is needed for the gate.

## Notes for the halation design

1. **Neutral blend.** E-P7 got the neutral blend from `bw_default` 600 → 1024 in its weight getter. The E-M1 has no getter,
   so repoint table words `0x6053e164` / `0x6053e16c` to stubs. Each stub replays the case (bank = (8,a2)+7364, 0x603dca05
   clear) and writes A = 1024, B = 0 for our jobs; others take the stock path. a2 = ctx: ctx+4 = request, ctx+8 = base,
   ctx+52 = key (used by case 13 at `0x603dd12b`) [S]. This is a 4-B data edit per combiner, no instruction replaced.
2. **The job marker gc_lvl relies on (job+15488..15490) is E-P7 transport and does not exist here.** The decision has to come
   from the flag hook, through the heap block, as `gc_pend` does.
3. **Mapper contract differs [S].** `0x6006888f` refuses bus < 0x84000000 and 0xa0000000..0xafffffff (debug print via
   `0x60023188`, then returns 0). It maps 0x84000000..0x9fffffff and 0xb0000000.. in 128 MB steps through window
   0xb0000000 / 0xb8000000 (mode ids 0..11). E-P7 returned 0 for "direct below 0xb0000000". The gc_cls/gc_grain range logic
   and its guards (2a..2e) must be re-derived on this body before any buffer is touched.
4. **The plain-look route (gc_wl + gc_ob) is not portable as-is.** There are no list helper functions. A port would add
   items inline at job+10984 or hook the `fc cd` OB word only. Routing halation through flag 0x80 + blend word (gc_gs)
   avoids that and needs only the sites marked high above.
5. `0x6039517c` (the "≈ entry" from the prefix search) is a stage-0x0200 request modifier (`mov 512,d0; movhu d0,(12,a1)`),
   **not** the Soft Focus entry. `0x60398ee1` is the entry.

## Emulator candidates (inputs are fabricated structs)

- **Converter `0x6042285e`**: a0 = request (+194 kind, +28 → capture with +24951 / +24204 / +24205), a1 = flags word. It
  only calls out (`0x6141a79a`) for an Art byte outside 0..9. Best first target for the flag hook on/off, every kind.
- **Kind mapper `0x6042257f`** (calls `0x60425e48`; stub or fixture it). **bufidx `0x6038c01c`** (pure).
- **Selector `0x603f1653`** + dispatcher → **combiner 11/12 cases**: ctx with +4 request (+12 stage, +16 kind), +8 base,
  +52 key. Callee `0x603dca05` writes the bank only. This proves the table-word stubs (A/B values) against stock.
- **Blend setup `0x60398ee1`**: job with records at +6592 for 0x1000 / 0x1061. Callees: `0x6038c01c`, `0x60390dbe`
  (request init at job+11364), `0x6038bc07`, `0x60390536`. Heavier, but it is the gc_gs path.
- **lock/unlock/modeget/modeset/mapper/flush**: need PSW and the 0x98100000 / 0x8070 MMIO. Flush busy-waits on hardware
  (count calls, as on E-P7). The mapper runs once the windows at 0x98100058/4c (+0x400, +0x800) are mapped.
- **Builder `0x60392e0d`**: job-sized fixture; check that flag 0x80 adds 0x60398e6f / 0x60398ee1 / 0x6039905e for classes 0..3.

## Open questions

1. Fetch the E-P7 1.1 container (`tools/fetch_stock.sh`, user approval) so `omdem1mk2_ep7_match.py` and side-by-side
   disassembly can confirm the [S] shape matches. It also confirms the E-P7 OB/dev-entry pairing (fn vs cb) that I
   inferred from distances.
2. E-M1 picture-mode values for Monotone, e-Portrait and Color Creator. Which job key the stock colour modes get (gc_gs
   checks key 11).
3. `0x60354930` wait equivalent. It is only needed if the plain-look route is ported.
4. Is there a second watchdog-10 restore after the flash-op path (E-P7 `0x6005bcff`)? Not found as an immediate.
5. Mapper return 0: does it mean direct or refused for E-M1 callers? Read a stock caller, then run it in the emulator.
