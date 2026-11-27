# Changelog — Caduceus for Olympus OM-D E-M1 Mark II

Firmware modification package for the Olympus OM-D E-M1 Mark II (firmware v3.70 / build 3700 / model `0x1250`).
Container update package: `E1259999.BIN` (93,050,944 bytes) installed via `DCOLYMP/` with the **OK** button held during power-on.

---

## v0.4c26t — 2026-11-27 (look WB camera-test build; emulator-checked, not camera-tested)

- v0.4c25t plus one feature: **a colour look's WB shift is applied.** Its record's `a_b` / `g_m` (−7..7, flag +25)
  replace the stored WB fine-tune at the 14 image-pipeline reads (12 in the capture block, 2 in the compact slot)
  while Color Creator shows an active colour look. Menus keep the user's values; nothing is written.
- Stays stock: other picture modes, no active look, mono looks, looks without a WB shift, **CWB** (a chosen colour
  temperature is kept, as on the E-P7; this body would otherwise apply the fine-tune in CWB too), and in-camera RAW
  development.
- **Behaviour change:** five built-in looks (and the same looks in the card pack) carry a WB shift the camera ignored
  until now, so their JPEGs change: Nostalgic A-B +3, Gold 200 +2, Kodachrome64 +1, Portra 400 +1, CineStill800 −3.
- Code: `patches/omdem1mk2/look_wb` (222 B at 0x612f1000, in the 100 KB gap after look memory's restore), built with
  `EM1_LOOKMEM=1` so its `p_get` call matches this sd_loader; the seal refuses the other build.
- Emulator: every v0.4c25t check, plus `emu_look_wb`:
  - each of the 14 sites across 27 states: stock in every register (except psw) whenever the look does not apply;
    the look's value, sign-extended like the getter, with the other registers as stock, when it does;
  - the capture WB segment run natively for category 1 × preset 0..14 and categories 0 / 2 / 3 / 4: no look = stock
    byte for byte; a look = the stock block with that look stored as the fine-tune; CWB = stock.
- Not emulated: WB bracketing and the gain calculator after the segment (they read only the capture block, which
  matches the stock one exactly), the compact slot's consumer and live view. On the E-P7 live view did not show the
  shift. Camera test: `docs/OMD-EM1-II/thu-may-look-wb.md`.
- Look switch order (`color_creator_wheel`): the editor now clears `P_ACTIVE` before it writes a new `P_LOOK` / `P_INIT`
  (arrow step and editor entry), so the colour stage and the WB stub never pair one look's state with another's look
  index. Only the look memory wheel build ships here; v0.4c25t keeps the wheel it was sealed with.
- Known limit: the stub reads the WB category at read time, so a category the capture remapped away from CWB leaves the
  look's WB off (the safe direction).
- Sealed with 23 checks; `E1259999.BIN` SHA-256 `26135ee0…`, `edits.json` `bc44f149…`. Rebuilt and verified with
  `caduceus.py build` / `verify` (Windows Python) from the catalog stock file.

## v0.4c25t — 2026-11-24 (look memory camera-test build; emulator-checked, not camera-tested)

- v0.4c24 plus one feature: **the Color Creator look survives power-off.** A look chosen with the arrows in the editor
  is stored in sid 965 (property 0xF719 index 1, a setting this body never uses) as `1 + look + 32 × card`. After
  power-on, the first half-press, or opening the editor if that comes first, rebuilds the look in RAM. A card look waits
  until LOOKS.BIN is read. Tone and vividness are stock settings the camera already keeps. A restored colour look ends
  with one SetValue(618) of its own value, as the editor's `lv_refresh` does, so live view shows the look at once; the
  camera showed in v0.3b3 that a change to P alone does not redraw it.
- Not remembered: Strength (back to x1), Chroma (back to 0). A full reset clears the remembered look; the camera then
  behaves as v0.4c24. When the editor switches itself to card look 0 because LOOKS.BIN was read after a built-in look
  was chosen, that card look is what is remembered.
- Known limit: the half-press restore (HLS task) and an arrow step (UI task) are not locked against each other. Only a
  half-press landing inside one arrow step, while a card look is still waiting for the card, can replace that step's
  choice.
- Review fix before the camera test: the first v0.4c25t seal linked halation's `p_get` call from the default
  sd_loader build, which is 2 bytes off in the look memory build. It ran only because the flags at that point made the
  stray branch fall through. The halation build now links against the sd_loader build in the spec, and the seal
  refuses a spec where that call misses `p_get`.
- Review fix, halation (resealed v0.4c22t, v0.4c23t, v0.4c24 and this build): two of the 11 callers of the job
  constructor leave a stray byte where the halation marker sits (`0x6035d6e4` never writes it; `0x60d19672` copies a
  byte of another record there). With Halo Off, a stray 0xAx byte could have sent a job down the Art route. Every
  hook that acts on the marker now also requires its stage to equal the current Halo stage, so **Halo Off is stock
  for every job**, whatever that byte holds. Emulator: Halo Off with every 0xA0..0xAF goes to the stock builder,
  `hl_ob` skips the pass, and the combiners stay stock. The opcode audit now also covers the code in the gap.
- Section 2 and Section 6 are full, so the new code lives in the 100 KB gap the halation patch loads: `.hlui` at
  0x612f0000 for the save, after the Halo page, and `.lmem` at 0x612f0800 for the restore. Build with
  `EM1_LOOKMEM=1` for sd_loader, and with `EM1_CC_HALO=1 EM1_LOOKMEM=1` for color_creator_wheel. The default builds are
  byte-identical to before.
- Emulator: every v0.4c24 check, plus `emu_look_memory`, which covers:
  - sid 965 through the real settings store (0..64, the three boot reset paths, neighbours untouched);
  - the half-press restore of built-in, card and mono looks, a card that is late, missing or too short, and
    invalid values;
  - the editor save and restore;
  - that a colour restore makes exactly one SetValue, 618 rewritten with its stored value, and changes no stored
    setting, while mono, skipped and invalid cases make none;
  - that stock and v0.4c24 ignore sid 965.
- Not emulated: the flash write at power-off; the live-view redraw itself, and the 618 write from the half-press
  (HLS) task, which stock code may never do. Its post-set notifier only posts a message. Camera test:
  `docs/OMD-EM1-II/thu-may-nho-look.md`.

## v0.4c24 — 2026-11-23 (halation release candidate; emulator-checked, not camera-tested)

- v0.4c23t with the strength taken from the Color Creator **Halo** page (Off / Low / Med / High, sid 961). It starts at
  **Off** (the setting's default; stock never writes it), so right after flashing photos match v0.4c17 until Halo is
  turned on. A stored value outside 0..3 counts as Off.
- It includes everything the test builds check, so it can be flashed on its own: with Halo Off the emulated capture
  jobs are stock, and a problem with Halo on is undone by setting Halo back to Off (`docs/OMD-EM1-II/thu-may-halation.md`).
  The step-by-step test builds stay available to find a fault.
- Emulator: every v0.4c23t check, plus the stage read from sid 961 through the real settings store (`emu_halation_flag`
  without a forced stage, tint cases included), `emu_spare_setting` on this spec, and the route / pass / combiner checks
  on this image with only hl_flag's own getter call fixed to Med (`emu_halation_route --stage-setting`).

## v0.4c23t — 2026-11-23 (halation glow camera-test build; emulator-checked, not camera-tested)

- **First build that should show halation.** Vivid / Natural / Color Creator stills get a tinted glow around bright
  highlights, at Med strength (stage fixed at 2 in this test build). The colour comes from the active look (red for
  every built-in look; card looks may choose amber, warm or cool).
- **Only the two emulated ordinary-still capture kinds (0x1000 / 0x1001) are touched.** Every other kind (High Res,
  HDR, bracketing, Live Composite and the rest), Monotone, Art Filters and Art Effects stay stock, and so does any
  job the constructor sends to another builder: the Soft Focus flag is set only at the hooked colour-builder call.
- Marked stills develop through the Soft Focus Art route with a neutral blend, so they take about as long as a Soft
  Focus Art Filter shot plus the glow pass (estimated 0.2–0.3 s without lights, about 4–8 s on a night scene).
- The hardware watchdog limit is raised from 10 s to 30 s (both run-time settings), as on E-P7 v0.31b, so a long save
  can't restart the camera. A real hang now restarts after up to 30 s instead of 10 s.
- Color Creator has a fifth page, **Halo Off / Low / Med / High** (INFO steps pages). It stores the setting, but in this
  build the strength stays at Med whatever it shows; the page is here to test the control.
- v0.4c17 otherwise. To go back, flash v0.4c17 or the stock restore file.
- Emulator: route, blend, pass (36 cases bit-exact against the model), tint, Halo page, watchdog and every v0.4c17
  check. Not emulated: the image processor, the camera's colours, real timing. See `docs/OMD-EM1-II/HALATION.md` step 4.

## v0.4c22t — 2026-11-23 (halation route diagnostic build; emulator-checked, not camera-tested)

- **Diagnostic, no glow.** Same as v0.4c23t without the glow pass: marked colour stills take the Soft Focus Art route
  with a neutral blend. Shoot the same scene and settings (tripod) with v0.4c17 and with this build: the JPEGs should
  match. A colour or contrast difference means the Art development (combiner 13) changes pixels, which v0.4c23t then
  inherits.
- Watchdog 30 s and the Halo page as in v0.4c23t.

## v0.4c20t / v0.4c21t — 2026-11-23 (withdrawn before any camera test; replaced by v0.4c22t / v0.4c23t)

- A review found that their gate set the Soft Focus flag in the flag converter for every marked colour still,
  including kinds and constructor branches nobody had emulated (High Res, HDR, bracketing, Live Composite), and that
  the combiner hooks trusted one marker byte. v0.4c22t / v0.4c23t allow only kinds 0x1000 / 0x1001, set the flag only
  at the hooked builder call, and the combiners also need the stage bits and the flag. The tested route is unchanged
  (the marked job is byte for byte the same except the hl_ob address). Their release folders were removed.

## v0.4c19t — 2026-11-23 (Sharpness scale camera-test build; emulator-checked, not camera-tested)

- Sharpness becomes a linear scale: −2 off, −1 25 %, 0 50 %, +1 75 %, +2 100 % (= stock +2). Flat and Log stay stock.
  Menus and EXIF still show −2..+2.
- v0.4c17 otherwise (no halation). To go back, flash v0.4c17 or the stock restore file.
- Emulator: the sharpening-gain helper on stock and patched images (3,780 runs, `tools/omdem1mk2_emu_sharp_scale.py`),
  plus every v0.4c17 check. See `docs/PORT_EM1MK2.md` §5 for what was and wasn't emulated, and the camera checks.

## v0.4c18t — 2026-11-20 (halation step 3 camera-test build; emulator-checked, not camera-tested)

- **Test build, not for everyday use — and no visible effect.** It sets the Soft Focus flag 0x80 on ordinary colour
  stills (stage fixed at 2). **Correction (2026-11-23):** the capture-job emulation (`tools/omdem1mk2_emu_work_list.py`)
  shows that Vivid / Natural / Color Creator stills use the plain builder `0x603a63f4`, which ignores that flag and
  builds the same four work-list items as stock. So this build makes **no glow**; the earlier "soft neutral glow" note
  was wrong (it assumed the E-P7 behaviour). Not worth a camera test; the colour-still route is step 4a.
- Same as v0.4c17 otherwise. To go back, flash v0.4c17 or the stock restore file.
- Emulator: the gate through the real flag converter (1,260 runs, stage / Art Effect / picture mode / capture kind),
  plus every v0.4c17 check. See `docs/OMD-EM1-II/HALATION.md` "Step 3" for what to look at on the camera.

## v0.4c17 — 2026-11-20 (emulator-checked test release)

- Loading a card pack after opening Color Creator keeps the built-in look active until the editor is reopened.
  Reopening selects the first card look and updates its name, sector colour values and tone together.
- The emulator reproduces the v0.4c16 mismatch and checks the corrected editor and SCP labels, early and late
  loading, look navigation and reentry. The display, card driver and settings facade are fixture boundaries.
- Retains the v0.4c16 OM 3.70 source, restore and shared card pack. Camera confirmation is pending.

## v0.4c16 — 2026-11-19 (emulator-checked test release)

- Builds from the pinned OM catalog E-M1 Mark II 3.70 package. Its matching restore is byte-identical to that package.
- Reuses the v0.4c15 patch set. Restores the 2 KiB Section 1 tail required by the 65:24 and 21:9 aspect code and labels.
- The emulator checks the transfer request length and addresses, aspect UI, SD look loading, AF, recording limits,
  and focus-stacking branch. The release awaits confirmation on an E-M1 Mark II.

## v0.4c15 — 2026-11-13 (camera-tested: card looks load, `C1.1` after a half-press)

- v0.4c14 on the camera read `C0.0`: the loader had never tried once. Its trigger sat in a part of the firmware that a
  half-press never reaches (it was believed to be the half-press handler since v0.1; it isn't). The loader now starts from
  the camera's main button-event loop, the same place the E-P7 uses, on the half-press event, once the camera has finished
  loading. The bottom line codes are unchanged (`C1.n` loaded, `C0.n` still trying, `CF.8` no file, `CF.1` damaged file).
- Same as v0.4c14 otherwise.

## v0.4c14 — 2026-11-13 (not camera-tested; emulator-checked)

- Looks from the card (`EM1MOD/LOOKS.BIN`) now load. Until now the camera waited for a "card ready" sign that never came,
  so only the 16 built-in looks were ever used (the bottom line always read `C0`). Now it simply tries to open the file at
  each half-press until it loads. The bottom line reads `C1.n` once loaded, `C0.n` while still trying (n = attempts), `CF.8`
  when there is no file, `CF.1` for a damaged file.
- Same as v0.4c13 otherwise (the memory test from v0.4c13-sp1 is not included; its result is recorded).

## v0.4c13-sp1 — 2026-11-13 (test build; camera: S+ after bursts and mode changes)

- v0.4c13 plus a memory test for the next features (halation): the camera loads 100 KB more of the firmware into memory,
  and the look editor's bottom line ends in **S+** (the memory is there and untouched), **S!** (it changed) or **S0** (not
  loaded). Nothing else changes.

## v0.4c13 — 2026-11-13 (camera-tested: SCP tile and option row show 65:24 / 21:9 — working)

- Super Control Panel option row: the screen already had the two extra cells, but it reads its icons from one more
  list that still had only the five stock aspects. That list now has 65:24 and 21:9 too.
- v0.4c12 is withdrawn (it changed the option screen on a wrong assumption; never flash it).

## v0.4c12 — 2026-11-13 (WITHDRAWN, never flashed)

- Super Control Panel option row: 65:24 / 21:9 open the camera's general option row, which has room for all seven
  aspects. The aspect-only row it used before draws just five cells. The pixel-size line under the row may no longer
  appear.

## v0.4c12d — 2026-11-13 (diagnostic; camera-tested: both slots blank → the row draws only five cells)

- Test build for the Super Control Panel option row only: the 65:24 slot uses the stock 16:9 icon, and 21:9 shows the
  16:9 icon everywhere. What appears in the two slots tells which part of the drawing still fails. Not for regular use.

## v0.4c11 — 2026-11-13 (camera-tested: SCP tile labels render; option row still empty)

- Super Control Panel tile: 65:24 showed "17:9" (it borrowed the 17:9 label's slot). 65:24 and 21:9 now have their own
  slots and their own labels in the panel's style.
- Super Control Panel option row: the two extra slots now get their values (the row reads a second copy of the aspect
  setting that still listed only the five stock aspects), so they can show the 65:24 / 21:9 icons.

## v0.4c10 — 2026-11-13 (camera-tested: tile shows "17:9", option row still empty; regular menu icons OK)

- Super Control Panel option row (OK on the aspect tile): 65:24 / 21:9 now have icons. The row reads its icons from
  a second table that still listed only the five stock aspects, so the new slots never had an icon to draw. That
  explains every blank from v0.4c5 to v0.4c9d.
- Keeps the v0.4c9 icon lookup and the v0.4c8 AF fix.

## v0.4c9 / v0.4c9d — 2026-11-13 (camera-tested: both still blank)

- Super Control Panel icons for 65:24 / 21:9 no longer depend on changes to the camera's graphics component, which
  never showed any effect on this camera. The firmware's icon lookup now serves the two icons from the main firmware.
  The graphics component is back to stock.
- v0.4c9d: the same, but 21:9 shows the stock 16:9 icon. Flash it only if v0.4c9 is still blank.

## v0.4c8 — 2026-11-13 (camera-tested: AF target selector works; SCP icons still blank)

- Super Control Panel: the 65:24 / 21:9 value cell. The cell looked the value up in a list that had no 65:24 / 21:9
  entry, so it never picked an icon (that is why v0.4c5–c7 stayed blank whatever icon they offered).
- AF target selector and shooting screen: 65:24 / 21:9 use the 16:9 AF layout, point mask, AF frame geometry,
  selected-point check and metering geometry (as the working E-P7 fix does).
- Both checked in the emulator against stock: stock settings behave exactly as before.

## v0.4c7 — 2026-11-13 (camera-tested: SCP still blank, AF cursor still missing)

- AF target selector in 65:24 / 21:9: uses the 4:3 point layout throughout (the camera's own selector code already
  falls back to 4:3 for these values; v0.4c6 mixed in the 16:9 point mask, so no cursor was drawn).
- Super Control Panel: 65:24 tries the new icon with the address form every stock icon uses. 21:9 deliberately shows
  the stock **16:9** icon this time: it tells whether graphics-table edits work on this camera at all.

## v0.4c6 / v0.4c6p — 2026-11-12 (v0.4c6 camera-tested: SCP still blank; AF selector without cursor)

- Super Control Panel: 65:24 and 21:9 were selectable but blank on v0.4c5. The icons now live in free space in the
  main firmware, and the graphics component only gets two pointer changes (nothing is added to it).
- Selected cells show the same white icon (there is no room for the larger green versions).
- v0.4c6p: the same build with stock placeholder icons (16:9 for 65:24, 3:2 for 21:9). Flash it only if v0.4c6 is blank.

## v0.4c5 — 2026-11-12 (camera-tested: regular menu works; Super Control Panel shows 65:24 / 21:9 blank)

- **Real 65:24 and 21:9 icons** in the stock aspect-icon style (white and green/selected), for the Live Control strip,
  the Super Control Panel tables and the info displays. This build also changes the OSD (graphics) component.
- Includes everything in v0.4c4.

## v0.4c4 — 2026-11-12 (not camera-tested)

- Image Aspect detail screen (OK on the menu row): the box shows "65:24" / "21:9" and the size table shows their pixel
  sizes (e.g. Large 5184x1920 / 5184x2224) instead of blank entries.
- Super Control Panel: its icon tables now know 65:24 and 21:9 (they were missing there on v0.4c3).
- Placeholder icons (16:9 / 3:2) as in v0.4c3.

## v0.4c3 — 2026-11-12 (camera-tested: short labels in the menu row; detail screen and SCP incomplete)

- Labels use the ratio: **65:24** and **21:9** (menu value text; no camera strings changed).
- Strip and option list: 65:24 / 21:9 use placeholder icons (the 16:9 icon and the 3:2 icon) because these screens draw
  icons only; on v0.4c1 they were blank. Real 65:24 / 21:9 icons are next.
- Otherwise as v0.4c1 (Panorama/Wide available; v0.4c1 shot a 5184x1920 JPEG on camera).

## v0.4c1 / v0.4c2 — 2026-11-11 (v0.4c1 camera-tested 2026-11-12: Panorama shows in the menu and shoots at 5184x1920)

- **Panorama (65:24) and Wide (21:9) should now appear** in the Shooting Menu and the Super Control Panel / Live Control.
  The real filter was the camera's interlock rules: the aspect rule only knew the values 4:3, 16:9, 3:2, 1:1, 3:4 and 17:9,
  and the menus hide any value the rule rejects. Its value tables now include Panorama and Wide. Shown in the emulator,
  running the camera's own code (stock: 5 options; v0.4c1: 7).
- AF target selector: Panorama and Wide use the 16:9 AF area table (the E-P7 crashed here before the same fix).
- v0.4c1: the strip entries are text ("Panorama", "Wide"); v0.4c2: placeholder icons (16:9 icon for Panorama, 3:2 icon
  for Wide) in case the strip draws icons only. Real XP / 21:9 icons later.
- No debug log. Switch back to 4:3 before powering off while testing.

## v0.4b5 — 2026-11-11 (not camera-tested)

- The camera-tested v0.3b5 + aspect ratios (Panorama 65:24 / Wide 21:9). **No debug log.**

## v0.3b5r — 2026-11-11

- Rebuild of the camera-tested v0.3b5 without the debug log, byte-identical to it (patched SHA-256 72552d29…). Use it
  to get a working camera back.

## Debug log — pulled (2026-11-11)

- v0.4b3 no longer restarted, but broke the shutter: a CARD error at every half-press with DEBUG.TXT, and a live-view
  reset with nothing captured without it. Its hook point runs for more than the half-press and it lacks the task check
  the E-P7 and OM-3 loggers use. **v0.4b1–v0.4b4 are withdrawn.** It comes back after it is moved and gated.

---

## v0.4b4 — 2026-11-11 (WITHDRAWN: contains the debug log)

- v0.4b3 + the v0.4 aspect patch (Panorama 65:24 / Wide 21:9). Flash only after v0.4b3 works.

## v0.4b3 — 2026-11-11 (WITHDRAWN: CARD error / no capture)

- **Fixes the restart when taking a picture (third fault).** The debug log's hook jumped one byte before its code, onto a
  `break` instruction, in v0.4, v0.4b1 and v0.4b2. The jump now lands on the code; the release check now verifies
  every hook's target.
- Otherwise identical to v0.4b1.

---

## v0.4b2 — 2026-11-11 (WITHDRAWN: hook still lands on a break; use v0.4b4)

- v0.4b1 + the v0.4 aspect patch (Panorama 65:24 / Wide 21:9), unchanged. Flash only after v0.4b1 works.
- Aspect is untested on camera: v0.4 restarted at the shutter before anyone could check it. No static reason found for the
  missing menu entries (validator, menu and SCP records are patched as on the E-P7, all in loaded memory).

## v0.4b1 — 2026-11-11 (WITHDRAWN: still restarts at the shutter; use v0.4b3)

- Fixed two of the three faults behind the restart (it still restarted: see v0.4b3). The debug logger returned to a wrong address on
  every shutter event (its call and ret frames did not match), and it wrote its flags into the firmware image in memory,
  which has crashed a camera before. Rewritten: flags in the shared heap block P, matched frames, waits for a mounted card.
- Debug log: put `DEBUG.TXT` in `EM1MOD`, half-press; `EM1MOD/CADLOG.TXT` (1,024 bytes) shows the build, report number,
  card, P state, look index/page/strength, and the first 8 bytes of `LOOKS.BIN`.
- Aspect left out on purpose (one feature group per flash).
- Build audit now rejects stores into the firmware image and mismatched call/ret frames.

---

## v0.4 — 2026-11-11 (WITHDRAWN: restarts the camera at the shutter; use v0.4b1)

- **Expanded Aspect Ratios: X-Pan (65:24) & Ultra-Wide (21:9)**:
  - Repurposed hidden internal aspect ratios (`id 6` and `id 7`) to provide Hasselblad X-Pan equivalent **65:24** and cinematic **21:9**.
  - **Setting 270 Validator**: Record at `0x604f07cc` expanded from 5 entries `[1, 3, 2, 4, 9]` to 7 entries `[1, 3, 2, 4, 9, 6, 7]`.
  - **Shooting Menu Integration**: Main menu Image Aspect descriptor (`0x6124ea1c`) expanded to 8 options with localized text labels: **Panorama** (String ID 241) and **Wide** (String ID 2661).
  - **Super Control Panel (SCP) & Live Control**: Option strip descriptor (`0x6124aea4`) expanded to 7 selectable options in both white and green strips.
  - **Capture & Sensor Pipeline**: All 46 per-aspect size and geometry tables updated across the firmware image. Split capture tables (Width `0x60556cc4`, Height `0x60556e62`) updated across all 23 size classes.
  - **ORF AspectFrame**: Jump table at `0x60556c24` redirects IDs 6 and 7 to the width-limited framing handler (`0x604240b1`).
  - **Live View Framing & Rec-View**: CapThr switches S7 (`0x60b2f8ec`), S8 (`0x60b2f918`), S9 (`0x60b2f944`), S10 (`0x60b4cedc`), and S_alt (`0x60b3bd68`) redirected to custom Section 1 case blocks rendering $640 \times 240$ (65:24) and $640 \times 272$ (21:9).
  - **Pixel Readout**: Pixel-dimension readout routine (`0x60f13985`) repointed to an expanded 7-column dimensions table.
  - **Cave Residency**: All aspect code and tables live safely in Section 1 free space (`0x60257580..0x602577f2`, 626 of 640 bytes).
  - Opcode audit verified: 0 `0xFB` opcodes, 0 mul/div, 0 hardware loops.

---

## v0.3b5 — 2026-11-11

- **Hardware Image-Request Tone Pipeline**:
  - Highlights, Midtones, and Shadows write directly to the image request records read by the hardware pipeline: Highlights (384), Midtones (692), Shadows (383), matching the E-P7 engine architecture.
  - Tone adjustments confirmed functional on-camera in both live view and saved JPEG stills ($\pm 7 / \pm 7$: highlights $\pm 14$, shadows $\pm 24$).
- **Diagnostic Debug Logger (`debug_log`)**, added later to the rebuilt v0.3b5 folder. **Correction:** this entry called it
  non-invasive and inert without `DEBUG.TXT`. It was not: it crashed the camera at every shutter event, with or
  without the file (mismatched call/ret frames, stores into the firmware image). The v0.3b5 tone work is not affected;
  the fix is v0.4b1.

---

## v0.3b4 — 2026-11-11

- **Velvia & Film Profiles Confirmed on Camera**:
  - Captured JPEGs confirmed matching panel preview (saturated blues, punchy red ground, deepened shadows, neutral sky).
  - Look colour and tone processing verified reaching stills, not just the live view display.
- **Strength Adjustment Page**:
  - Added new Page 3 to Color Creator: allows scaling look intensity ($\times 1$, $\times 1.5$, $\times 2$, $\times 3$) across saturation, hue, and luminance.
- **Live View Refresh Trigger**:
  - Re-triggers colour stage recalculation after manual wheel adjustments by re-issuing vividness (setting 618), eliminating previous need to switch looks back and forth.

---

## v0.3b3 — 2026-11-11

- **Subtle Rendering & Tone Sync**:
  - Corrected tone write settings for live view vs image request.
  - Resolved issue where Chroma and Luminance slider modifications did not visibly affect live view without re-triggering mode refreshes.

---

## v0.3b2 — 2026-11-11

- **Section 5 Relocation (Memory Boundary Fix)**:
  - Relocated built-in looks table into Section 5 tail (`0x60bc8150`) after discovering Section 6 is loaded only up to `0x612e7000` (not `0x61300000`).
  - Added automated section residency verification tool (`omdem1mk2_check_loaded.py`) to prevent any unmapped flash memory edits.
- **Sticky Monochrome Fix**:
  - Fixed bug where picking a B&W look (vividness $-4$) left all subsequent colour looks stuck in monochrome. Colour looks now explicitly restore proper vividness baselines.

---

## v0.3b1 — 2026-11-11

- **TruePic VIII COLOR Hardware Pipeline Hook**:
  - Directly hooked the TruePic VIII 12-sector hardware colour engine (`0x603ec642` / `0x603ec82c`) inside Color Creator mode.
  - Bypassed camera's stock limitation of a single uniform hue and vividness, feeding 12 independent sector saturations, per-sector hue shifts, and lightness offsets.
- **Unified Look File Format**:
  - Switched `EM1MOD/LOOKS.BIN` to standard E-P7 v3 look format (`EP7B`, 64 + 64 bytes per look, up to 32 looks).
  - Cross-compatible with E-P7 Control Panel web exports and custom recipe packs.

---

## v0.2b2 — 2026-11-10

- **Heap & Allocator Safety**:
  - Corrected heap `free()` call to the camera's primary OS allocator pool (`0x6002323d` instead of `0x600232d9`).
  - Fixed caller-saved register clobbering in SD card loader CRC calculation routine.
- **String Sanitization**:
  - Added strict printable ASCII validation to look names to prevent garbage character rendering on OSD banners.

---

## v0.2b1 — 2026-11-10

- **Isolated Shared Heap Block P**:
  - Fixed critical state memory corruption: moved patch state (SD card loaded flag, look index, active page) out of stock callback ring (`0x621e2f74`) into an isolated heap block P referenced via compiler padding pointer (`0x621e24ae`).
- **Register Preservation in Dial Loops**:
  - Arrow key event handlers updated to preserve `d2` and `d3`, preventing disruption of the stock dial loop detent counters.
- **Vividness Range Clamping**:
  - Clamped monochrome look vividness writes to $-4$ to adhere to camera's $-4..+3$ validator limits.

---

## v0.1 — 2026-11-06

- **Initial Port of Caduceus to OM-D E-M1 Mark II**:
  - **Video Recording Limits (`rec_limit`)**: Patched duration check at `0x603549d7` and `0x603549dc` from 29 min (1740s) / 2 hours (7200s) to 9 hours (32400s).
  - **Focus Stacking Unlock (`focus_stacking`)**: Patched `0x60656a4a` (`bne` $\to$ `nop nop`), removing the PRO lens whitelist and allowing automated focus stacking with any autofocus lens (Olympus non-PRO, Panasonic, Sigma).
  - **SD Card Look Loader (`sd_loader`)**: Added initial Section 2 cave routine (`0x60580200`) hooked into shutter half-press event to load custom looks from SD card (`C:\EM1MOD\LOOKS.BIN` or `D:\EM1MOD\LOOKS.BIN`).
  - **Color Creator Look Browser (`color_creator_wheel`)**: Initial implementation of look browser interface overlaid on the camera's native Live View Color Creator screen.

