# Halation on the OM-D E-M1 Mark II (fw 3.70): port plan

Status (2026-11-23). The flag gate and CPU pass have emulator coverage. Routing the pass for ordinary colour stills is
open. The design comes from the E-P7 halation in this repo (`patches/halation`,
`docs/HALATION_RED.md` §14–17, on `patches/bloom` + `patches/grain_cpu` r2). The OM-3 version
(androidfanman/caduceus-om3 v0.28, Apache-2.0, its own code after the E-P7 method) runs on different base firmware; only its
tuning is a candidate for later (h2: u = 255v/(v+K) tables, 3 + 10 two-layer blur, chroma weight from the cell's mean
brightness, gradual daylight fade; credit in NOTICE).

## Owner decisions (2026-11-13)

| Question | Decision |
|---|---|
| Scope | Halation applies **over any film / colour profile** once enabled, not per look |
| Where the setting lives | **A camera control, remembered over power-off** in the camera's own settings memory (one spare stock setting, found and emulator-proven first) |
| Picture modes | **All colour modes**: our looks (Color Creator) and the stock colour modes (Natural, Vivid, Muted, Portrait, i-Enhance, …). Not Monotone, not Art Filters |
| Precedence | **The global setting sets the strength; the glow colour comes from the look** (red / amber / warm / cool, `tint` at LOOKS.BIN record +47), red when the look has none |

## How "always applied" is guaranteed

1. **One global stage** (Off / Low / Med / High = gmax 0 / 112 / 176 / 240), read at each shot from its own setting. It is
   not in any look slot, so picking a film, a look or a picture mode cannot change or drop it.
2. The capture-flag hook adds the Soft Focus flag 0x80 when stage ≠ Off **and** the job is an ordinary still of a colour
   mode. Step 4a verifies where the firmware can use that flag to schedule the blend. The gate excludes the capture kinds the E-P7
   skips for grain (0x2001, 0x2006, 0x1008, 0x1006), Monotone, Art Filters (they keep their own flags), movies, live view.
   If the job already has 0x80 (e.g. a look with bloom), the halation pass runs after that blend as on the E-P7.
3. **Look values are only a fallback for the tint.** The E-P7's "0 = follow the look" stage is not used on this body.
4. **Emulator proof before any camera build** (AGENTS.md): run the flag hook and the pass entry with stage on/off for every
   picture-mode value, every look slot (built-in, card, none), card present / absent, each excluded capture kind, and
   bloom on/off; pass = the 0x80 flag and the pass call happen exactly when the rule above says, stock otherwise. The
   pass itself bit-exact against a Python model (as the OM-3 did).

## What has to exist first (E-P7 layers → E-M1 II)

| Layer | E-M1 II status (2026-11-13, byte search of the E-P7 sites) |
|---|---|
| Soft Focus route (bloom: flag hook, blend setup, combiner 11, callback) | callback `0x60391959`, blend setup `0x60398f5f`, effect selector `0x603f1653` exact; flag hook ≈ `0x604228fc`, Soft Focus entry ≈ `0x6039517c` / `0x60398ee1` (prefix match); combiner 11/12 calls not found by bytes |
| CPU pass route (grain_cpu r2: work-list hook, window / mapper, lock / unlock) | not found by bytes; needs code-shape search |
| Watchdog 10 s → 30 s (E-P7 v0.31b) | **Done [E]:** both run-time settings `0x600792c4` / `0x6005aecc` → 30 s (halation patch). See below. |
| Spare remembered setting for the stage | **sid 961** (key `0xF709[0]`), see "Stage setting" below; power-off survival needs one camera test |
| Code space ~1.8 KB + tables; one malloc ≤ 16 KB per shot | 100 KB of loaded gap confirmed on camera with sp1. The actual halation allocation and code placement still need verification. |
| Camera control | a Halo row/page in the look editor (`color_creator_wheel`) |

## Step 1: code-space probe sp1 (2026-11-13; **camera: S+**)

- Gaps between loaded sections (loader `0x60042b96`, end getter `0x60042b35`, descriptor table `0x60027450`), scanned for
  code that uses an address inside them (`mov imm32` / absolute operands, cached and uncached): `0x605d3000` (8 KB),
  `0x6078f000` (28 KB), **`0x60bc8800..0x60bf1000` (162 KB)** and **`0x612e7000..0x61300000` (100 KB)** are referenced only
  by their section's end word; `0x60580800..` is written at runtime (`0xa05842f8`): not usable. The getter is called only by
  the loader. Base-region 0xFF runs are startup copy/clear ranges (`0x60021111`): not usable.
- sp1 raises **section 5's end word** (`0x60042b6d`) `0x612e7000 → 0x61300000`: the flash span then ends at section 6's own
  source (`0x4183f000`), so the loader copies the gap straight from the package. The gap holds a magic word + an LCG
  pattern; a 65-B check (`0x605d2f98`, section-3 tail, outside the probed region) sums it on each look-editor banner draw and
  appends **`S+`** (loaded, intact), **`S!`** (loaded, changed since boot) or **`S0`** (not loaded). Patch
  `patches/omdem1mk2/space_probe`; editor call only with `EM1_SPACE_PROBE=1`; `check_loaded` now reads the release's own
  end words.
- **Emulated** (`tools/omdem1mk2_emu_space.py`): end getter stock `0x612e7000` / patched `0x61300000`, flash span =
  section 6's source; the check on the built / 0xFF / one-word-changed region → `S+` / `S0` / `S!`, registers kept; the
  editor's own `call` site through the check and back. **Not emulated:** the loader's flash copy, and whether anything
  uses that RAM later -- that is the camera test.
- **Camera (owner, v0.4c13-sp1):** banner `Provia C0 S+ K0009+` after several bursts and picture-mode changes: the region is
  loaded and untouched by normal use → **0x612e7000..0x61300000 (100 KB) usable** for code and tables [C].
  The owner also reported `S+` after a power cycle and a movie.
- The 162 KB gap after section 4 can be probed the same way when needed.

## Step 2: E-M1 II sites (2026-11-20, static unless marked)

Full table and evidence: [`plans/reports/research-261120-1400-em1ii-softfocus-cpupass-sites.md`](../../plans/reports/research-261120-1400-em1ii-softfocus-cpupass-sites.md).
The E-P7 image was not available locally, so every match is from the E-P7 patch sources and docs, checked on the
E-M1 II disassembly.

- **Flag converter `0x6042285e`** (E-P7 `0x603eab39`): request +28 → capture; Art Effect byte capture+24951 → jump
  table `0x60556bfc` (1 → 0x80 Soft Focus, 2 → 0x400, 3 → 0x8000, 4 → 0x2000, 5 → 0x40, 6/7 → 0x100/0x200,
  8/9 → 0x800/0x1000); clears 0x4000 / 0x10000; sets 0x200000 from capture+24204 | +24205. **Emulated**
  (`tools/omdem1mk2_emu_artflags.py`, 160 cases, stock and v0.4c17; part of the release checks).
- **Flag hook `0x604228fc`**: stock `fa438c5ea000` (`movbu (24204,a3),d0; cmp 0,d0`), back at the `bne` `0x60422902`;
  a 6-byte `jmp d32; nop` fits as on the E-P7.
- **Soft Focus blend setup `0x60398ee1`.** The Art work-list builder loads its address from `0x60393a6b` under
  `btst 128` on job+16 at `0x603939ff`. The blend-setup hook `0x60398f5f` has the same 6 bytes as the E-P7. **Emulated**
  (`tools/omdem1mk2_emu_blend_setup.py`, entered with `calls` like a work-list item): finds records 0x1000 / 0x1061
  (bufidx), inits the request at **job+11364**, writes stage 0xf005 (+12) and effect 0x0402 (+656), copies both
  records to +20 / +84, describes the output at +340 (format 0x302, stride = width rounded up to 32, width, height) and
  queues it; the selector maps that request to combiner 11; at `0x60398f5f` a2 = request, a3 = record 0x1000; without
  record 0x1061 it returns 48 and writes nothing. Allocation, queue submit and release are frame-correct fixtures.
- **Gate design consequence:** the combiner stub gets ctx+4 = request = job+11364, so it can find the job itself
  (request − 11364) and test a per-job mark set by the flag hook, instead of a global flag that another job could see.
- **Combiners:** dispatcher `0x603dcd0c` (bank init, then `0x603dcd35`) → selector `0x603f1653` → table `0x6053e108`
  {id, handler}. For a kind-3 request the selector reads the effect code at **request+656**: 0x0402 → 11, 0x0403 → 12
  (effect table `0x6054c97c`, key = effect − 259). Combiner 11 `0x603dd06f` (word `0x6053e164`), 12 `0x603dd0b8` (word
  `0x6053e16c`); both write the bank at (ctx+8)+7364 and end in the shared tail `0x603dd518`. **No weight getter on
  this body:** 11/12 use the constants 600 / 424. **Emulated** (`tools/omdem1mk2_emu_combiner.py`): stock selects
  11/12 and writes +92 = 600|600<<16, +96 = 600, +136 = 424|424<<16, +140 = 424 (12 swapped). The neutral-blend design
  is proven with the prototype stubs `tools/emu_fixtures/em1_combiner_neutral.s` behind the two repointed table words
  (4-byte data edits): gate off = the stock bank byte for byte, gate on = w 1024 (11: A 1024 / B 0; 12: A 0 / B 1024)
  with every other bank word unchanged, combiners 9/10 untouched. The real gate (which job halation marked) is step 4.
  Lesson kept in the fixture: a helper the stub `call`s must have a non-zero frame (`[],4`), or its own nested `call`
  overwrites the return slot (the emulator caught this as an endless loop).
- **Capture kind [E]:** mapper `0x6042257f` (`tools/omdem1mk2_emu_capture_kind.py`): request+194 0x2001 / 0x2006 →
  type 0x110 / 0x120 (by request+206; 0x1000 if helper `0x60425e48` returns 1), 0x1008 / 0x1006 → 0, any other kind →
  0x1000. So the gate can test request+194 directly against the four excluded kinds, as on the E-P7.
- **CPU pass (grain_cpu r2):** bufidx `0x6038c01c`, lock/unlock `0x6006e9d0` / `0x6006ea19`, flush `0x60068709`,
  modeget/modeset `0x60068b78` / `0x60068b88`, malloc/free `0x600231fe` / `0x6002323d`.
- **Mapper `0x6006888f` [E]** (`tools/omdem1mk2_emu_mapper.py`, 144 cases, CPU ids 0..2). The E-P7 treated every
  address below 0xb0000000 as direct; this body differs:
  - **Refused, use directly:** addresses below 0x84000000 and 0xa0000000..0xafffffff. The mapper prints
    `[exad]change_addr_err!!` (`0x60023188`, a log, not a stop), returns 0 and does not lock.
  - **Windowed:** every other address. It locks (`0x6006e9d0`), flushes (`0x60068709`), maps the bucket holding the
    address (0x84..0x87 is 64 MB, the rest 128 MB) into this CPU's window and returns `0xb0000000 | (addr & 0x07ffffff)`
    (`0xb8000000 | …` for 0x98..0x9f and 0xf8..0xff). It writes the bucket code (0x1000, 0x2100, 0x3200, 0x7600,
    0x8700 … 0xfe00) into the window registers `0x98100058` / `0x9810004c` (+0x400 per CPU, low byte kept), stores a
    mode 0..11 in `0xa274d410[cpu]`, then unlocks with the lock's token.
  - **For the halation pass:** test the buffer address first; use refused-range addresses as they are, and call the
    mapper only for the others. One window per CPU at a time, so a pass that walks two buffers in different buckets
    must remap between them (or copy through a direct buffer). The Art work-list builder `0x60392e0d` writes items inline.
    Step 4a traces the separate colour-still builder.
- **Capture fields do not shift uniformly:** picture mode +24203, profile +24233 (+150 vs E-P7) but Art Effect +24951
  (+166). Capture kinds 0x2001 / 0x2006 / 0x1008 / 0x1006 appear unchanged in the kind mapper `0x6042257f`.
- Still open: Monotone's picture-mode value, the job key of stock colour modes, and the mapper's 0 return.

### Stage setting: sid 961 (2026-11-20)

Report: [`plans/reports/research-261120-1400-em1ii-spare-setting.md`](../../plans/reports/research-261120-1400-em1ii-spare-setting.md).

- **Sid 961, property key `0xF709` index 0** (E-P7 "sid − 2" mapping: COLOR1 highlight; this body never offers
  picture modes 11/12). The key appears nowhere in code; the sid number only as two log line numbers and one GUI
  resource id; it is in no descriptor, UI init table or editor list [S]. Validator lists −7..+7, default 0 = Off.
- **Persistence [S]:** all settings live in property block 90 (table `0x600a29b0`, RAM `0x624e2000`, registry
  `0xa2736c50`), shadowed to flash slots `0x40240000` / `0x40280000` ("fmem"). 961 is stored at `0x6250423a`.
  What triggers the flash write (power-off or periodic) is not traced.
- **Boot resets:** boot tail `0x601ac7cd` → store load `0x602daefb` → normal boot `0x602da762` (26-id list `0x604cd464`,
  or the 628-id list `0x604ce176` + custom-bank copy when sid 10052 ≠ 0) and boot reasons 7/9 `0x602da77a` (6-id
  list `0x604ce662`); reset primitive `0x602e5ba5`. 961 is in none of them. A full reset (1647-id list `0x604cd498`,
  or `0x602e5acc` when the store check fails) sets it to 0 = Off.
- **Emulated** (`tools/omdem1mk2_emu_spare_setting.py`): facade SetValue 0..3 → 0 and GetValue reads back; stored in
  block 90; kept through all three boot paths while control sid 267 is reset where its lists say.
- **Rules for the halation code:** SetValue does not range-check (7, 8, −8 are stored), so treat any value outside
  0..3 as Off. The value is the same in every shooting mode and is saved in custom modes (C1..), like Color Creator
  hue. Fallbacks: sid 981 (`0xF779[2]`, 0..3, default 1, one reader in the mode-12 mono branch) and 965.
- **Camera test needed:** set the stage, power off and on, read it back.

## Step 3: Soft Focus flag gate for colour stills (2026-11-20)

Patch `patches/omdem1mk2/halation` (`hl_flag.s`, `build.py`):

- **Code space:** section 6 loaded end `0x612e7000 → 0x61300000` (word `0x60042b6d`, the sp1 edit, camera S+); `hl_flag`
  (97 B) at `0x612e7000`.
- **Hook at the converter entry `0x6042285e`**, not at `0x604228fc`: at the entry a0 is still the request (capture kind
  at +194), later it is overwritten. The first 7 bytes (`mov (28,a0),a3; mov a1,a2; mov 24951,a1`, absolute, no branch
  lands inside) become `jmp hl_entry; nop; nop`; `hl_flag` replays them and returns to `0x60422865`.
- **Gate:** stage (sid 961 via the stock property getter `0x6005e6cf(0xF709, 0, a0 = 0)`, as stock `0x604226d2` calls
  it) is 1..3 (anything else Off), Art Effect byte capture+24951 = 0, picture mode capture+24203 < 100 and not 5
  (Monotone) or 12 (MONO) — the stock mono test `0x60342c32` returns 1 for 5, 12, 104 and 109/variant 2 — and the
  capture kind is not 0x2001 / 0x2006 / 0x1008 / 0x1006. Then flag 0x80 is ORed in; nothing else changes.
- This patch sets the Soft Focus flag. The step 4a capture-job test below shows that the class-0
  colour-still builder produces the same list with the flag set. The blend route for those jobs remains open.
- **Emulated** (`tools/omdem1mk2_emu_halation_flag.py`): the real settings store holds the stage in sid 961 (written
  through the facade), the patched converter reads it back; 1,260 runs over stage 0..3 / 7 × Art Effect × picture
  mode × capture kind × seed give exactly the stock flag word, plus 0x80 in the 36 gated cases. A build with the
  stage fixed (`EM1_HL_FORCE_STAGE`) passes with `--force-stage` and fails the sid-961 check, so the harness sees the
  stage. `emu_artflags` keeps the stock flag table for every Art Effect (gate off through Monotone).
- **Test release `v0.4c18t`** (stage fixed at 2 because no control sets sid 961 yet): `tools/omdem1mk2_catalog_release.py
  --version v0.4c18t` after `EM1_HL_FORCE_STAGE=2 python3 patches/omdem1mk2/halation/build.py`.
- For camera acceptance after routing is verified, Natural / Vivid / Color Creator stills show a soft glow with Halo
  enabled. Monotone, Art Filter, Art Effect, bursts, RAW+JPEG and movie are regression checks.

## Stock watchdog write path (2026-11-20)

The OM 3.70 stock path at `0x6005aecc` passes 10 to `0x600226fd`. The emulator ran that stock call with
mapped watchdog registers. It changed `0x98e0008c` from `0x13f` to `0x10a`, preserving the upper bits,
then wrote `0x20041001` to `0x98e000a4`. The run stopped before the hardware acknowledgement loop at
`0x60022728`. The startup path, timer units on camera, and time consumed by an E-M1 II image pass still
need confirmation before deciding whether to change the timeout.

**Decision (4g, 2026-11-23): raise the limit to 30 s, keep the 1/3 coverage cap [E].** The E-M1 II has the same two
run-time settings as the E-P7 (v0.31b changed both):
- `0x600792bc` SYS_WDT on: stores 1 at `0x62095e4a`, `mov 10,d0` at **`0x600792c4`**, setter wrapper `0x60079282`
  (`exthu d0` → `0x600226fd`). SYS_WDT's task (`0x60079311`) calls it at start (`0x60079303`), then kicks
  (`0x600792dd`) and waits ≤ 3000 ms on its mailbox (`0x600513e9`) in a loop, like E-P7 `0x6005b287`.
- the flash-operation path: off (`clr d0` at `0x6005aeb0` / `0x6005ae8c`), the operation, then `mov 10,d0` at
  **`0x6005aecc`** (E-P7 `0x6005bcff`).
- left stock: the 1 / 0 settings (`0x60059a4a`, `0x6006ed47`, `0x6057adc4`, the other `0x60079282` callers) and the 10
  before the `bra .` at `0x600cdfb5` (a deliberate hang that the watchdog must end).

The setter writes the 6-bit seconds field (max 63), so 30 is inside the range. Lowering the cap was rejected: on a
night scene it would drop the glow on exactly the frames halation is for, and the E-P7 restarts were fixed by the
limit, not by a cap. Worst case with the cap kept: ≈ 25 instr/px ≈ 5–8 s for the pass, + the Soft Focus development
and ≤ 3 s since the last kick, under 30 s. `tools/omdem1mk2_emu_watchdog.py` runs both settings stock / patched: the
field becomes 10 / 30 with the register's upper bits kept and the handshake written; only those two bytes differ in the
SYS code. Cost: a real hang restarts after up to 30 s instead of 10 s.

## Order

1. Code space: confirmed with the sp1 loaded-end probe above.
2. Find the spare remembered setting and the Soft Focus / CPU-pass sites; emulator fixtures for the capture job.
   Sites: done (static, above). Emulated: flag converter, stage setting sid 961, capture-kind mapper, selector +
   combiner 11/12 with the neutral-blend stubs, blend setup, bus-address mapper. **Step 2 done.**
3. The step 3 flag gate is emulated in `v0.4c18t`. Complete the colour-still blend route before the glow camera test.
4. Halation pass with the global stage and gate above, then the camera control; emulator proof as in §"How", then camera.

## Step 4: tinted halation pass (in progress, 2026-11-23; plan `plans/261123-0838-em1ii-halation-step4/plan.md`)

- **Blend completion [S].** `0x60398ee1` submits at `0x60399008` (`0x60390536`), waits at `0x6039903d`
  (`0x60390293` → `0x603901f3`) and releases records at `0x60399048` / `0x60399053` before returning success.
  The standalone emulator fixture stubs the submit and wait services. `0x6039923c` also calls the body at
  `0x60398ee6` directly, outside the work-list immediate examined in 4a.
- **Work list (4a) [E].** `tools/omdem1mk2_emu_work_list.py` starts at the real capture entry `0x6041ec04`, follows
  the params fill `0x6041dda4` and lets constructor `0x6038f173` choose the builder. The request and capture input,
  heap allocations and logger are fixtures. The ordinary and Soft Focus-only cases reach publication at request+36.

  | Capture fixture | Work-list result |
  | --- | --- |
  | Vivid, Natural and Color Creator, kind `0x1000` / `0x1001`, class 0 | Stock flags `0` and `v0.4c18t` flags `0x80` both use builder `0x603a63f4` and publish identical lists: `0x603a5d7d`, `0x603a5d96`, `0x603a5df6`, `0x60391a9b`. |
  | Art Filter 101, Art Effect 0 | Flags `0x80`, builder `0x60392e0d`. After reduce `0x60398e6f`, the list has `0x6039905e` and `0x60391a9b`. Blend Setup remains pending in `a2` when the builder returns. |
  | Art Filter 101, Art Effect 2 | Flags `0x480`. At `0x60393b9c` the `0x400` branch writes the pending `0x60398ee1` into slot 3 (zero-based), at **job+11020**. The fixture stops after finalizing the primary list, before the secondary setup. |

  The list starts at job+10984 and each item is 12 B. The primary entry at item+0 is called by `0x6038fb5f`
  with `a0 = job`. The runner reached both the original entry and a redirected address after changing just the
  immediate at `0x60393a6b` in emulator memory. The callback dispatch at `0x60392765` uses item+4.
  The planned immediate edit is specific to the tested Art route. **4a still needs a route for ordinary colour
  stills** before `hl_gs` can be validated on those jobs.
- **Pass [E]:** `patches/omdem1mk2/halation/hl_pass.s` = the E-P7 h1/h2 passes A/B/C instruction for instruction, with the
  E-M1 bus guard (0xa0000000..0xafffffff direct; 0x84000000..0x9fffffff and 0xb0000000 up windowed; below 0x84000000
  refused), per-piece window open (lock, mode get, mapper, flush or mode restore, unlock) and the E-M1 allocators.
  `tools/omdem1mk2_emu_halation_pass.py`: 36 cases bit-exact with `tools/omdem1mk2_halation_model.py` (direct, windowed and
  a buffer crossing 0xd0000000, every stage × tint); daylight cap, no highlights, malloc failures, bad format and bad bus
  leave the photo untouched; locks == unlocks, frees balanced, the window mode restored.
- **Not yet:** the wrapper and per-job decision (4a/4b), combiner neutral blend (4c), look tint (4e), Halo control (4f),
  time budget vs the 10 s watchdog (4g). Nothing of step 4 is in a release.
- **Per-job marker (4b) [E, partial]:** the params block of each shot is a zeroed 32-byte stack local; the job constructor
  `0x6038f173` allocates a new 15,484-byte job and copies it word for word to job+4..+35 (`0x6038f2a4`), so params+N =
  job+4+N (job+8 request, job+16 flags). Marker = a magic byte hl_flag writes at params+31 → job+35 (combiner stub:
  request − 11329). `tools/omdem1mk2_emu_job_marker.py`: constructor and work-list builder give identical results with
  the byte 0 or 0xA5 except job+35 itself. Report: `plans/reports/research-261123-0838-em1ii-halation-job-marker.md`.
  Still to prove: the blend setup, combiners and destructor with the marker set, and the other three constructor paths.

### Step 4a: the colour-still route (2026-11-23, emulated; report `plans/reports/research-261123-1123-em1ii-plain-route-completion.md`)

- **No CPU-visible developed image in stock [E]** (`tools/omdem1mk2_emu_plain_route.py`, real capture entry): for Vivid /
  Natural / Color Creator stills the development item `0x603a5df6` (`0x603a44ca`) writes the main JPEG entry (format 0x0702)
  directly. There is no record 0x1000 and no full-size 0x0302 record; the only 0x0302 record is the 160×120 EXIF thumbnail
  intermediate (id 4 on 4:3, id 5 on other aspects). The development item waits for its request synchronously.
- **4:3 jobs get three items, not four:** the last item `0x60391a9b` is appended only when job+23 (aspect index) ≠ 1
  (`0x60390102`). The earlier "four items" result used aspect index 0, which is not a real value.
- **Possible route (not built):** give the main JPEG entry +42 bit 3 (0x208) on marked jobs so development writes a
  full-size record 5 (0x0302, stride = W, offsets 0, 2·W·H — the layout `hl_pass` accepts) and `0x60391a9b` encodes it;
  run the pass in a wrapper behind the immediate at `0x6039011f` (data edit; runner calls it with a0 = job). Needs three
  instruction hooks (main-entry flag `0x60421bbd`, the 4:3 aspect test in `0x603a573d`, the 4:3 append test `0x60390102`),
  careful handling of the second (thumbnail) encode, and costs one extra full-size buffer (~40 MB) per marked shot. The
  review image would show no halation. Alternative not yet tried: route marked jobs through the Art builder `0x60392e0d`.
- **Art route for colour stills [E]** (`tools/omdem1mk2_emu_art_route.py`; report
  `plans/reports/research-261123-1709-em1ii-art-route.md`): repointing the colour-builder call at `0x603900ec`
  (`dd 84 3b 01 00 00 04`, a0 = job, frame `[],4` like the Art call `0x60391c1c`) for marked jobs gives the
  Soft-Focus-only Art list `0x60392df2, 0x6039276e, 0x60398e6f, 0x6039905e, 0x60391a9b`. The development then writes a
  full-size record 0x1000 (0x0302, 5184×3888) and waits for it; `0x60398e6f` blurs into 0x1061; `0x6039905e` blends
  0x1000 + 0x1061 (combiner 11) into record 3 and encodes the main JPEG. The development request equals the plain one in
  every colour field (key, picture mode, profile, sectors, 617/618, tone, NR, sharpness, aspect) **except** the outputs and
  `req+1838` = 0x0400 (written at `0x6039272f`), which runs combiner 13 `0x603dd101` inside development with fixed
  constants. Whether that changes pixels needs a camera A/B. Plan: pass on 0x1000 in a wrapper behind the immediate at
  `0x60393a54` (`mov 0x60398e6f,d1`) + neutral combiner 11 for marked jobs. Cost ≈ a stock Soft Focus shot (≈121 MB live).
- **Step 4 route built [E]** (`patches/omdem1mk2/halation`: `hl_flag.s` + `hl_route.s` + `hl_pass.s`, 1,672 B at
  `0x612e7000`; `tools/omdem1mk2_emu_halation_route.py`, stage fixed at 2 on v0.4c17):
  - `hl_flag` also writes the job marker `0xA0 | (tint − 1) << 2 | stage` at params+31 (→ job+35) when it sets 0x80
    (tint red for now); `emu_halation_flag` checks the marker in every gated case and 0 elsewhere.
  - `hl_route` (colour-builder call at `0x603900ec` repointed, 7-byte `call` kept): marked jobs → Art builder; Vivid /
    Natural / Color Creator get the Art list with `hl_ob` in place of the blur; Monotone stays byte for byte stock.
  - `hl_ob` (word at `0x60393a54`): a marked job reaches `hl_pass` with the record of 0x1000 and `d0 = tint << 4 | stage`,
    then the stock blur runs with identical submits, waits and job bytes; unmarked jobs never reach the pass.
  - `hl_c11` / `hl_c12` (table words `0x6053e164` / `0x6053e16c`): neutral blend for marked jobs, stock 600 / 424 otherwise.
  - Build switches: `EM1_HL_FORCE_STAGE=1..3` (no Halo control yet), `EM1_HL_NO_PASS=1` (Art route + neutral blend, no
    pass: the camera A/B of combiner 13 against plain stills).
  - Open: look tint (4e), Halo control writing sid 961 (4f), time vs the 10 s watchdog (4g), the camera A/B, and which
    blend input carries record 0x1000 (assumed A, as on the E-P7; if not, the neutral weights must swap).
- **Look tint (4e) [E]:** `hl_flag` takes the tint from the active look: P (sd_loader `p_get`) → `P_ACTIVE` = 1 → the record
  of `P_LOOK` (card buffer when the editor applied the card and the index is inside the pack, else the built-in table
  `0x60bc8150`) → byte +47 (1 red, 2 amber, 3 warm, 4 cool) into the marker; no P, no active look or a tint outside 1..4
  keeps red. `emu_halation_flag` checks no P, inactive, all 16 built-in looks, card looks 2/3/4 and an index past the pack.
- **Halo control (4f) [E]:** `color_creator_wheel` built with `EM1_CC_HALO=1` (`edits_halo.json`; the default
  `edits.json` is byte for byte unchanged) adds page 4 "Halo Off/Low/Med/High": RIGHT / LEFT step sid 961 through the
  facade, clamped 0..3, a stored value outside 0..3 counts as Off; the code is section `.hlui` at `0x612f0000` in the
  gap the halation patch loads (two 9-byte branches in the Section 6 cave, which ends at `0x612e6fe4`).
  `tools/omdem1mk2_emu_halo_page.py`. Cosmetic: the SCP tile on page 4 shows page 0's mode label (`and 3`).
- **Time (4g) [E count, I time]:** instruction counts of `hl_pass` (640×448, scaled per pixel): no highlights ≈ 1
  instr/px (pass A only); a night scene with lights covering 19 of 70 cells ≈ 20.5 instr/px; above the 1/3 coverage cap
  the write pass is skipped (≈ 1 instr/px). Windowed access adds 1–2 %. At the E-P7's measured 0.2–0.33 s per instr/px
  for a full frame that is ≈ 0.2–0.3 s without lights and **≈ 4–7 s** for a night scene with lights (more near the cap),
  on top of the Soft Focus passes — close to the stock 10 s watchdog (`0x6005aecc` passes 10). The E-P7 restarted on
  bright frames until v0.31b raised its timeout to 30 s. **Decided:** limit 30 s, cap kept (see "Stock watchdog write
  path" above).
- **Camera test builds (4h) [E]** (`tools/omdem1mk2_catalog_release.py`; v0.4c17 + `edits_halo.json` + halation, stage
  fixed at 2, watchdog 30 s):
  - **`v0.4c22t`** diagnostic (`EM1_HL_NO_PASS=1`): Art route + neutral blend, no pass. Same scene as v0.4c17 → the
    JPEGs must match; a difference is combiner 13 (`req+1838`) in the Art development.
  - **`v0.4c23t`** glow: the full pass. Night scene with point lights in Vivid / Natural / Color Creator: tinted glow
    around the lights; Monotone, an Art Filter, burst and RAW+JPEG stay stock; note the save time and any restart.
  - Sealing runs every v0.4c17 check plus `emu_halation_flag --force-stage 2`, `emu_halation_route` (with `--no-pass`
    for c22t), `emu_halo_page`, `emu_watchdog` and, for c23t, `emu_halation_pass`, all on the sealed spec. The Halo page
    stores sid 961 but the stage stays 2 in both builds.
  - **Narrowed after review (replaces v0.4c20t / v0.4c21t, never flashed) [E]:** the first gate ORed 0x80 into the
    flag word in the converter, so a marked job that the constructor (`0x6039009a`) sends to another builder
    (`0x60399eb9` when params+22 ∉ {0, 4}, `0x60391c25` when params+27 ≠ 0, the Art builder for class 1) or a capture
    kind nobody emulated (High Res, HDR, bracketing, Live Composite) would have carried Soft Focus into a route stock
    never gives it. Now `hl_flag` writes only the marker, and only for kinds 0x1000 / 0x1001; `hl_route` ORs 0x80 into
    job+16 just before `jmp` to the Art builder; `hl_marked` (combiners 11 / 12) needs the marker, stage bits ≠ 0 and
    0x80 at job+16, so a combiner request outside a job matches only by a three-way coincidence (stock jobs have job+35
    = 0, from the zeroed params block). `emu_halation_flag`: 1,680 runs, flags = stock exactly, marker only in the 36
    gated cases (kinds 0x1002 / 0x2000 added). `emu_halation_route`: Vivid of kinds 0x1002 / 0x2000 / 0x2001 / 0x1008
    byte for byte stock; combiners: marker without 0x80, stage 0 and another byte give stock. The marked job for modes
    1 / 2 / 10 is byte for byte the v0.4c21t job except the hl_ob address.
  - **Release candidate `v0.4c24` [E]:** v0.4c23t with the stage read from sid 961 (default 0 = Off). Sealing adds
    `emu_halation_flag` without `--force-stage` (the real settings store), `emu_spare_setting` and
    `emu_halation_route --stage-setting`, which runs the sealed image with only hl_flag's own getter call (label
    `hl_stage_get`) replaced by `mov 2,d0`. With that call fixed to 0 (Halo Off, the default after flashing) the capture
    jobs for Vivid, Natural, Monotone, Color Creator, Art Filter 101 and kinds 0x1001 / 0x2001 / 0x1008 are stock byte
    for byte, except the Soft Focus list naming `hl_ob` for the blur (hl_ob = stock blur on an unmarked job).
    `tools/omdem1mk2_check_gap_refs.py` repeats sp1's scan on the catalog image: in every loaded section only the
    end-getter stub uses an address in `0x612e7000..0x61300000` as an operand; the 32 branch-shaped hits are data decoded
    as code (stock never loads the gap, so a real branch there would crash stock). Camera order and pass criteria
    (Vietnamese, one flash of v0.4c24 recommended): [thu-may-halation.md](thu-may-halation.md).
  - **Where the camera puts record 0x1000 [E] (`tools/omdem1mk2_emu_image_heap.py`):** the development allocates it
    through the job callback op 19 (`0x6038bb47` → `0x60380399` → capture callback `0x6041f8ae`, table `0x605569d8` →
    `0x6041fcf6`). For kind 0x1000, `+81` = 0 and `+76` = 0x1000, so `0x6041febc` allocates in mode 0 (`0x604254fe` →
    `0x60411126` → `0x604111b7`) from image heap 0 or 1 (table `0x60553370`, chosen by the heap mode `0xa26d4f84`). The
    init `0x6041157a` (init table `0x6058017c`) creates them with fixed constants: `0x8dc64e00` + 281 MB and
    `0x9b758800` + 62.5 MB, both ending at `0x9f5e7400`. The camera's own init and allocator, emulated, return
    `0x8dc64e00` / `0x9b758800` for the 40 MB record. Both heaps lie inside 0x84000000..0x9fffffff, which `hl_pass` maps
    through the window, so the pass does run on the camera. `emu_halation_pass` now also runs it bit-exact at both heap
    bases and across the 0x90000000 and 0x98000000 (0xb8 window) edges (84 model cases).
