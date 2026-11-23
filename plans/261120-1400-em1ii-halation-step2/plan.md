# E-M1 II: review c17 + halation step 2 (no camera available)

Status: done (2026-11-20); step 3 next. Owner has no camera now: emulator and static work only, nothing flashed.

| Phase | Status | Done when |
|---|---|---|
| 1. Independent review of v0.4c16/c17 code | done | No firmware defect. Fixed: copy_to_card kept unreadable LOOKS.BIN; stock-not-found message; card-source stepping added to emu_color_creator. Section 1 tail shown unreferenced in catalog stock (docs/PORT_EM1MK2.md) |
| 2a. Spare remembered setting for the halation stage | done (emulated) | Sid 961; tools/omdem1mk2_emu_spare_setting.py; power-off survival needs the camera |
| 2b. Soft Focus / combiner / CPU-pass sites on E-M1 II | done (emulated: converter, kind mapper, combiners, blend setup, mapper) | Table in docs/OMD-EM1-II/HALATION.md "Step 2"; flag converter emulated (emu_artflags, in the release checks) |
| 3. Next build | not needed yet | Phase 1 fixes are PC tools and harnesses only; v0.4c17 firmware unchanged |

Reports: `plans/reports/research-261120-1400-em1ii-spare-setting.md`,
`plans/reports/research-261120-1400-em1ii-softfocus-cpupass-sites.md`.

Constraints: AGENTS.md (emulate before any camera build; shared look format), docs/OMD-EM1-II/HALATION.md owner
decisions. Releases are sealed with `tools/omdem1mk2_catalog_release.py` on the OM catalog stock `691a8a8e…`.

Update 2026-11-20: combiner 11/12 + neutral-blend stubs and the capture-kind mapper emulated
(`emu_combiner`, `emu_capture_kind`, both in the release checks). Then the blend setup 0x60398ee1 (emu_blend_setup). Left for step 2: the mapper 0x6006888f ranges.
