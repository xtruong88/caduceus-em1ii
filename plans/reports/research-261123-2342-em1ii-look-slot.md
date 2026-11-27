# E-M1 II 3.70: setting slot for the remembered look, and Color Creator's raw picture mode

Date 2026-11-23. Image: OM catalog 3.70 main (`em1mk2/extracted/00_0100_40560020.decoded.bin`). Tags: **[E]** emulator,
**[S]** static. Builds on `research-261120-1400-em1ii-spare-setting.md` (sid 961 for the Halo stage).

## Answer

- **Slot: sid 965** (property `0xF719` index 1, s8 storage; E-P7 "COLOR1 shadow", which this body never offers).
- **Encoding:** `v = 1 + look + 32 * (source is the card)`, so 1..16 for built-in looks and 33..64 for card looks.
  `v = 0` (the default and the value after a full reset) means nothing is remembered.
- **Color Creator's raw `0x9481` value: 9** (facade sid 111 = 21).

## Sid 965

| Check | Result |
|---|---|
| Validator | −7..+7, but SetValue does not range-check this path [E]. Facade SetValue/GetValue round-trip 0..64, 65, 100, 127 and −1 [E]. |
| Raw getter | `0x6005e6cf(0xF719, 1)` returns the stored value (this is what the restore reads) [E]. |
| Readers | 7 immediates: 5 are log or malloc line numbers (`0x60062a37`, `0x60a8fbc3`, `0x60d25f6d`), and 2 are `cmp 965` in the COLOR tone-curve widget, which this body cannot reach (`0x60e570fe`, `0x60ea2846`). Key `0xF719` never appears as an immediate [S]. |
| Boot resets | Not in the 26, 628 or 6-id lists. Values 1, 33 and 64 survive the normal, 10052 ≠ 0 and 7/9 paths, while control sid 267 resets as its list says [E]. |
| Neighbours | Sids 961, 964 and 966 are unchanged after writes [E]. |
| Persistence | Block 90, like 617/618/111 [S] (spare-setting report). Not emulated: the flash write itself. |
| Banks | In the Myset / C-mode lists: a C-mode recalls the look it was saved with. |

**Rejected.**
- 961 is the Halo stage.
- 981 is MONO profile 3, which a future true-mono path (key 12) may read.
- Others were not needed: 965 holds the full range.

## Boot store check `0x602fc45d`

`0x6005ec12` only reads and clears a flag at `0xa267b00c` [S]. The flag is set in `0x6005ef22..efc7` when
`0x6005c1a2` finds no valid flash slot for the settings block (`0x6005c039` picks the slot; 2 = none valid). Defaults
are then reloaded with cmd 7. This is a whole-block check, not a per-value range check, so an out-of-validator value
such as 33 does not trigger a reset.

## Raw picture mode

The raw getter and facade GetValue(111) were read for raw bytes 0..63, and for 0x100/0x200 + 0..0x1f [E]:

| raw | 1 | 2 | 3 | 4 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|
| GUI (sid 111) | 0 | 1 | 2 | 5 | 6 | 7 | 20 | **21** | 28 |

- The property is one byte: the getter returns `0x9` for a stored `0x109`.
- The SCP code formats the Color Creator tile when sid 111 = 21. `cc_init` stores the raw getter value in `P_CCMODE`, so
  the restore sets `P_CCMODE = 9`.

## Not verified

- The flash write at power-off (camera).
- Whether live view redraws. Added after review: a restored colour look ends with SetValue(618, its own value), the
  editor's `lv_refresh`. On the camera in v0.3b3, P changes alone did not redraw live view. Emulated: exactly one
  SetValue, and no stored setting changes.
- The 618 write from the HLS (half-press) task. The HLS loop is a message pump, and no direct setting call was seen in
  it. The post-set notifier `0x608647c0` only allocates a 32-byte message (`0x60a8fbc3`) and posts it
  (`0x607ee8c8`) [S]; no blocking wait was seen there.
