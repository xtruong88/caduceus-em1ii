# E-M1 II 3.70: spare remembered setting for the halation stage (research)

Date 2026-11-20. Read-only research; no repo file changed except this report. Image: `em1mk2/extracted/00_0100_40560020.decoded.bin`
(catalog 3.70 loader, Section 1 ends 0x60257000). Tags: **[E]** emulator-verified, **[S]** statically traced, **[G]** guess.

## Ranked candidates

| # | Sid | Key [idx] | Validator (rec) | Default | Readers found | Persisted? | Reset at boot? | Confidence |
|---|---|---|---|---|---|---|---|---|
| 1 | **961** | `0xF709[0]` (s8) | s16 list -7..+7, 15 values (`0x604f2e64`) | **0** | **None.** Key `0xF709` is never an immediate in loaded code; sid 961 appears only as 2 log line numbers (`0x60d216d6/e3`) and 1 GUI resource id (`0x60f119bd`). Not in the descriptor registry (no apply callback), the per-sid UI init table, or any editor child list. | Yes [S]: block 90 (below); data at `0x6250423a` [E] | No [E]: value 3 survives all three boot reset paths | **High** |
| 2 | 981 | `0xF779[2]` (s8) | s8 list {0,1,2,3} exactly (`0x604f2ff4`) | **1** | One read: picture-mode switch `0x60cc2f2a`, **MONO (pipeline 12) branch only**, `0x60cc329e` → request `+24235` when MONO profile = 3. This body never selects pipeline 12. | Yes [S]; data `0x62504251` [E] | No [E] | Medium-high |
| 3 | 965 | `0xF719[1]` (s8) | -7..+7 | 0 | No setting call. The sid is compared in a stock tone-curve widget (`0x60e570fe`, `0x60ea2846`, MID family 692/962/965/968/997/1000/1003). This is UI-only and only reachable from a COLOR-profile tone editor, which this body doesn't have. | Yes [S] | No [E] | Medium |

**Recommendation: sid 961.**
- **What it is.** COLOR profile 1 Highlight tone, using the E-P7 "sid − 2" mapping [G for the meaning]. It is storage for a feature this body lacks: the picture-mode validator for sid 111 offers 7, 1–6, 8, 10, 9, 100–124, with no COLOR (11) and no MONO (12).
- **Reset value.** A full reset gives 0, which is Off.
- **Range check.** SetValue does **not** range-check this path [E]: values 7, 8 and −8 were stored and read back. The halation code must clamp or mask the value it reads (e.g. `v & 3`, or treat `v ∉ 0..3` as Off).

**Sid 981 caveats.**
- **Meaning and fit.** It is MONO profile 3. Its 0..3 range fits Off/Low/Med/High, and it may be "MONO grain" [G].
- **Default.** Its default is 1, so a full reset would land on Low unless the value is stored XOR 1.
- **Future mono path.** It becomes live if a future Caduceus mono path switches the pipeline to 12 with profile 3.

**Rejected or avoided.**
- **Already used by Caduceus:** 270, 511, 512, 617, 618, 449, 450, 383, 384, 692, 889–891, 111, 906, 971.
- **962/968, other members of the same family:**
  - Their numbers are noisy: 51 and 77 immediates, most of them GUI resource ids or malloc line numbers.
  - 962 has a facade-singleton call nearby (`0x60e9c517`).
  - Both are in the MID compare set.
- **963/966/969:** in the SH compare set. 964/966/967/969 also have non-zero defaults.
- **925–960 (per-profile saturation):** read by the 0x60cc COLOR branch and by the colour-property gatherer `0x6097a1b5`.
- **979/980:** also read by the MONO branch, and 980 has 48 immediates.

## Persistence mechanism found [S unless noted]

- **Property blocks.** The property system keeps several blocks; each block object holds `{u16 id, …, +12 table, +16 RAM, +20 size}`. Block objects are created at `0x6005d86b..`, the handles are kept at `0xa2748c58..70`, and the registry is filled at `0x6005d442..`.
- **Every settings sid is in block 90 (id 0x5a).** 1623 of the 1625 sid keys are there, including 617, 618, 111 and 270, which stock remembers across power-off.
  - Its table is at `0x600a29b0`: 1046 records of `{u16 key, u16 n, data}`, which are also the factory values.
  - Working RAM: `0x624e2000` (256 KB).
  - Registry: `0xa2736c50` (8 B per key>>4); lookup `0x6005d6a4`, getter `0x6005e6cf`, setter `0x6005e780`→`0x6005e7aa`.
  - Defaults are copied into RAM by cmd 7 of `0x6005dd42` → `0x6005e088`.
- **Flash backing.** Block 90's shadow `0xa2a66000` maps to flash **`0x40240000` / `0x40280000`**: two 0x40000-byte slots, from the slot table at `0x6002f118..0x6002f143` (the "fmem" module; `0x6005a330` classifies the addresses; string "fmem]can't exchange sdram --> flashrom address" at `0x6007dff9`).
  - Block 61 is backed the same way (`0xa2aa6000` ↔ `0x402c0000` / `0x402e0000`).
  - **Not traced:** the trigger that writes the shadow to flash (power-off or periodic).
- **The candidate lives in that block** [E]: the registered data pointer for 961 is `0x6250423a`, inside block 90 RAM (`0x624e2000..0x62522000`).
- **Per-mode planes.**
  - Key `0x8b64[plane*1625 + sid]` (helpers `0x602fbce8` / `0x602fbd11`) and `0x8b54[sid]` (`0x602fbd3d` / `0x602fbd63`).
  - Mode-change lists: table `0x604cb2d4`, 44 transitions × 1218 `{u16 sid, u8 plane}`.
  - 961, 965 and 981 use plane 0 in every transition, the same as 617/618/270. The value is therefore shared across all shooting modes.
- **Custom banks (Myset / C-modes).**
  - Key `0x85d4[bank*3250 + plane*1625 + sid]`, with 9 banks (copied by `0x602fbc7b` / `0x602fbc3f`).
  - Sid lists `0x604ce66e` (1208) and `0x604cefde` (1207), used from `0x602e5dc3`, include 961/965/981.
  - So a C-mode recalls the halation level it was saved with, like CC hue. This is not harmful.

## Boot path and resets (E-P7 `0x60192961` equivalent)

- **Boot tail.** Boot phase 2 (trace marks "2_l"/"2_o" around `0x601aad4a..6d`) calls **`0x601ac7cd`**.
  - It loads the settings store with `0x602daefb` (between the "MCS"/"MCE" trace strings).
  - Then it runs the per-boot resets, chosen by the boot reason from `0x60068558`:
    - Normal boot: `0x602da762` → `0x602db0e6`. If sid 10052 = 0 (its default), it resets the **26-id list `0x604cd464`**; otherwise it resets the **628-id list `0x604ce176`** and copies the planes to bank 0.
    - Boot reasons 7/9: `0x602da77a` → `0x602db11c`, which resets the **6-id list `0x604ce662`**, then `0x602e3676`.
  - Both are skipped when the gate byte `0x62262534` == 1 (checked in `0x602fc310`).
- **Reset primitive.** `0x602e5ba5(d0 = count, a0 = u16 list)`:
  1. Looks up the default with `0x602e6253` (u32 table `0x604cb4f0` + 4·sid; virtual sids at `0x604cce54` / `0x604cd038`).
  2. Sets it with setter `0x602fb89e`.
  3. Writes `0x8b54` and both planes.
  - A second list, `0x604ce65e` (2 ids), is used from `0x602db111`.
- **961, 965 and 981 are in none of these lists** [S].
  - [E] With each set to 3, all three survived the normal boot, the 7/9 path and the 10052 ≠ 0 path.
  - Control sid 267 (in the 26-id list), set to 2: reset to 0 by the normal and 628 paths, kept by the 7/9 path, as its list membership predicts.
- **Full resets set them to the default (961 → 0).**
  - The 1647-id list `0x604cd498` (`0x602e59da` → `0x602e5bf2`, also `0x602e675c`; probably the menu Full Reset [G]).
  - `0x602e59e2` / `0x602e5acc`, which reset every sid and all 9 banks. `0x602daefb` runs `0x602e5acc` when the store check `0x602fc45d` (`0x6005ec12`) fails.
  - The 628-id list (`0x602e59c9`, a Basic Reset candidate [G]) does not include them.

## Emulator checks [E]

Harness: `/scratch/spare/emu_spare.py` in container `em1emu`, copy in the session scratchpad `hal/emu_spare.py`. It is built on the `omdem1mk2_emu_rules` fixtures (`.bss`, `.data`, CPU id, task table, ROM memcpy/memset).

**Setup.**
- Registers block 90 with the stock `0x6005d707` (registry `0xa2736c50`, data `0x624e2008`).
- Sets the plane pointers `0x6225e400/404/408` from `0x6005e6a5`.

**Fixtures and stubs added on top of the rules harness.**
- Enlarged task table and kernel areas, hardware semaphore page `0x8fdff000`, heap `0x61a00000..`.
- The lazy lock-object pointer `0x61f9dfc4`, set non-zero.
- Stubbed:
  - trace/log calls `0x607a9436`, `0x607b1cea`, `0x607b1f15`, `0x607b4ba9`;
  - camera-state queries `0x607abb14`, `0x607abb7e` (return 0, the idle state);
  - post-set listeners `0x608647c0`, `0x60864039` (notification only; the store is done before them in `0x60863a8a`).

**Results.**
- **Facade `SetValue(sid, 0, v)` `0x60837170` → `GetValue` `0x60836747`:** for 961, 965 and 981, v = 0, 1, 2, 3 each returned `0x0` and read back v. The raw property getter agrees (core setter path).
- **Not emulated:** the listener side effects, real camera-state rejections (`0xF0000058`), and the flash write. On the camera this needs one power-cycle test: write 961 from a diagnostic or editor build, power off and on, read it back.

## Method

1. Parsed the sid table (`0x604f808c`), the validator (1215 records) and the defaults table.
2. Walked every property block table and mapped each sid key to its block.
3. Kept the sids whose validator includes 0..3 (210). Removed those in any boot reset list and those Caduceus already uses (176 left).
4. Disassembled all loaded sections (`/scratch/spare/full.dis`, 10.3 M lines) and collected every immediate equal to a candidate sid or key. Checked each hit's context (`ctxchk.py`) for setting calls (`0x602da802`, `0x602fb84b`, `0x602da60b`, the facade) as opposed to log and malloc line numbers or resource ids.
5. Searched u16 and u32 data tables for the sid (UI child lists, mode and bank lists, reset lists) and checked the descriptor registry (406 records, `0x6046ef3c`) and the per-sid UI init table (`0x61227b40`).
6. Traced both request fills: the main builder `0x602d1de5..`, and `0x60cc2f2a`, which switches on the pipeline mode through table `0x610110b4`.

## Open questions

1. **Flash write trigger.** The trigger and timing of the shadow → flash write for block 90 were not traced. This is the main reason the camera power-cycle test is still needed. The supporting evidence that block 90 persists comes from stock settings that are already remembered (617, 111, 270).
2. **Computed key reads.** Could anything read `0xF709` with a computed key (base + 16·n)? No such pattern was seen, but an exhaustive data-flow check was not done.
3. **When `0x602fc45d` fires.** Does the store check, and with it the full reset, fire after a firmware reflash? If it does, halation returns to Off after installing a build. That is harmless but worth stating in the user notes.
4. **The 628-id list.** Which menu action uses it (`0x602e59c9`), and what sets sid 10052?
5. **Range check.** SetValue does not range-check in emulation, so the doc's `0xF0000016` rejection probably comes from a state check, not from the validator. The halation reader must sanitise the value.
