# E-M1 II colour stills through the Art work-list builder (halation route, 4a alternative)

Date 2026-11-23. Harness: `tools/omdem1mk2_emu_art_route.py` (RESULT PASS, container `em1emu`; ~3 s).
[E] emulated, [S] static, [?] open or guessed.

## Verdict

- **Routing a marked colour still through the Art builder works, but it is not proven colour-identical.** All
  look-related inputs reach the development request byte for byte. Two other parts of the request change:
  1. **The output list (expected).** It now names records `0x1000` and `0x1060` instead of the main JPEG and the
     thumbnail.
  2. **`req+1838`, the development effect code.** It changes from `0` to `0x0400`. The Art development callback
     `0x6039271b` writes it, and it makes the ISP setup (`0x6037666f`) run **combiner 13** (`0x603dd101`) inside
     the development. Plain stills run no combiner. Combiner 13 programs bank (ctx+8)+7364 with fixed constants
     (`0x1002`, `0xeee`, `0x8080ff`, `0x151500`, `0x04000400`). They look like pass-through values, but whether
     they change pixels is **[?]**.
- **The Art route without a code hook (key class byte = 1) is worse.** It also changes the job key in the request
  (`req+8` = 1, so the colour stage sees key `0x010000pm`). It also drops `req+1858` and shifts every key-based
  test. Not recommended.
- **Recommendation: the Art route (class 0 + marker), if one camera A/B check passes.** The check is a neutral
  route with no pass, compared against plain stills (see Q5). Until then, the record-5 route from the
  plain-route report is the only route whose development request differs from stock **only** in output routing.
  But it needs three instruction hooks, a full-size record 5 on 4:3 (stock never does this), and second-encode
  juggling. Its review image shows no halation.

## Q1. Minimal change that sends a marked job to the Art builder

- **Dispatcher `0x6039009a`, all [S]:**
  - job+26 must be 0 or 4, and job+31 = 0.
  - job+12 (key class = params+8) == 1 → Art (`0x60391c1c` → `0x60392e0d`).
  - job+12 ∈ {0,2} and job+11308 == 12 → Art too.
  - Otherwise the call at **`0x603900ec`: `dd 84 3b 01 00 00 04` = `call 0x603a3c70,[],4`** → colour builder
    `0x603a63f4`.
- **Recommended hook (one 4-byte operand edit plus a stub) [E].**
  - Repoint the rel32 at `0x603900ed` to `hl_route`: `movbu (35,a0),d0; cmp 0xa5,d0; bne →; jmp 0x60391c1c;
    → jmp 0x603a3c70`.
  - a0 = job and frame [],4 on both targets, and only d0 (the return value) is clobbered.
  - The marker is the planned params+31 → job+35 byte from hl_flag.
  - What the harness shows for Vivid / Natural / Color Creator:
    - The marked job gets the Soft-Focus-only Art list `0x60392df2, 0x6039276e, 0x60398e6f, 0x6039905e, 0x60391a9b`.
    - It equals the plain job except job+35, the list, and the builder hook word job+11304 (`0x603a3c79` →
      `0x60391c3f`).
    - With stock flags (no 0x80, no marker), the job is byte for byte the stock job.
- **Key-class alternative [E]:** params+8 = 1 gives the same list and job+11308 = `0x010000pm`. It also runs the Art
  secondary setup `0x60394083` (a no-op here: it only acts on flags 0x40000 / 0x100000) and the destructor
  `0x60394456` [S]. Its colour side effects are listed in Q2.
- **The class-0 hook skips the Art secondary setup and destructor (`0x6039012e` / `0x60390169`, also key-class
  based).** Safe for 0x80-only jobs, because secondary does nothing for them [E fixture, S].
- **Flag 0x80 is required.** A marked job without 0x80 gets `0x60392df2, 0x6039276e, 0x60391a9b`. Nothing
  encodes `0x1000` (no record 5) on the class-0 route [E, exploratory run, not kept in the harness].
- **Blend Setup `0x60398ee1` is not in this list.** The builder keeps it in a2 and uses it only when another
  effect follows (0x300, 0x400, …, job+32). A Soft-Focus-only list ends with `0x6039905e` [S, E].

## Q2. Development request, plain vs Art (same capture, job+36 block pattern-filled) [E]

- Both routes call the same development `0x603a44ca` [S]. The Art item `0x6039276e` passes its own outputs; the
  plain item `0x603a5df6` builds them from the job+4756 table.
- **The first 2048 request bytes differ only in:**

| Field | Plain | Art (class 0) |
|---|---|---|
| req+916.. output 0 | main JPEG `0x0702` (3:2: 5184x3456), +42 = 4 | record `0x1000`, `0x0302`, 5184x3888 |
| req+972.. output 1 | thumbnail record `0x0302` 160x120 (3:2 window 160x106 @7) | record `0x1060`, `0x0305`, 160x120 |
| req+1838 effect | 0 | `0x0400` → combiner 13 in development |

- **Everything else is identical** on 4:3 and 3:2. That covers the job key at req+8..11 and the 12-sector S at
  req+1816 (cc_sel), plus every field the request init copies from the job+36 block (req+1610..1880). Those
  fields carry picture mode, profile, saturation, Color Creator 617/618, tone 383/384/692, NR, sharpness,
  gradation, aspect and size. Each of them gets the same bytes on both routes.
- The colour-stage selector `0x603ec82c` reads req+8..11, +12, +1524 and +1816, not +1838 [S]. So with the same
  request it should take the same branch and feed builder `0x603ec642` the same inputs. That is [E] for the
  request bytes and [S] for the selector, which was not run.
- **Class-1 variant:** also req+8 = 1 (key class) and req+1858 = 0 (block+5556 not copied, `0x60390a08`). The
  colour stage and cc_sel then see key `0x0100000a`/… instead of the picture mode [S].
- Other (non-colour) differences [S]:
  - **RAW pre-stage.** The plain route runs `0x603a4133` when job+11339 is set (builder hook `0x603a3c79`:
    block+5524 == 2, from capture+24172/24170). The Art hook `0x60391c3f` returns 0, so marked jobs skip it, as
    stock Art Filters do. The feature behind it is unknown [?].
  - **The 0x10000-flag branch at `0x603a5483`** (req+1838 = 0xfe00 …) is skipped for class 1 only. Unused for
    these stills, since the converter clears 0x10000.

## Q3. Art work list for a marked Vivid still [E]

| Item | Result (4:3 and 3:2) |
|---|---|
| `0x60392df2` | pre-stage only if job+11340; nothing here |
| `0x6039276e` | development → **record `0x1000`: 0x0302, 5184x3888, stride 5184, window offsets 0, 2·W·H = 40.3 MB**; `0x1060` 0x0305 160x120. Waits for it; nothing pending afterwards |
| `0x60398e6f` | stage 0xf005 / effect 0x0401: `0x1060` → `0x1061` (full-size 0x0302); left pending at item+8 |
| `0x6039905e` | via `0x603920d6` + edit callback `0x603992f1`. Three submits: (1) **blend**, stage 0xf005 / effect 0x0402: `0x1000` + `0x1061` → **record 3, full-size 0x0302** (selector → combiner 11), chained on the blur; (2) **record 3 → main JPEG** (rows 3888 / 3456), chained on the blend; the CPU waits on this one; (3) thumbnail via a 740x556/494 record 4 |
| `0x60391a9b` | 4:3: nothing. 3:2: encodes the letterboxed 160x106 record 5 into the thumbnail |

- **No CPU point exists between the blend and the main encode.** The pass therefore cannot run after the blend on
  this list. It can run on **record `0x1000` after item 1**:
  - The development is waited for and nothing is pending.
  - `0x60398e6f` reads only `0x1060`.
  - With the 4c neutral combiner 11 (A = 1024, B = 0) for marked jobs, record 3 = `0x1000`, so the pass result
    reaches the JPEG through the stock encode.
- **Hook:** data edit of the immediate at **`0x60393a54`** (insn `0x60393a52`: `fc cd 6f 8e 39 60` = `mov
  0x60398e6f,d1`, the only load of that address). The wrapper (`calls`, a0 = job) gates on job+35, runs `hl_pass`
  on bufidx(0x1000), then jumps to `0x60398e6f`. Every Soft Focus Art shot passes through it, so it must gate.
- **3:2 crop [?]:** with the full-frame RAW fixture, the Art development makes 5184x3888 and the encode takes rows
  0..3455 (offset 0). On camera, the crop comes from the real RAW record window. Stock Art Filters in 3:2 use
  this path, so it is expected to be right, but it is unverified here.

## Q4. Costs vs the plain route

- **Memory [E sizes]:** at 5184x3888, `0x1000` + `0x1061` + record 3 are each 40.3 MB and are alive together
  during the blend: **~121 MB** of full-size 0x0302, plus 0x1060 (77 KB) and record 4 (~0.8 MB). The plain route
  has none. The record-5 route adds one 40 MB buffer.
- **Time [S]:**
  - The development is the same.
  - The Art route adds a blur upscale (writes 40 MB), a blend (reads 80, writes 40), a JPEG encode from memory
    instead of inline, and the pass.
  - Roughly the cost of a stock Art Filter Soft Focus shot. Not measured. The watchdog budget (4g) still
    applies; the pass runs in the runner task as on the E-P7.
- **Aspect:** both 4:3 and 3:2 work with the same list [E]. No 4:3 aspect bypass is needed (unlike the record-5
  route).
- **RAW+JPEG and burst:** not emulated [?]. This is the stock Art Filter (Soft Focus) path, which the camera
  already runs with RAW+JPEG and sequential shooting. Expect a lower burst depth and rate for marked shots.
- **Review image [S]:** the Art development writes no job+4756 entries (only `0x1000`/`0x1060`). The main JPEG and
  thumbnail come from record 3 [E], so the review image should come from the output stage too and **show the
  halation**. Review entries were not in the fixture (a fabricated 0x0302 review entry made the plain development
  fail; not pursued).

## Q5. Recommendation

1. **Art route.** Hook `0x603900ec` (class 0 + marker), the `hl_pass` wrapper behind `0x60393a54`, and neutral
   combiner 11 for marked jobs (4c stubs).
   - Uses the stock, camera-exercised Soft Focus pipeline on every aspect.
   - One instruction-operand edit and one data edit; the review shows the glow.
   - The only colour risk is combiner 13 (req+1838 = 0x0400).
2. **Before a glow build, a camera A/B diagnostic:**
   - Marked stills get the Art route, neutral combiner 11 and no pass.
   - Compare them with plain stills of the same tripod scene (Vivid, Natural, CC + look), for example by histogram
     or pixel difference of JPEGs at fixed exposure.
   - Identical → keep the Art route.
   - Different → either hook `0x6039272f` (`2c 00 04` `mov 1024,d0`, then `movhu d0,(1838,a1)`) to keep effect 0
     for marked jobs (whether the 0x0302 memory output still works with effect 0 is [?]), or fall back to the
     record-5 route.
3. **The record-5 route remains the fallback.** Its development is colour-identical except output routing, but it
   costs three instruction hooks, untested full-size record 5 on 4:3, a second-encode fix-up, and a review image
   without halation.

## Unresolved

- Pixel effect of combiner 13 in development (bank constants above). The emulator can show the bank values but not
  the ISP result.
- The feature behind block+5524 == 2 (capture+24172/24170), which marked jobs would no longer get.
- 3:2 crop with a real RAW record; RAW+JPEG and burst on the Art route; review entries.
- Whether `0x60391c2e`/`0x60394456` matter for any marked job (only flags 0x40000/0x100000 trigger them).

Status: DONE_WITH_CONCERNS
Summary: A one-operand hook at 0x603900ec (marker-gated) sends marked colour stills to the Art builder. Their development request then matches the plain one except outputs and req+1838 = 0x0400, which adds combiner 13 (colour effect unproven). The full-size 0x0302 record 0x1000 is CPU-visible after the development, and the pass can run there before the neutralised Soft Focus blend. Recommend this route after a camera A/B check of combiner 13, keeping the record-5 route as fallback.
