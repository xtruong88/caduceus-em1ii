# E-M1 II halation step 4b: per-job "halation forced this Soft Focus" marker

Date 2026-11-23. Image `em1mk2/extracted/00_0100_40560020.decoded.bin` (base 0x60021020), disassembly
`/scratch/spare/full.dis` in `em1emu`. [S] static, [E] emulated, [?] guess. Nothing was emulated in this research.

## 1. Where the params block lives: on the stack, copied by value into the job

- **Fill functions** [S]: `0x6041dda4` (holds the converter call 0x6041dde2) and `0x60420ab9` (holds 0x60420af1).
  Both take a0 = source request, a1 = params block (`mov a1,a2`). Neither is the job.
- **Callers** [S]: `0x6041dda4` from 0x60415cde, 0x6041ec34, 0x60423eac, 0x60429a41, 0x60429c24, 0x60429cfe,
  0x6042b452; `0x60420ab9` from 0x6042b7d3. Every caller does the same thing:
  `a2 = sp+16` (or a stack slot) → `memset(a2, 0, 32)` (`0x47001177`) → fill(request, a2) →
  **job constructor `0x6038f173`(a0 = params, d0 = 0, a1 = &status)** → `mov d0,(36,request)`.
  So the params block is a **32-byte stack local**, zeroed per shot, and the returned job pointer is kept at
  **request+36** (accessor `0x6038f5eb` returns job+36, so request+36 holds the raw job pointer).
- **Constructor `0x6038f173`** [S]: `malloc(15484)` (`0x600231fe`) → fresh job each shot. memsets job+36 (6556),
  +6592 (4224), +10816 (84), +10900 (84), +10984 (192, work list), +11176 (104), +11280 (14), +14304, +14476, +14572,
  +15468; +11312 = 16, +11314..11318 = 0, many words 0. Then **copies the 8 params words to job+4..job+35**
  (0x6038f29e..0x6038f2aa: `a3 = job+4`, d1 = -8 .. 0). So **job = params − 4 by layout, at a new address**:
  | params | job | meaning |
  |---|---|---|
  | +0 | +4 | callback (0x6041f8ae / 0x6042169d) |
  | +4 | +8 | source request pointer |
  | +8..11 | +12..15 | key bytes (0x6042270e → 0x6038492b); packed key also at job+11308 |
  | +12 | +16 | flag word (converter 0x6042285e; hl_flag ORs 0x80 here) |
  | +16 | +20 | type (kind mapper 0x6042257f) |
  | +18..+26, +29 | +22..+30, +33 | bytes set by the two fills (0x6041dda4: 18,19,21,22,26,29; 0x60420ab9: 18..22,24) |
  | +23, +30 | +27, +34 | read by the constructor (0x6038f3b3, 0x6038f305); never written by the two fills |
  | +25 | +29 | read by the destructor 0x6038f5ab |
  | **+28, +31** | **+32, +35** | **written by neither fill; no reader found (survey below)** |
- After the copy the constructor still edits job+16: key table `0x6053b818` (keys 0x01010065 and 0x01010071 OR 0x80;
  others 0x400/0x40/0x200000/0x100/0x200/0x20000/0x40000/0x100000) when key byte 0 == 1, and it **clears 0x80** (and
  0x40, 0x300, 0x4000, 0x40000, 0x100000) when type & 0xF0 == 0x40 or type & 0xF00 == 0x100 (0x6038f45e) [S].
- Only two call sites reach the converter (`grep 0x6042285e` = 2, no decimal function-pointer use) [S], both with
  a1 = params+12. So at hl_flag, **a2 = params+12** and params+31 is `(19,a2)`.

## 2. Ordering

- Request side, one call chain, no wait in between [S]: memset → fill (key, **converter + hl_flag**, type) →
  constructor → request+36 = job → `0x6041df76` / `0x6041de55` / `0x6041eab9` / `0x6041eb8d` (fill job+36.. via
  0x6038f5eb). Conversion and construction of one shot cannot be split by another shot's conversion inside this chain.
- Work list [S]: builder `0x60393e12` writes items at job+10984 (12 B each), count at job+11314; runners
  `0x6039271b`/`0x603929cc`/`0x60392b4f` call the item at index job+11312 (`calls (a2)`, a0 = job). `0x603929cc` is
  itself pushed as an item (0x60393e38) and `0x6039271b` is a callback (0x60392850), so items advance on completions:
  the list runs **asynchronously** to the request side.
- Whether shot N's blend item always runs before shot N+1's conversion: **not proven** [?]. Each job is a separate
  heap object reached through its own request+36, which suggests several jobs can be alive at once (burst). Task names
  for these paths are not in ARCHITECTURE_AND_MEMORY_MAP.md §3 (it lists GUI/movie/battery tasks only).
- The job-module code (0x6038b000–0x603b0000) never reads request+28 / +194 / +116 or capture+24951 / +24203 [S]:
  the job is built to be self-contained once constructed.

## 3. Marker options, ranked by safety

**A. By-value byte in the copied params: params+31 → job+35 (recommended).**
- hl_flag, in the same gated branch that ORs 0x80: `mov MAGIC,d0; movbu d0,(19,a2)` (a2 = params+12). MAGIC a fixed
  non-zero byte (e.g. 0xA5) rather than 1, so a stray value from another builder is unlikely to match.
- hl_gs (a0 = job): forced ⟺ `(job+16) & 0x80` and `movbu (35,a0) == MAGIC`. Else 0x80 is stock (Art Effect 1 or
  Art Filter key 0x01010065/0x01010071): stock blend; halation pass only if the stage is on.
- Combiner 11/12 stubs: request = ctx+4 = job+11364, so the byte is at **request − 11329**; also test
  (request − 11348) & 0x80 (job+16).
- Why safest: travels with the job by value; the stack block is memset each shot, so no stale marker; a new malloc'd
  job each shot, so burst, address reuse and aborted shots (constructor fails → params dropped) cannot leak a decision
  to another job. No heap-P state, no lifetime question.
- Evidence it is unused [S, heuristic, not a proof]: neither fill writes params+28..31; whole image has 118
  `(35,aN)` and 105 `(31,aN)` sites; none of the 35-sites lies within ±200 lines of job-specific code (offsets
  11308/11312/10984/11364/6592/11341/15468, accessors 0x6038f5eb/0x60390dbe, constructor); the five 31-sites near job
  code use other bases (job+11244 struct at 0x6035f2b4/0x6035f333, job+4756 records at 0x6038fc46, 0x60391319).
  The job core 0x6038f5ab–0x60391000 reads job+20..+29 and +34 (via other bases) but never +32..+35. Word reads at
  (32,aN) near job code are stores into other structs (0x6039d9d7/0x6039e268 etc.), not job+32 reads.
- What could go wrong: an unseen reader of the word job+32 or byte job+35 through a biased base (e.g. a2 = job+16 →
  (19,a2)); the other constructors (0x6035d6e4 via 0x6033c437, 0x6041999a, 0x60d19672) fill params from other
  buffers and were not checked for +31 (they never pass the converter, so hl_flag never marks them; worst case is a
  1/256 MAGIC match on a job that also has 0x80 → neutral blend on that shot).
- Proof still needed (4b): in the emulator, run constructor + builder + blend setup + combiner + destructor with
  job+35 = 0 and = MAGIC and show identical stock outputs; add a watchpoint (read hook) on job+32..35 during those runs.

**B. Heap-P table keyed by request pointer** (hl_flag writes {request, forced} on every conversion; hl_gs looks up
job+8, combiner looks up (request−11356)). Works only if a request is not re-converted while its previous job still
waits for its blend item; ordering (§2) is unproven, aborted shots leave stale entries, needs table sizing. Second.

**C. Recompute from job+8 → request → capture** (forced ⟺ 0x80 and capture+24951 == 0 and capture+24203 < 100).
Capture = slot table `0x6224a9a0`[request+116 id 1..64] +12 (`0x602c710e`). Nothing in the job module dereferences
these at work-list time, so the capture may be recycled or edited by then; also re-reading sid 961 could disagree with
the conversion. Third; useful only as a debug cross-check.

**D. Last-decision global.** Safe only if every shot's work list finishes before the next conversion; not shown,
and a burst would mislabel jobs. Reject.

## 4. What else in the job records the Art Effect

- job+16 flags: 0x80 = Soft Focus from any source (converter Art Effect 1, key table, or hl_flag) [S].
- job+12..15 / job+11308 key: built from picture mode and capture+24950 (byte 0 set only when picture mode ≥ 100);
  keys 0x01010065 / 0x01010071 add 0x80 in the constructor [S]. With hl_flag's gate (picture mode < 100) these keys
  should not occur [?].
- No copy of the Art Effect byte (capture+24951) itself was found in the job [S, by the offset search]; job+8
  (request pointer) is the only way back to it (option C).

## Unresolved

1. Exact task/queue that runs the work list and whether conversions of later shots overtake it (only matters for B/D).
2. Exhaustive reader proof for job+32..35 (emulator watchpoint runs recommended above).
3. What 0x6033c437 / 0x6041999a / 0x60d19672 put in params+28..31.

Status: DONE_WITH_CONCERNS
Summary: The params block is a zeroed 32-byte stack local copied by value into a fresh malloc'd job at job+4..+35 by
constructor 0x6038f173 (job+8 = request, job+16 = flags), so the safest marker is a magic byte hl_flag writes at
params+31 → job+35 (combiner: request−11329), read together with job+16 & 0x80. Unused-ness of job+32..35 rests on a
static heuristic survey and still needs an emulator watchpoint proof; shot ordering vs the async work list is unproven.
