# Caduceus for the Olympus OM-D E-M1 Mark II

**Caduceus for E-M1 II** is a port of [Caduceus](https://github.com/cakelesscoder/caduceus-ep7) (open-source
firmware patches for the Olympus PEN E-P7) to the **Olympus OM-D E-M1 Mark II on firmware 3.7** (build 3700,
model 0x1250). It brings Caduceus film looks to the camera's **Color Creator** picture mode, through the same
colour engine the E-P7 uses, plus **65:24 (XPan)** and **21:9** stills, longer video recording and focus
stacking with any lens.

It reads the **same look format, share codes and card files** as the E-P7 and OM-3 ports, so one look works on
every body.

**Latest build: v0.4c17** (emulator-checked, not yet camera-tested; see [Status](#status)) · **[Changelog](patches/omdem1mk2/CHANGELOG.md)** ·
**[Port notes](docs/PORT_EM1MK2.md)** · **[To-do](current.todo)** ·
Vietnamese firmware update guides: [OM Workspace](docs/huong-dan-cap-nhat-firmware-om-workspace.md),
[SD card](docs/huong-dan-cap-nhat-firmware.md)

> [!WARNING]
> **Experimental, use at your own risk.** This is unofficial, in-development firmware modification for one
> camera model. Flashing modified firmware can crash, freeze or brick your camera, corrupt photos or damage your
> SD card's data. **No responsibility is accepted for any damage, data loss or other harm.** It is provided
> "as is", without warranty of any kind (see the [Apache License 2.0](LICENSE), sections 7–8). Using it may
> affect your warranty with OM Digital Solutions. Read [Safety](#safety) before flashing.
>
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
| Halation (global stage over any colour mode) | design + code-space probe only ([plan](docs/OMD-EM1-II/HALATION.md)) |
| Blacks / Whites, true B&W looks, grain, sharpening off, NR per look | not ported |

**v0.4c16** builds v0.4c15 on the firmware file OM's update server serves today (SHA-256 `691a8a8e…`; v0.4c15 and
older were built on `f0c25dd8…`). That file loads 2 KiB less of Section 1 at boot, which would leave the 65:24 / 21:9
code unloaded, so v0.4c16 adds one edit that loads it again. **v0.4c17** = v0.4c16 plus a Color Creator fix: card
looks that load after the editor was opened now show their own colours, not the built-in look's. Both passed every
emulator check [E]; neither has run on a camera yet.

## Install

You need: an E-M1 Mark II on firmware **3.7** (Setup › Firmware), a **full battery**, an SD card in **slot 1**,
and Python 3 on your computer.

1. **Update to official 3.7 first** if the camera shows an older version (OM Workspace; see the Vietnamese guide above).
2. **Build the update file.** The builder downloads OM's official 3.7 file from OM's own server, checks its hash,
   applies the release and writes the card files plus a stock-restore file:

   ```bash
   git clone https://github.com/xtruong88/caduceus-em1ii
   cd caduceus-em1ii
   python3 caduceus.py build --camera em1mk2 --release v0.4c17 --out out/em1mk2-v0.4c17
   python3 caduceus.py verify out/em1mk2-v0.4c17
   ```

3. **Copy to the SD card:** `DCOLYMP/E1259999.BIN` and (optional, for card looks) `EM1MOD/LOOKS.BIN`.
   Keep `restore/E1259999.BIN` safe on your computer.
4. **Flash:** card in slot 1, hold **OK** and switch the camera on. The LED stays on while writing and blinks
   (~2 Hz) when done. Do not switch off or open the battery door while it writes.
5. **Shoot:** set the picture mode to **Color Creator**. Half-press once after power-on (this loads the card's
   looks), then open Color Creator to pick and edit a look.

**Go back to stock:** flash `restore/E1259999.BIN` the same way (it is OM's file, unchanged).

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
python3 patches/omdem1mk2/color_creator_wheel/build.py   # rebuilds the Color Creator edits v0.4c17 takes
python3 tools/omdem1mk2_catalog_release.py --stock stock_firmware/OLY_E_125_3700_0000_0000.BIN --version v0.4c17
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
