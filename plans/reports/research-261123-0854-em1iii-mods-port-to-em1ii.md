# E-M1 III mods: which ones can port to the E-M1 II

Source: `dfeldt91-blip/E-M1-Miii` (`builder/mods.json`, 21 mods; `builder/README.md`; `docs/FINDINGS.md`,
`docs/FEATURE_LIST.md`), read 2026-11-23. E-M1 II check: setting-name table in block 2 of stock 3.70
(`em1mk2/extracted/02_0106_43960020.decoded.bin`, 3808 `MODE_*` names). Static string check only: nothing
disassembled, emulated or built.

**License:** the E-M1 III repo has no license file, so its code can't be copied. Use ideas and addresses as
leads only. Its looks come from Caduceus (Apache 2.0, credited in its README).

## Already done on the E-M1 II

| E-M1 III mod | E-M1 II |
|---|---|
| `rec_limit` | Done, camera-tested (`patches/omdem1mk2/rec_limit`) |
| `stack_any_lens` | Done, camera-tested (`focus_stacking`) |
| `panorama` (65:24) | Done (`aspect`, `aspect_icons`), camera-tested v0.4c15 |
| `custom_looks` | Done differently: looks behind Color Creator + `LOOKS.BIN` |

## Worth porting (setting exists on the E-M1 II, small edit)

| Mod | Evidence on the E-M1 II | Size | Note |
|---|---|---|---|
| `sharp_scale` | `MODE_SHARP_M2..P2`, `MODE_SHARP_<mode>` present | 3 edits on III | E-P7 recipe in `docs/SHARPENING_OFF.md`. Best first pick |
| `filename_underscore` | `MODE_FILENAME_CUSTOM_SRGB1..4/ADOBE1..4` present | 2 char lists | Data edit, low risk |
| `iso_auto_low` | `MODE_ISO_AUTO`, L64 exists on body | 3 immediates | Find the 0x600 floor near AE code |
| `owner_title` | Same language section layout likely | data only | Check block 1 string table layout first |
| `underwater_mono` | `MODE_COLORTONE_UNDERWATER` present | small | Needs per-mode saturation path |
| `multiexp` (3–4 frames) | `MODE_CAMERA/EXPOSE_MULTI_EXPOSURE` present | 14 edits on III | Frame count limit + compositing buffers; medium risk |

## Possible, needs research first

| Mod | Why uncertain |
|---|---|
| `cmode_video` | No `CUSTOM*_DIAL` / assign names in the E-M1 II table; C1–C3 handling differs |
| `keyline_mono` | Key Line II = `LIGNE_CLAIR_2` present; the 1-byte III edit site must be found |
| `white_frame` (+ `_panorama`) | Art effect frame exists; III patch rewrites frame drawing (0 static edits, generated) |
| `hires_art` | E-M1 II has tripod High Res; unknown whether art filters can run in that path |
| `picture_mode_button`, `scp_menu` | Button/SCP tables differ by body; 27 / 2 edits on III |
| `art_gradation` | 81 edits; no `GRADATION` names on the E-M1 II |
| `xpan_icon` | Only cosmetic; E-M1 II already has its own 65:24 icons |

## Not portable

| Mod | Reason |
|---|---|
| `hhrs_flash` | E-M1 II has no Handheld High Res |
| `mono_slots` (Monochrome II profile) | Names `MODE_COLORTONE_MONOCHROME_CREATOR` exist but the E-M1 II has no profile UI (same reason looks live in Color Creator). B&W looks via key 12 judged feasible, but the owner skipped it 2026-11-23 (rarely shoots mono) |
| `arrow_keys` | Not camera-tested even on the III |

## Suggested order

1. `sharp_scale` (known E-P7 recipe, visible result, easy to emulate).
2. `filename_underscore`, `iso_auto_low` (small, low risk).
3. `multiexp` once the above pass.

Each needs: locate the site on 3.70, emulator run patched vs stock (AGENTS.md rule), then camera.

## Unresolved

- Strings in block 1 look shared across models (e.g. "Key Line" appears 99x), so UI-string presence was not used as evidence.
- `cmode_video`: how E-M1 II stores C1–C3 and whether movie mode is greyed out the same way is unchecked.
