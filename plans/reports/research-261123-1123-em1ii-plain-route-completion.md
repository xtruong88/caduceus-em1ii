# E-M1 II plain colour stills: where a CPU halation pass can run (4a)

Date 2026-11-23. Harness: `tools/omdem1mk2_emu_plain_route.py` (RESULT PASS, container `em1emu`).
[S] static, [E] emulated (real capture entry + real items, fixtures listed at the end), [?] guess.

## Recommendation (first)

1. **Stock plain stills never hold the developed image in a CPU-visible buffer** [E]. The development request
   (item `0x603a5df6` → `0x603a44ca`) writes the **main JPEG output entry directly** (job+4756 table, format
   `0x0702`). The only `0x0302` record is the 160x120 EXIF-thumbnail intermediate. There is no record `0x1000`,
   and no full-size record at any point. So no hook point meets (b) without changing the route. A wrapper on the
   last item, or a callback word, would see no image.
2. **The cheapest working route uses stock machinery, the one the thumbnail already uses.** Give the main JPEG
   entry the thumbnail's flag (+42 bit 3, `0x208` instead of `4`) for halation jobs only. `0x603a573d` then makes the
   development write a **full-size record id 5** (`0x0302`, stride = W, window offsets 0, +72 = 2·W·H). Item 2
   **waits for it synchronously** and leaves nothing pending. The last item `0x60391a9b` encodes record 5 into the main
   JPEG [E, 3:2]. On 4:3 (aspect index job+23 = 1) the aspect test at `0x603a590c` must also fail for marked jobs [E].
3. **Hook = data edit on the last work-list word:** the immediate at `0x6039011f` (insn `0x6039011d`, stock
   `fc ce 9b 1a 39 60` = `mov 0x60391a9b,d2`). Every list gets this word, appended by `0x6039011d` in dispatcher
   `0x6039009a`, so the edit routes every job through `hl_ob`. `hl_ob` (`calls`, a0 = job) gates on the job+35
   marker. On a marked job it runs `hl_pass` on bufidx(5) and calls `0x60391a9b` (main encode). It then waits for
   and clears item[cursor]+8 (`0x603901f3`), releases the main record (`0x6038beea`), sets the main entry +42 back to 4,
   and returns through `0x60391a9b` again (thumbnail encode). [E] for the firmware side of each step (check 5); the
   wrapper itself is not written.
4. **4:3 jobs have no last item at all [E].** The dispatcher appends `0x60391a9b` only when job+23 ≠ 1
   (`0x60390102: f8 47 13 a5 01 c8 23` = `movbu (19,a3),d1; cmp 1,d1; beq 0x6039012a`). On the real capture entry,
   request+283 = 1 gives 3 items and request+283 = 2 gives 4 (scratch run). The "4 items" of the earlier 4a test came
   from aspect index 0, which is not a real value. So on 4:3, the camera default, the `0x6039011f` word is never
   used, and marked 4:3 jobs also need this test bypassed (hook (c)).
5. Instruction hooks still needed, since none has a data-only form (hook (c) is the one in point 4):
   - **(a) main-entry flag.** The capture builder writes `mov 4,d0` at `0x60421bbd`, the +42 argument for
     `0x60384567`, before the job exists; gate it on the same stage/colour test as `hl_flag`. Or, inside the job:
     set main +42 at the dev item's start.
   - **(b) 4:3 aspect test.** At `0x603a5906..0x603a590f` (stock `5e 24 22 13 f0 42 a0 01 c9 05`, then
     `cc 49 01` jmp `0x603a5a59`), on a marked job jump to `0x603a5913` with a2 = job+23 intact.
   - **Fallback without (b):** halation only for 3:2 / 16:9 / … shots. Not acceptable as a product, but a first
     camera test.

Alternative (not pursued): send marked colour jobs through the Art builder `0x60392e0d` (dispatcher picks it when
job+12 == 1, or job+11308 == 12 with job+12 ∈ {0,2}; job+12 = params+8 from `0x6042270e`/`0x6038492b`). That reuses
the planned Soft Focus/`0x1000` blend hook, but colour equivalence with the plain route is unproven (cf. the E-P7
key-11/12 bank work). Higher risk.

## Q1. The four items [E unless marked]

| Item | Role | Buffers |
|---|---|---|
| `0x603a5d7d` | only if job+11340 ≠ 0: `0x603a3c89` (a pre-stage with 0x0B00 descriptors) [S]; plain fixture: no-op | – |
| `0x603a5d96` | moves item[cursor−1]+8 to its own +8; if job+11339 ≠ 0 submits `0x603a4133(job,&pend,0,0x01000002)` [S] | RAW 0x01000002 |
| `0x603a5df6` | `0x603a44ca(job,&pend,0,1)`: development. Looks up 0x01000002 (RAW) and 0x0D01000F, temps 7,8,10–14 [S]. One request: RAW → output list at req+916 built by `0x603a573d` from the job+4756 entries. **Waits for it (`0x603a557c` → `0x603901f3`) whenever the RAW record exists, and job+11320 = 0.** Releases temps + RAW. Then `0x603a42fb` encodes a record-4 intermediate (4:3) into the thumbnail, and that request is left pending at item+8. | writes main JPEG 0x0702 directly; thumbnail via record 4 (4:3) or record 5 (other aspects, letterboxed 160x120 window 160x106 at row 7, after a grey fill `0x6038ce2d`) |
| `0x60391a9b` | bufidx(5); if absent passes pending on and returns 0. Else: request at job+11364, src = record 5 (req+20), dst = first job+4756 entry with format>>8 == 7 and +42 bit 3 (req+340), submit chained on item[cursor−1]+8, token at item[cursor]+8 | reads record 5 → JPEG entry |

- Output entries [S]: main JPEG `0x0702` at `0x60421bb4` (bus = request+180 + 41984 header room, +42 = 4). The
  160x120 thumbnail `0x0702` is built at `0x60421e76` (+42 = 0x208); 0x0302 entries (review) at `0x60421f97` /
  `0x60422143`. In emulation an added 0x0302 review entry is written by the same development request.
- **Where the image is "final":** only inside the development request. In the stock route it goes straight into the
  JPEG stream, so there is no point where a CPU could see the full-size YCbCr.

## Q2. Hook point (with the route change above)

- (a) job: `hl_ob` gets a0 = job from the runner `0x6038fb5f calls (a1)` [E check 1, redirect dispatched].
- (b) finished image: record 5 after item 2. Item 2 waited for the development and nothing is pending at item 3
  [E checks 3–4]. As a guard, `hl_ob` can still wait on item[cursor−1]+8 if it is non-zero, then zero it, as stock
  does at `0x603a557c..0x603a558a`.
- (c) consumer not started: the main encode is submitted only by `0x60391a9b`, which `hl_ob` calls after the pass [E].
- (d) blocking: the runner `0x6038fae5` runs all items back to back in one call. Item 2 already blocks there on
  `0x603901f3`, the same situation as the E-P7 `gc_ob` [S]. The 10 s watchdog budget (4g) still applies.
- Stock bytes: `0x6039011d: fc ce 9b 1a 39 60`. `0x60421bbd: mov 4,d0` (entry flag). `0x603a5906:
  5e 24 22 13 f0 42 a0 01 c9 05 cc 49 01`. `0x603a5682: dd 79 ec f0 50 1c a0` (call `0x603a42fb`, not needed).

## Q3. Buffer/format for these jobs

- Not `0x1000`. With the route change it is **record id 5**, an 88-byte record at job+6592+88·idx, found by bufidx
  `0x6038c01c(job, 5)`. Format `0x0302`, stride = (W+31)&~31, +16/+18 = W/H, +20/+22 = 0, +72 = 2·stride·H, bus from
  job callback op 19 (`0x60380399`) [E with stub].
- It is the layout `hl_pass` already checks. Only the bus range on camera is unknown; `hl_pass` handles direct and
  windowed addresses.
- **Two records can carry id 5** (main, and the letterboxed thumbnail on non-4:3). bufidx returns the lowest slot.
  The main one was allocated first in every run, but `hl_ob` should pick the id-5 record whose size matches the main
  entry, not the first match [?].
- Stock thumbnail records (160x120, window offsets ≠ 0 on 3:2) must not be passed to `hl_pass`.

## Q4. Safety

- **Thumbnail collision [E].** `0x60391a9b` encodes into the first JPEG entry with +42 bit 3. After the main encode,
  a second call would write the thumbnail into the **main JPEG**. The main entry's +42 must return to 4 before that
  call. With the flag left set, the thumbnail would also not be encoded.
- **Second encode token [S].** A second encode overwrites item[3]+8. `hl_ob` must wait for and clear the first token
  first, or the job-end wait `0x6038fd77` (which waits only on the last item's token) leaks it.
- **Wait semantics [S].** `0x603901f3` waits through `0x6038c448(1000)`, then frees the token (memset 56) and
  releases the ids in token+42. Run the pass only when it returns 0.
- **Memory.** Every marked shot gains a full-size record 5 (2·W·H, 40 MB at 5184x3888). Stock never allocates it for
  plain stills; stock record 5 is 160x120. Burst/RAW+JPEG memory pressure is untested [?]. The record is freed after
  encode; `hl_ob` can release the main record early (step 3).
- **Concurrency.** After item 2's wait no request references record 5 until `0x60391a9b` submits [E]. The review image
  is written by the development request, so it shows the photo **without** halation [E, cosmetic].
- **Interrupts.** The pass runs in the runner's task; `hl_pass` already locks per window piece [S].
- **Other paths.**
  - The dispatcher appends `0x60391a9b` only when (job+11320 = 0 or job+28 = 1), job+23 ≠ 1 and the builder
    returned 0 (`0x603900f3`) [S]. The 4:3 case is [E], see recommendation 4.
  - Ordinary capture fixtures have job+11320 = 0, and the builder variants job+21 = 2 / job+25 ≠ 0 were not run [?].
  - `0x603a44ca` has 20+ callers (Art routes); hook (b) sits in `0x603a573d`, which serves all of them, so gate it on
    the marker.

## Verified vs not

- **Emulated (`tools/omdem1mk2_emu_plain_route.py`):**
  1. The immediate redirect changes only item 3 and is dispatched with a0 = job.
  2. Stock 4:3 and 3:2 with a realistic main+thumbnail table: main JPEG written directly; only 160x120 records.
  3. Main +42 = 0x208 on 3:2 gives a full-size record 5 with offsets 0, waited, encoded by `0x60391a9b`.
  4. The same on 4:3 only with the aspect test failed.
  5. Second-encode behaviour, including the main-entry collision.
- **Fixtures:**
  - The RAW record and the JPEG entries are fabricated. Real values come from the job+36 block, copied by
    `0x6041cf00` / `0x6033c92c` from the capture side.
  - Logging stubs for submit `0x60390536`, wait `0x603901f3`, release `0x6038beea` and job callback `0x60380399`;
    fill `0x6038ce2d` returns 0.
  - Main-record release in check 5 is done by clearing its id in Python.
  - No pixels are processed; the hardware result is assumed from the request descriptors.
- **Not emulated:**
  - the entry-flag hook and `hl_ob` itself;
  - real job+4756 contents for every picture mode, RAW+JPEG and bursts;
  - whether the JPEG engine accepts a record-5 source at full size on 4:3. Stock does this only on 3:2 etc. and for
    thumbnails, so it is plausible but unproven on 4:3 [?].

## Unresolved

- The real output table per shot (entry order, review entries, RAW+JPEG): it decides which id-5 record is the main one.
- Job+11320 / job+11339 / job+11340 values on camera.
- The Art-builder route as an alternative (colour equivalence).

Status: DONE_WITH_CONCERNS
Summary: Stock plain colour stills have no CPU-visible developed image: the development request writes the main JPEG directly, and the only 0x0302 records are 160x120 thumbnail intermediates (emulated). 4:3 jobs do not even get the last item 0x60391a9b. A workable route forces the main JPEG through a full-size record 5 (entry +42 bit 3; on 4:3 also the aspect bypass and the item append) and runs the pass in a wrapper behind the data edit at 0x6039011f. That needs small instruction hooks and careful handling of the second encode for the thumbnail.
