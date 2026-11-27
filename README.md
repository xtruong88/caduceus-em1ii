# Caduceus for the Olympus OM-D E-M1 Mark II

**English** · **[Tiếng Việt](README.vi.md)**

**Caduceus for E-M1 II** is a port of [Caduceus](https://github.com/cakelesscoder/caduceus-ep7) (open-source
firmware patches for the Olympus PEN E-P7) to the **Olympus OM-D E-M1 Mark II on firmware 3.7** (build 3700,
model 0x1250). It brings Caduceus film looks to the camera's **Color Creator** picture mode, through the same
colour engine the E-P7 uses, plus **65:24 (XPan)** and **21:9** stills, longer video recording, focus
stacking with any lens and **halation** (a tinted glow around highlights, set on a Color Creator **Halo** page).

It reads the **same look format, share codes and card files** as the E-P7 and OM-3 ports, so one look works on
every body.

**Public beta: testers wanted.** Three builds are ready, each adding one feature to the one before; none has run
on a camera yet. **[Become a tester](#become-a-tester)** · **[Changelog](patches/omdem1mk2/CHANGELOG.md)** ·
**[Port notes](docs/PORT_EM1MK2.md)** ·
Vietnamese guides: what it does, backup, install, every feature, restore ([Markdown](docs/huong-dan-firmware-em1-ii.md) ·
[HTML](docs/huong-dan-firmware-em1-ii.html)) ·
[official 3.7 update with OM Workspace](docs/huong-dan-cap-nhat-firmware-om-workspace.md)

> [!IMPORTANT]
> **Only for the E-M1 Mark II on firmware 3.7.** Never flash an E-P7, OM-3 or other body's build on it, and
> never flash this build on any other camera.

## Status

Marks: **[C]** = ran on a real E-M1 II; **[E]** = checked in the emulator (the camera's own CPU code, patched
against stock); **[S]** = static checks only. Details per build: [CHANGELOG](patches/omdem1mk2/CHANGELOG.md),
[WORKLOG](WORKLOG.md).

| Feature | Status |
|---|---|
| Video recording limit 29 min → 9 h (`rec_limit`) | [C] since v0.1 |
| Focus stacking with any lens (`focus_stacking`) | [C] since v0.1 |
| Film looks in Color Creator: E-P7 colour engine (12-sector saturation, per-sector hue / light), look tone (highlights / midtones / shadows), Chroma, Highlights / Shadows dials, Strength x1–x3 (`color_creator_wheel`) | [C] v0.3b5: colours change, Velvia matches the Panel preview, HL/SH order confirmed |
| 16 built-in looks | [C] |
| Looks from the card (`EM1MOD/LOOKS.BIN`, loaded at the first half-press) (`sd_loader`) | [C] v0.4c15: file loads (`C1.1`); look names / colours from the card still to confirm |
| 65:24 and 21:9 stills: Shooting Menu, Super Control Panel tile and option row, icons, AF target selector (`aspect`, `aspect_icons`) | [C] v0.4c13 |
| 65:24 / 21:9 live-view framing, rec-view, RAW+JPEG, power cycle with 6/7 saved, Live Control strip, tracking AF, grid | not tested yet |
| Halation: tinted glow on colour JPEG stills, Off / Low / Med / High on a Color Creator **Halo** page (default Off) (`halation`) | [E] v0.4c24: route, pass (bit-exact against its model at the camera's own image-heap addresses), Halo page, Off = stock capture jobs; not camera-tested ([details](docs/OMD-EM1-II/HALATION.md)) |
| Watchdog limit 10 s → 30 s, so a long save cannot restart the camera | [E] v0.4c24 |
| Look memory: the Color Creator look survives power-off (`sd_loader`, `color_creator_wheel`) | [E] test build v0.4c25t |
| WB shift per look (A-B / G-M from the look; CWB and other modes stay stock) (`look_wb`) | [E] test build v0.4c26t, including the capture WB block run natively ([test steps](docs/OMD-EM1-II/thu-may-look-wb.md)) |
| Sharpness as a linear scale (test build `v0.4c19t` only) | [E] |
| Blacks / Whites, true B&W looks, grain, sharpening off, NR per look | not ported |

**v0.4c16** builds v0.4c15 on the firmware file OM's update server serves today (SHA-256 `691a8a8e…`; v0.4c15 and
older were built on `f0c25dd8…`). That file loads 2 KiB less of Section 1 at boot, which would leave the 65:24 / 21:9
code unloaded, so v0.4c16 adds one edit that loads it again. **v0.4c17** = v0.4c16 plus a Color Creator fix: card
looks that load after the editor was opened now show their own colours, not the built-in look's. Both passed every
emulator check [E]; neither has run on a camera yet.

**v0.4c24** = v0.4c17 plus halation and the Color Creator Halo page, and the 30 s watchdog. Halo starts at **Off**: then
the emulated capture jobs are those of stock (an Art Filter's Soft Focus list names a hook that runs the stock blur), so the camera shoots like v0.4c17 until Halo is turned on, and a halation
problem is undone by setting Halo back to Off. At boot it adds only the 30 s watchdog and a 100 KB load that the
camera-tested probe sp1 used (nothing else in the current 3.7 file addresses that memory). Sealed with 21 checks;
not yet flashed on a camera. Recommended first time: flash the stock restore file once (step 0 in the guides), then
v0.4c24.

**v0.4c25t** = v0.4c24 plus look memory (sid 965). **v0.4c26t** = v0.4c25t plus WB shift per look, and the editor now
switches the look off before it changes it, so no capture pairs one look's state with another's. Both are camera-test
builds sealed with every check of the build before plus their own harness.

## Become a tester

The builds below have passed every emulator check but **have not run on a camera**. Testers who flash them
and report back decide what goes into the first release. Go **one step at a time**: flash the next build only when
the one before worked on your camera.

| Step | Build | Adds | What to check (step-by-step guide) |
|---|---|---|---|
| 0 | `restore` (OM's own 3.7 file) | nothing: a clean start | the camera boots and shoots as before |
| 1 | **v0.4c24** | halation (Halo page, starts Off), 30 s watchdog, on top of looks / XPan / 21:9 / 9 h video / focus stacking | [thu-may-halation.md](docs/OMD-EM1-II/thu-may-halation.md) |
| 2 | **v0.4c25t** | the Color Creator look is remembered after power-off | [thu-may-nho-look.md](docs/OMD-EM1-II/thu-may-nho-look.md) |
| 3 | **v0.4c26t** | each colour look's WB shift is applied (five built-in looks change colour: Nostalgic, Gold 200, Kodachrome64, Portra 400, CineStill800) | [thu-may-look-wb.md](docs/OMD-EM1-II/thu-may-look-wb.md) |

**Report** each step in an [issue](https://github.com/xtruong88/caduceus-em1ii/issues): build name, what you did,
what happened (works / odd / froze), and the JPEGs the guide asks for. A freeze or failed boot is the most useful
report: say exactly what you pressed last.

## Install

You need: an E-M1 Mark II on firmware **3.7** (Setup › Firmware), a **full battery**, an SD card in **slot 1**,
and **Python 3** on your computer (Windows: [python.org](https://www.python.org/downloads/), tick
"Add python.exe to PATH"). No compiler or other tool is needed.

1. **Update to official 3.7 first** if the camera shows an older version (OM Workspace; see the Vietnamese guide above).
2. **Get this repository:** `git clone https://github.com/xtruong88/caduceus-em1ii`, or download the
   [release](https://github.com/xtruong88/caduceus-em1ii/releases) "Source code (zip)" and unzip it.
3. **Build the update file** in that folder. The builder downloads OM's official 3.7 file from OM's own server,
   checks its hash, applies the build you chose and writes the card files plus a stock-restore file
   (macOS / Linux: `python3` instead of `py`):

   ```powershell
   py caduceus.py build --camera em1mk2 --release v0.4c24 --out out/em1mk2-thu-may/4-v0.4c24
   py caduceus.py verify out/em1mk2-thu-may/4-v0.4c24
   ```

   For the next steps use `--release v0.4c25t --out out/em1mk2-thu-may/5-v0.4c25t` and
   `--release v0.4c26t --out out/em1mk2-thu-may/6-v0.4c26t`: the test guides use these folder names.

   `verify` must end with "All good". Already have OM's file (`OLY_E_125_3700_0000_0000.BIN`)? Add
   `--stock <path to it>` to `build`.
4. **Copy to the SD card:** `DCOLYMP/E1259999.BIN` and (optional, for card looks) `EM1MOD/LOOKS.BIN`.
   Keep `restore/E1259999.BIN` safe on your computer.
5. **Flash:** card in slot 1, hold **OK** and switch the camera on. The LED stays on while writing and blinks
   (~2 Hz) when done. Do not switch off or open the battery door while it writes.
6. **Shoot:** set the picture mode to **Color Creator**. Half-press once after power-on (this loads the card's
   looks), then open Color Creator to pick and edit a look.

**Go back to stock:** flash `restore/E1259999.BIN` the same way (it is OM's file, unchanged).

**Why no ready-made `.BIN` to download?** OM's licence forbids redistributing their firmware, so the releases contain
only Caduceus's edit lists and card files. The builder applies them to the copy of OM's file it downloads for you.

## Using it

- **Color Creator editor:** the look name and a status line appear at the bottom. INFO cycles the editor pages
  (look, Chroma, Highlights / Shadows, Strength); the dials step the values.
- **Status line codes:** `C1.n` card looks loaded (n = attempts), `C0.n` still trying, `CF.8` no `LOOKS.BIN`,
  `CF.1` damaged file; `K<hex>` = active look key (`+` once applied); ` Exx` = a setting write was rejected.
- **Make your own looks:** run this repo's Control Panel (`webapp/`), pick **E-M1 II** as the camera and export
  `LOOKS.BIN` to `EM1MOD/` on the card. Packs and share codes are the same as on the E-P7. (The hosted E-P7 panel
  does not list the E-M1 II until the export target is merged upstream.)
- **Aspect:** Shooting Menu 1 › Image Aspect, or the aspect tile in the Super Control Panel. 65:24 shoots
  5184x1920, 21:9 5184x2224.
- **Halation:** in the Color Creator editor, INFO to the **Halo** page, Left / Right for Off / Low / Med / High (kept
  through power-off). It applies to ordinary colour JPEG stills (not Monotone, Art Filters, Art Effects or the special
  capture modes). A night scene with lights takes a few seconds longer to save.

## Safety

- **No responsibility is accepted for damage of any kind.** You flash this at your own risk.
- Only the E-M1 Mark II on firmware **3.7** is supported. The builder refuses any other stock file.
- Every patch is run in an emulator of the camera's CPU before a build goes to the camera (rule in
  [AGENTS.md](AGENTS.md)). The emulator does not cover the real SD card driver, the boot-time flash copy, image
  colour or what the screen draws: those are only proven by camera tests, which the Status table lists.
- A full battery and an uninterrupted write are essential. A failed write can leave the camera unbootable.
- **No `EM1MOD` folder on the card** = only the built-in looks, the aspect options, the longer recording limit
  and focus stacking remain. If something misbehaves, remove `EM1MOD` first; if that does not help, flash the
  restore file.

## How it works

- **This repository contains no OM firmware.** The builder downloads OM's official file and checks its hash.
- Patches (`patches/omdem1mk2/`) are small MN103 assembly routines and data edits. Each build script checks every
  stock byte it replaces and places code only in sections the camera really loads (`tools/omdem1mk2_check_loaded.py`).
- `tools/omdem1mk2_make_release_edits.py <VERSION>` rebuilds all patches, runs the load-range and opcode audits and
  seals a release under `releases/em1mk2/<VERSION>/`.
- Emulator harnesses (`tools/omdem1mk2_emu_*.py`) run the camera's own code from the decoded firmware, patched
  against stock: card loader, Super Control Panel cell, AF display, interlock rules and setting validator.
- Runtime state lives in one heap block (`patches/omdem1mk2/p_layout.inc`), never inside the firmware image or
  stock RAM tables.
- Firmware layout and evidence: [docs/OMD-EM1-II/](docs/OMD-EM1-II/), [docs/PORT_EM1MK2.md](docs/PORT_EM1MK2.md).

## For developers

Build tools need Linux (or a Linux container on Windows):

```bash
git clone --recurse-submodules https://github.com/xtruong88/caduceus-em1ii
cd caduceus-em1ii
tools/setup_toolchain.sh   # GNU binutils for mn10300 (assembler / linker)
python3 external/oly_fw_analysis/tools/build_mn103_emulator.py --archive <binutils-gdb archive, see its docs/tooling/EMULATOR.md>
python3 external/oly_fw_analysis/tools/om_firmware_catalog.py --model-id 1250 --model-name "E-M1 Mark II" \
  --installed 00001000 --download --out cache/catalog     # OM's 3.7 file; copy it to stock_firmware/
python3 external/oly_fw_analysis/tools/oly_container.py stock_firmware/OLY_E_125_3700_0000_0000.BIN \
  --code-base 0x60021020 --out em1mk2/extracted
python3 patches/omdem1mk2/color_creator_wheel/build.py   # Color Creator edits (edits.json)
EM1_CC_HALO=1 python3 patches/omdem1mk2/color_creator_wheel/build.py   # the same with the Halo page (edits_halo.json)
python3 patches/omdem1mk2/halation/build.py               # halation edits (stage from the Halo page)
python3 tools/omdem1mk2_catalog_release.py --stock stock_firmware/OLY_E_125_3700_0000_0000.BIN --version v0.4c24
                                           # seals on OM's catalog file; runs check_loaded, audit and every emu_* first
python3 -m unittest tools/test_caduceus_releases.py
```

Before porting or patching, read [docs/FIRMWARE_GUIDE.md](docs/FIRMWARE_GUIDE.md) and [AGENTS.md](AGENTS.md):
keep to the shared look format and share codes.

## Credits

- **[cakelesscoder/caduceus-ep7](https://github.com/cakelesscoder/caduceus-ep7):** Caduceus itself (E-P7), the look
  format, Control Panel, colour engine route and the build / safety tooling this port is built on.
- [androidfanman/caduceus-om3](https://github.com/androidfanman/caduceus-om3): the OM-3 port, a reference for
  porting to another body.
- [fishcu/oly_fw_analysis](https://github.com/fishcu/oly_fw_analysis): firmware research and the MN103 emulator
  harness (used as a submodule).
- u/fischgurke's PEN-F HSL firmware mod, which started the Caduceus project; LightSnowDev, Altsoph/mx3 (CHDK forum),
  the DVXuser and Personal View Olympus threads, and iKenndac for earlier Olympus firmware research.

## License

Patch code, tools and docs are released under the [Apache License 2.0](LICENSE). The OM firmware itself is not
included or redistributed: the builder downloads it from OM's own server on your machine. The
`external/oly_fw_analysis` submodule keeps its own licence. See [NOTICE](NOTICE).

Not affiliated with OM Digital Solutions. "Olympus", "OM-D" and film names are trademarks of their owners.
