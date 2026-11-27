# E-M1 II halation step 4: tinted halation pass

Blocks: [261123-2331-em1ii-look-quality](../261123-2331-em1ii-look-quality/plan.md). Its camera builds wait for the
v0.4c24 camera baseline, and it must not reuse sid 961.

In progress (2026-11-23). Verify each phase in the emulator, then make one camera build.
Design source: E-P7 `patches/halation` (h1–h4) on the grain CPU route, docs/HALATION_RED.md §14–22, docs/GRAIN_PORT.md;
E-M1 II sites and harnesses: docs/OMD-EM1-II/HALATION.md (steps 2–3).

`tools/omdem1mk2_emu_work_list.py` ran the firmware's capture entry, params
fill and constructor. With Art Filter 101 and flags `0x480`, the immediate at `0x60393a6b` supplies slot 3 (zero-based,
job+11020) and the stock runner dispatches it. With flags `0x80` alone the Art builder leaves Blend Setup pending.
Vivid, Natural and Color Creator class-0 jobs with stage 2 set `0x80`, take a different builder (`0x603a63f4`) and
publish the same four entries as stock. See [capture-job results in step 4](../../docs/OMD-EM1-II/HALATION.md).

4a remains open. Establish a route for ordinary colour stills with a verified image completion point, then run
`hl_gs` with Halo off and on. The Art work-list immediate by itself cannot route the tested colour stills.

| Phase | Done when |
|---|---|
| 4a. Wrapper route | Blend setup on E-M1 shown synchronous (submit + wait) or the right completion point found; wrapper `hl_gs` emulated: stock result unchanged when halation is off, pass entry reached with job + record 0x1000 when on |
| 4b. Per-job decision | Wrapper decides from the job alone (stage, colour still, our forced 0x80 vs the user's Soft Focus); marker design proven not to collide with stock flag use |
| 4c. Neutral blend | Combiner 11/12 stubs (prototype `tools/emu_fixtures/em1_combiner_neutral.s`) gated by 4b: our forced jobs blend at w = 1024, user Soft Focus keeps 600 |
| 4d. Halation pass | E-P7 passes A/B/C ported to E-M1 services (malloc `0x600231fe`, lock/unlock, flush, mapper map from `emu_mapper`); bit-exact vs a Python model; guards (format 0x0302, size, malloc, mapper refusal) leave the image untouched |
| 4e. Tint and strength | Stage 1..3 → gmax; glow colour from the active look's tint (LOOKS.BIN +47), red by default |
| 4f. Control | Halo row in `color_creator_wheel` writing sid 961 (code moved to the 100 KB region) |
| 4g. Time budget | Pass time estimated against the 10 s watchdog (`0x6005aecc`); decide whether the timeout must change |
| 4h. Test release | Sealed with every check; camera test list |

Update 2026-11-23 evening: Art route chosen (owner). 4a/4b/4c/4d built and emulated end to end
(tools/omdem1mk2_emu_halation_route.py, _halation_pass.py, _halation_flag.py, _job_marker.py). Next: 4e tint, 4f control,
4g time budget, then a no-pass diagnostic build (combiner 13 A/B) and a glow test build.

Update 2026-11-23 night: 4e/4f/4g/4h done in the emulator. 4g: watchdog 10 -> 30 s at both run-time settings
(`0x600792c4`, `0x6005aecc`; tools/omdem1mk2_emu_watchdog.py), 1/3 coverage cap kept. 4h: sealed `v0.4c22t`
(no-pass diagnostic) and `v0.4c23t` (glow), stage fixed at 2, with every check; they replace v0.4c20t / v0.4c21t after
a crash-risk review narrowed the gate (kinds 0x1000 / 0x1001 only, flag 0x80 set at the route, combiners need the flag).
Release candidate `v0.4c24` (stage from the Halo page, default Off) sealed. Remaining: the camera tests only. Remaining: camera tests
(docs/OMD-EM1-II/HALATION.md "Camera test builds"), then a release that takes the stage from the Halo page.
