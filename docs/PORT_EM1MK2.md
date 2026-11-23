# Porting Caduceus to the Olympus OM-D E-M1 Mark II

**Firmware Target**: Olympus OM-D E-M1 Mark II, Firmware v3.70 (Build `3700`, Model `0x1250`)  
**Package File**: `OLY_E_125_3700_0000_0000.BIN` / `E1259999.BIN` (93,050,944 bytes)  
**Main CPU**: Panasonic MN10300 (AM33-2) 32-bit RISC  
**Main Base VMA**: `0x60021020` (note: E-P7 is `0x60020020`)  
**Update Container**: Scrambled `OE` format (5 components: 0x100, 0x101, 0x106, 0x10e, 0x102)  
**SD Card Directory**: `EM1MOD/` (update file in `DCOLYMP/E1259999.BIN`)

---

## 1. Architecture & Memory Overview

Unlike the PEN E-P7 (TruePic IX, 26 MB main program, base `0x60020020`), the E-M1 Mark II uses the TruePic VIII processor with a 23,068,608-byte main image starting at `0x60021020`.

### Verified Loaded Section Caves (FF Tails)
All patches reside in non-volatile runtime-loaded section caves copied during `c_startup` / `application_startup`:

| Section | VMA Range | Cave Location | Usable Size | Role in E-M1 Mark II Port |
| :---: | :--- | :--- | ---: | :--- |
| **2** | `0x602ae000 - 0x60580800` | `0x60580190 - 0x60580800` | 1,652 B | SD loader gate (`0x60580200`) |
| **5** | `0x60796000 - 0x60bc8800` | `0x60bc8140 - 0x60bc8800` | 1,728 B | Built-in looks (16 × 64 B at `0x60bc8150`, v0.3b2) |
| **6** | `0x60bf1000 - 0x612e7000` | `0x612e68c4 - 0x612e7000` | 1,852 B | Color Creator controller, look selector, guide label & SCP tile (`0x612e6900`). **Corrected 2026-11-11**: earlier this said `…0x61300000` / 104 KB; the cave ran past the real end until v0.3b2 |

---

## 2. Ported Feature Status (v0.1)

### 1. Video Recording Limit Removal (`rec_limit`)
- **Sites**:
  - `0x603549d7`: `1740s` (29 min) $\to$ `32400s` (9 hours)
  - `0x603549dc`: `7200s` (2 hours) $\to$ `32400s` (9 hours)
- **Status**: Tested and verified. Directly ported from the E-P7 / PEN-F pattern.

### 2. Focus Stacking Limit Removal (`focus_stacking`)
- **Site**: `0x60656a4a`: `c9 04` (`bne`) $\to$ `cb cb` (`nop nop`).
- **Effect**: Eliminates the PRO-lens whitelist check, allowing in-camera automated focus stacking with any autofocus lens (Olympus non-PRO, Panasonic, Sigma).
- **Status**: Tested and verified.

### 3. Dynamic SD Card Looks Loader (`sd_loader`)
- **Site** (v0.4c15): `0x602f7bf7` in the HLS event loop `0x602f7b11` (the E-P7 loop `0x602c7f5a`'s counterpart), on the
  half-press event `0x02000100` / `0x02010100` once all sections are loaded (`0xa2767afc & 0x1ff`). Until v0.4c14:
  `0x6023d0db`, believed to be a half-press classifier; it is the command-256 branch of an unrelated message loop and
  never runs on a half-press (camera, v0.4c14: `C0.0`). **Camera v0.4c15: `C1.1` after a half-press — loads [C].**
- **Cave**: `0x60580200` (Section 2).
- **Behavior**: on each half-press the loader tries SD slot 1 (`C:\EM1MOD\LOOKS.BIN`), then slot 2
  (`D:\EM1MOD\LOOKS.BIN` if slot 1 did not open). It validates the shared `EP7B` v3 header, size (64-byte
  header plus 1–32 64-byte records), and CRC-32. The first valid pack stays in memory for the session.
- **Status**: `C1.n` means the file loaded in `n` attempts. Missing files are retried for up to eight half-presses
  (`C0.n` while trying, then `CF.8`). An opened file that fails validation gives `CF.n` immediately.
- **State**: the shared heap block P holds the buffer, count, attempts, and state (pending, loaded, or failed).
- **Verification**: the v0.4c15 emulator harness enters the HLS hook `0x602f7bf7` with each event. The
  camera confirmed loading with `C1.1`. Distinct card look names and rendering in live view and saved JPEG
  still need a camera check. See [WORKLOG](../WORKLOG.md) for the earlier hook and card-state investigation.

### 4. In-Camera Look Selection via Live View Color Creator (`color_creator_wheel`)

**Status:** v0.3b5 on camera: colour (12-sector S, H/L), tone (HL/MID/SH), Chroma and Strength all confirmed. Details and addresses: `docs/OMD-EM1-II/ARCHITECTURE_AND_MEMORY_MAP.md` §6–7.

| Build | Camera result |
|---|---|
| v0.1 | Look name changes, image doesn't; Chroma/Luminance/Midtones change only the banner; SCP rear dial seems dead |
| v0.2b1 (2026-11-10) | Saturation always 0; looks all look the same; **garbage look names**; hue/saturation/chroma do nothing |
| v0.2b2 (2026-11-10) | Some looks load but render wrongly (e.g. Eterna B&W-looking, vividness −3): Color Creator's one hue + one vividness value cannot reproduce a look |
| v0.3b1 (2026-11-11) | Colours **do** change (the E-P7 COLOR engine route works), but only 2 looks have names, only 2–3 distinct looks, the rest repeat; chroma/hue do nothing on those |
| v0.3b2 (2026-11-11) | Colours change better. After a B&W look (vividness −4) every look stays B&W; only hue (Color Creator's own control) affects the image |
| v0.3b3 (2026-11-11) | B&W bug gone; looks change colour (and tone on look change) but subtly; Chroma and Luminance adjustments show no effect |
| v0.3b4 (2026-11-11) | **Velvia confirmed on camera**: a JPEG of the Panel's sample photo matches the Panel preview closely (red ground, saturated blues, deepened shadows, neutral sky); blues lean slightly more cyan. The look reaches stills, not just live view. An earlier violet cast was from photographing a monitor through live view |
| v0.3b4 page checks | Strength works; Chroma works (+5 visibly punchier); **Luminance: values stored but no effect** in live view or JPEG (0/0, ±5/±5) |
| v0.3b5 | Tone (looks + Luminance page) now writes the values the image request reads: 384 Highlights, 692 Midtones, 383 Shadows (same as the E-P7). **Camera: works** in live view and JPEG (±7/±7: highlights ±14, shadows ±24) |
| v0.3b4 (build) | Manual adjustments re-trigger the live view (re-write vividness, which is what look changes do); new **Strength** page (x1 / x1.5 / x2 / x3 on S, hue and light) |

**Cause of the v0.3b3 report:** live view re-runs the colour stage only when certain settings are written. A look change writes vividness (618) and its effect shows, while Chroma (no setting write) and Luminance (449/450 only) did not trigger that refresh. The core setter `0x60863a8a` has no unchanged-value skip, so v0.3b4 re-writes 618 with its current value after each manual step. "Subtle" is expected at E-P7 strength (S ±5 steps, under Color Creator's own processing). The builder scales S linearly with no clamp, so Strength allows S up to ±10 and H/L up to ±15.

**Cause of the v0.3b2 report:** (1) colour looks never reset Color Creator vividness, and Color Creator's own processing still runs on top of the COLOR engine, so a mono look's −4 stuck. (2) The tone writes went to 889/890/891, which nothing on this body reads (no descriptor, no code). The live controls are **449 (Highlights) and 450 (Shadows)**, each with a stock apply callback. The E-M1 II has no Midtone control. Chroma likely looked dead only because everything was stuck in B&W; re-test.

**Root cause of the v0.3b1 report (and part of every earlier one):** Section 6 is loaded only up to `0x612e7000`, not `0x61300000` as the docs said. The Color Creator cave ran past that point, so its data tables (v0.1–v0.2: preset names and values; v0.3b1: the built-in looks) were never in RAM: only the first look or two were real, and the rest read leftover memory. v0.3b2 puts the built-in looks in the Section 5 tail, and every release is now checked against the firmware's own section table. The card file wasn't loading either: with the card, all names would have come from it. The banner now shows why.

**Root cause of the v0.2b1 report:** all patch state (card-loaded flag, card buffer pointer, look index, page, dial flag) lived at `0x621e2f76..0x621e2f87`, inside a stock 32-entry ring of `{callback, argument}` pairs at `0x621e2f74`. Stock code overwrote it, giving garbage names, lost looks and wrong pages. Our writes also landed in queued callbacks. It was there in v0.1 as well, so most v0.1 symptoms probably share this cause. v0.2b2 keeps all state in one heap block P whose 16-bit handle sits in compiler padding (`0x621e24ae`, checked statically, not yet camera-proven) and is checked with a magic word, as the E-P7 does. If P is ever lost, the handlers behave like stock and the state is rebuilt; nothing reads garbage.

Also fixed in v0.2b2: the card loader's CRC check could overwrite a saved register of its caller (missing call slot), and its `free` was for the wrong heap pool (`0x600232d9` instead of `0x6002323d`). Look names are now limited to printable characters.

**"Saturation always 0"** was reported on v0.2b1. The 12-sector colour route arrived in v0.3b1, and the Chroma
adjustment was confirmed in v0.3b4 after adding a live-view refresh.

#### v0.3: the E-P7 colour engine behind Color Creator
The E-M1 II's colour stage is the E-P7's (and PEN-F's), byte for byte: selector `0x603ec82c`, per-sector builder `0x603ec642`. On the E-P7, Caduceus feeds looks through it. Stock runs it only for COLOR picture modes (job key 11), which the E-M1 II has no way to select. v0.3 makes it run for **Color Creator** while a Caduceus look is picked, the way the E-P7 got looks into movie mode (`docs/MOVIE_COLOUR.md`):
- the look's **12-sector saturation** goes into the request the builder reads, and the COLOR branch runs;
- the look's **per-sector hue and light** are written into the builder's output exactly like the E-P7's `lv` hook;
- **tone** (H/M/S) uses the request-side settings 384/692/383, confirmed on v0.3b5.
Color Creator stays the screen you pick looks on. Its own hue/vividness wheel is not used for colour looks. **Mono looks** still only lower vividness (no B&W path yet). Addresses: `docs/OMD-EM1-II/ARCHITECTURE_AND_MEMORY_MAP.md` §7.7.

**Card file: `EM1MOD/LOOKS.BIN` is now the E-P7 file** (`EP7B` v3, 64 + 64 bytes per look, up to 32 looks). An E-P7 `LOOKS.BIN` or a Control Panel export (either camera target) works when copied to `EM1MOD/`. The old 2,080-byte `EM1B` file is no longer read. Without a card, 16 built-in looks are used (Provia … Acros).

#### Why looks live in Color Creator
The E-P7 and PEN-F have COLOR/MONO picture modes, a front Profile Control dial and per-profile editor screens. The E-M1 Mark II has none of that UI. Its TruePic VIII pipeline does have the plumbing: the image request builder reads COLOR/MONO profile numbers, and it copies an effective 12-sector saturation into the request. The per-profile saturation (3 profiles × 12) and tone settings exist too (§7.6). But there is no screen or picture mode that reaches them. Color Creator is the only stock screen with a colour wheel, and its hue (617) and vividness (618) go straight into the request, so it hosts the looks:
- **Works through stock settings:** hue, vividness and Highlights/Midtones/Shadows.
- **Needs new firmware code:** 12-sector saturation (planned: read-site override at the builder's `0xF6EA` reads), per-sector hue/light, and monochrome. Color Creator has no B&W, and its lowest vividness is −4.

#### What the editor does in v0.4c15
- **Page 0 (Film):** the arrows pick a look from the loaded card file or the 16 built-ins. The dials run the
  stock wheel. The banner shows the look name and reports `E58` (camera busy) or `E16` (value rejected)
  when a Color Creator value write fails.
- **Page 1 (Chroma):** adds a −5..+5 offset to all 12 saturation sectors for colour looks.
- **Page 2 (Luminance):** the front dial and Left/Right change Highlights (384). The rear dial and Up/Down
  change Shadows (383). Midtones (692) come from the selected look.
- **Page 3 (Strength):** the front dial and Left/Right scale sector saturation, hue and light from x1 to x3.
- **SCP tile:** the bottom cell shows the look name.

#### Fixed in v0.2b1 (v0.1 mistakes)
1. **E-P7 sid numbers.** This body's numbers are the E-P7's minus 2 in this range. v0.1 wrote saturation to 915..926 (here: derived effective saturation 913..924 plus COLOR1 sectors) and tone to 449/450/963/964/965 (an untraced pair, plus one key from each of three COLOR-profile tone sets). v0.2b1 writes tone to the ordinary-mode settings 889/890/891 and leaves saturation alone until it can be done properly.
2. **Registers.** The arrow handlers overwrote `d2`/`d3` before saving them. The stock dial loop keeps its detent counter in exactly those registers, and the dial wrappers changed the router's `d2`.
3. **Invalid vividness −5** for mono looks (valid range −4..+3). It is now clamped to −4.
4. **Untraced "commit/refresh" calls** (`0x602da6b9`, `(0x61fbfc94)` vtable +76) removed.
5. **Init tone sync** read through `0x602da5f9`, which is not the sid getter. It now uses facade GetValue.
6. **Card file (`make_looks_bin.py`):** colour looks had raw saturation written over the tone bytes `+33..+44`, so a card look's "tone" was its saturation numbers. It now matches the Control Panel's `lookRecord()`. The firmware checks the tone flag (`+32`), and no longer takes vivid/hue from `+38/+39`.

#### Earlier claims that were wrong
- "`SetValue` rejects tone/saturation in Color Creator mode": no. It rejects only on global camera-state bits; see `ARCHITECTURE_AND_MEMORY_MAP.md` §7.3.
- "Settings applied via `em1_set_setting` (`0x602da60b`)": v0.1 called the facade, not `0x602da60b`. Calling `0x602da60b` froze the camera in an earlier test.
- Validator value-array addresses for 449/450/617/618 pointed at unrelated data. The real lists are in `REA_FIRMWARE_FUNCTIONS_REFERENCE.md` §1.

#### Camera checks for v0.4c15
1. Copy `DCOLYMP/` and `EM1MOD/` (the new 1,088-byte `LOOKS.BIN`), flash, half-press once, then set the picture mode to Color Creator and open its editor (this records which mode the looks belong to).
2. Page 0 banner: look name, card status (`C1.1` for a load on the first half-press), then `K` and four hex
   digits. A trailing `+` indicates that the colour hook has applied a look.
   - **no `K…`**: the colour-stage hook never ran (or ran before the editor opened); half-press and look again;
   - **`K…` without `+`**: the hook runs but the look was not applied (mode check failed); report the digits;
   - **`K…+`**: the look is applied to live view frames.
3. With `+`: step Provia → Velvia → Eterna → Bleach Bypass. Velvia should be clearly more saturated, Eterna muted but **in colour**, Bleach Bypass very desaturated. Take a still with each and compare with the live view.
4. Page 1 (Chroma): left/right should visibly change overall saturation. Step to Tri-X (B&W), then back to Velvia: Velvia must be in colour again.
4b. Page 2 (Luminance): front dial / left-right changes highlights, rear dial / up-down changes shadows.
4c. Page 3 (Strength): front dial / left-right steps x1 → x3. Velvia and Classic Chrome should get much stronger; report the strength that looks right.
5. Switch the picture mode to Natural: the image should go back to stock Natural.
6. Export a pack with uniquely named, visibly different looks via the Control Panel. Copy it to
   `EM1MOD/LOOKS.BIN`, power-cycle, then check the custom names, live view and saved JPEGs.

#### Architecture
- **Parent Controller Table**: Entry 79 at `0x61259c40` (key `0x13a9` = 5033, Live View Color Creator) in the 92-entry table at `0x61258af8` (searched by `0x60e8b6be`).
- **Hooks** (cave at `0x612e6900` in Section 6's `0xFF` tail `0x612e68c4..0x612e7000`): record words `+04` init, `+12/+16/+20/+24` arrows (also called once per detent by the stock dial loops `+28/+32`), `+28/+32` dial wrappers (`dial_active` flag), `+36` other events (TRASH cycles pages), `+44` INFO cycles pages and stays in the editor; guide label part 3 at `.data` init word `0x60297fb4`; SCP cell call at `0x60e25ec8`.
- **Wheel sync**: after a write, `0x60e4a59c` re-reads each child's value and index, and `0x900c` makes the child commit and redraw (§7.5).

---

### 5. Sharpness as a linear scale (`sharp_scale`, test release v0.4c19t)

**Status: emulator-checked, not camera-tested.** v0.4c19t = v0.4c17 + this patch (no halation).

Sharpness −2..+2 becomes off / 25 % / 50 % / 75 % / 100 %, where 100 % is stock +2. The idea comes from the
E-M1 III mod (dfeldt91-blip/E-M1-Miii, `sharp_scale`; it has no license, so only the idea is reused, the stub is written
here). Settings, menus and EXIF keep the −2..+2 values. Flat and Log jobs (keys 2000 / 2001) stay stock.

**Where the gain comes from [V].** The ISP sharpening-gain helper `0x603e8b..0x603e8c97` has the E-P7's shape
(`0x603ab8fe`, `docs/SHARPENING_OFF.md`):
- Index = base[class] + Sharpness, where Sharpness is the signed byte at request +1795.
  - The base tables are `0x6052a940` (6,5,4,4,6,7) and the alternate `0x6052a946` (5,5,4,4,5,6).
  - Flat/Log take Sharpness + 4 on the main path.
  - The index is clamped to 0..10.
- Gain = u16 table (`0x6052a94c` = 0,16,64,112,184,256…, or `0x6052aaca` when +1810/+1811 is set) × ISO amount / 256, capped at 255. Then it is scaled again by d2 / 256 and capped.
- The final byte is stored at output +2.

The other users of these tables (`0x603d42af`.. in five functions) only copy them into a record.
`0x603e06ff` is a second index helper with its own tables (`0x60521aa8`; multiplier 256 up to index 5, rising above).
It is not touched. At −2..0 it stays at 256 for most classes [I].

**Patch** (`patches/omdem1mk2/sharp_scale/`, `ss.s`, 94 B at `0x605d2f94..0x605d2ff2`):

| Site | Stock | Now |
|---|---|---|
| `0x603e8bfa` | `movbu (1795,a0),d1; extb d1` | `jmp ss_index`: index uses Sharpness +2 (Flat/Log: real Sharpness) |
| `0x603e8c83` | `mov (40,sp),a0; movbu (50,sp),d0` | `jmp ss_scale`: gain × (S+2)/4 (k ≤ 0 → 0, 1 → /4, 2 → /2, 3 → ×3/4, ≥ 4 → stock) |

- Code sits in the Section 3 tail, after the aspect AF/AE stubs. `build.py` refuses to build if they overlap.
- No mul/div (audit rule), no stores outside the stack frame.
- Neither hooked range is a branch target inside the helper.

**Emulated** (`tools/omdem1mk2_emu_sharp_scale.py`, 3,780 runs, part of the v0.4c19t seal): the helper tail runs from
`0x603e8bb6` to its `ret`. Inputs cover Sharpness −3..+3, classes 0..5, both base tables, all three gain tables, three
ISO amounts, and keys 11 / 2 / 1 / 2000 / 2001.
- Stock output matches a Python model of the code.
- Patched output = stock(+2) scaled as above.
- Flat/Log are unchanged (1,512 runs).

Example (class 1, amount 37):

| Sharpness | −2 | −1 | 0 | +1 | +2 |
|---|---|---|---|---|---|
| Stock gain | 16 | 26 | 37 | 37 | 37 |
| Patched gain | 0 | 9 | 18 | 27 | 37 |

Stock −2 keeps about 43 % of the gain. Stock +1 and +2 saturate to the same value, as on the E-P7.

**Not emulated / unproven:**
- The callers of the helper (live view vs capture vs movie).
- That the gain reaches the JPEG and the movie.
- The resize path.
- The `0x603e06ff` multiplier.
- How playback and EXIF show the value.

**Camera checks for v0.4c19t:**
1. Shoot a tripod scene with fine text, ISO 200, Natural, at Sharpness −2, 0 and +2.
   - −2 must look softer than stock −2, with no halo.
   - +2 must match stock +2.
2. Repeat at ISO 3200 and in Vivid.
3. Record a movie in Flat at −2 and at +2: it must look like stock.
4. Play back each shot and cycle the INFO pages: the camera must not hang.

## 3. Building & Testing

Use **v0.4c17** for the OM catalog E-M1 Mark II 3.70 package. This is an emulator-checked test release awaiting camera validation.

```bash
# List available releases for the E-M1 Mark II
python caduceus.py list --camera em1mk2

# Download the matching stock package from OM and build
python caduceus.py build --camera em1mk2 --release v0.4c17 --out out/em1mk2-v0.4c17

# Verify the built files
python caduceus.py verify out/em1mk2-v0.4c17
```

For a local download, add `--stock PATH` to the build command. v0.4c16 and v0.4c17 pin the stock SHA-256
`691a8a8e90af75b3848b70856a3a49ef24d72394cdfd2766fa37bdfe6325de70`.
v0.4c15 still uses its original `f0c25dd8…` image.

v0.4c16 retains the v0.4c15 edits and changes the catalog stock loader's Section 1 end from `0x60257000`
to `0x60257800`. The added 2 KiB are padding in catalog stock and contain the v0.4c15 aspect code and labels
after patching. The emulator checks the loader's transfer arguments, aspect switches, menu labels, SCP bitmaps,
AF, SD look loading, recording limits and the focus-stacking branch. Camera startup, flash transfer, card-driver
behavior and rendered photos still need camera testing. v0.4c17 also checks card loading before and after
opening Color Creator. If `C1` first appears while the editor is open, reopen Color Creator to switch to
the first card look. Until then, the editor and SCP label continue to show the active built-in look.

**Why the catalog stock loads less (static, 2026-11-20).** The two 3.70 files differ in Section 1 content, not only
in its end word. In `f0c25dd8…` a function started at `0x60256ff0` after linker padding and ran to about `0x60257578`
(end word `0x60257800`). In `691a8a8e…` everything from `0x60256ce8` is `0xFF` and the end word is `0x60257000`: OM
dropped that function and the linker rounded the section end down. In the catalog image nothing uses
`0x60256ce8..0x602577ff`: the only 32-bit value in `0x60257000..0x60257fff` (cached, uncached `0xa…` and `0x8…`
aliases) that is an instruction operand is the end word `0x60042b4d` itself, and no relative `call`/`jmp`/`calls`
targets the range (the five byte-pattern hits are inside `mov imm32` operands or ASCII / string-pointer tables). So
loading the 2 KiB again overwrites only padding. Still unproven: that no code computes an address there at run time
(the camera boot + 65:24 test).

The release was sealed with `python3 tools/omdem1mk2_catalog_release.py --stock PATH --version v0.4c17` after
rebuilding the wheel edits with `python3 patches/omdem1mk2/color_creator_wheel/build.py`. The sealer uses the MN103
emulator and cross-toolchain and creates a fresh release directory. To repeat the focused check on an existing release,
run `python3 tools/omdem1mk2_emu_color_creator.py releases/em1mk2/v0.4c17/edits.json`.

### SD Card Deployment
1. Confirm the camera is an Olympus OM-D E-M1 Mark II on 3.70 and has a fully charged battery.
2. Copy `DCOLYMP/` and `EM1MOD/` to the root of the SD card. If the card already has your
   `EM1MOD/LOOKS.BIN`, keep that pack. The one-press builder preserves it automatically.
   Keep `restore/E1259999.BIN` on your computer.
3. With the camera off, insert the card into Slot 1. Hold **OK** while switching on the camera.
4. Wait for the activity LED to blink steadily (~2 Hz) before switching off or removing the card.
5. Run the [camera validation checklist](../plans/2026-11-19-em1-ii-release/phase-02-camera-validation.md).
