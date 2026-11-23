#!/usr/bin/env python3
"""Reference model of the E-M1 Mark II halation pass (patches/omdem1mk2/halation/hl_pass.s), integer for integer.

It is the E-P7 h1/h2 algorithm unchanged (patches/halation/verify.py `model`, camera-proven on the E-P7: a red / orange
halo around an LED strip, docs/HALATION_RED.md §15), on a 0x0302 buffer (2 B/px: Y0 Cb Y1 Cr per pixel pair):
  A  Y of every 2nd pixel on every 4th row (from row 2): cell += max(0, Y - THR) >> 2, saturating at 248, 64 x 64 cells;
  B  two [1 2 1] / 4 passes per axis (zero beyond the ends); u = min(255, 21 v >> 3); g = (u (511 - u) >> 8) gmax >> 8;
     no halation when no cell has g >= 16 or 3 x (cells with g >= 16) > cells (daylight stays fast);
  C  per row with glow in either neighbouring cell row: g per pixel pair, bilinear between cell centres; w = 255 - Y:
     Y += dY w g >> 16 (each pixel), Cb += dCb w0 g >> 16, Cr += dCr w0 g >> 16 (chroma clamped to 0..255).
"""
import numpy as np

THR = 224
GMAX = (112, 176, 240)                           # stages Low / Med / High
TINTS = {1: (48, -24, 72), 2: (56, -48, 48), 3: (56, -36, 30), 4: (48, 48, -20)}   # red, amber, warm, cool (dY, dCb, dCr)


def model(pic, w, h, pitch, stage, tint):
    """pic: bytes of h rows of `pitch` bytes. Returns (new bytes, count of cells with g >= 16)."""
    gmax = GMAX[stage - 1]
    a = np.frombuffer(pic, dtype=np.uint8).copy().reshape(h, pitch).astype(np.int64)
    gw, gh = (w + 63) >> 6, (h + 63) >> 6
    g = np.zeros((gh, gw), dtype=np.int64)
    for y in range(2, h, 4):
        for x in range(0, w, 2):
            e = a[y, 2 * x] - THR
            if e > 0:
                g[y >> 6, x >> 6] = min(g[y >> 6, x >> 6] + (e >> 2), 248)

    def box(v):
        for _ in range(2):
            t = np.concatenate([[0], v, [0]])
            v = (t[:-2] + 2 * t[1:-1] + t[2:] + 2) >> 2
        return v
    for r in range(gh):
        g[r] = box(g[r])
    for c in range(gw):
        g[:, c] = box(g[:, c])
    u = np.minimum(255, (21 * g) >> 3)
    g = (((u * (511 - u)) >> 8) * gmax) >> 8
    cnt = int((g >= 16).sum())
    if cnt == 0 or 3 * cnt > gw * gh:
        return pic, cnt
    dy, d0, d1 = TINTS[tint]
    for y in range(h):
        fy = y - 32
        g0, t = (fy >> 6, fy & 63) if fy >= 0 else (0, 0)
        g1 = min(g0 + 1, gh - 1)
        if not (g[g0].any() or g[g1].any()):
            continue

        def li(c):
            c = min(max(c, 0), gw - 1)
            return (64 * g[g0, c] + (g[g1, c] - g[g0, c]) * t) >> 6
        gp = []
        for k in range(gw + 1):
            aa, bb = li(k - 1), li(k)
            v, step, n = 64 * aa, 2 * (bb - aa), 32
            if k == 0:
                v += 16 * step
                n = 16
            if k == gw:
                n = 16
            for _ in range(n):
                gp.append((v >> 6) & 0xFF)
                v += step
        row = a[y]
        for p in range(w // 2):
            gg = gp[p]
            if not gg:
                continue
            y0, c0, y1, c1 = row[4 * p:4 * p + 4]
            t0 = (255 - y0) * gg
            row[4 * p] = y0 + ((dy * t0) >> 16)
            row[4 * p + 2] = y1 + ((dy * ((255 - y1) * gg)) >> 16)
            row[4 * p + 1] = min(255, max(0, c0 + ((d0 * t0) >> 16)))
            row[4 * p + 3] = min(255, max(0, c1 + ((d1 * t0) >> 16)))
    return a.astype(np.uint8).tobytes(), cnt


def scene(w, h, pitch, lights, seed=3, base=40, wall=None):
    """Dark noisy frame with random chroma and clipped discs at lights [(x, y, r)]; wall = fraction of clipped rows."""
    rng = np.random.default_rng(seed)
    a = rng.integers(0, 256, size=(h, pitch), dtype=np.int64)
    yy, xx = np.mgrid[0:h, 0:w]
    Y = base + rng.integers(-20, 20, size=(h, w))
    for x0, y0, r in lights:
        Y = np.where((xx - x0) ** 2 + (yy - y0) ** 2 <= r * r, 255, Y)
    if wall:
        Y[: int(h * wall)] = 250
    a[:, 0:2 * w:2] = np.clip(Y, 0, 255)
    a[:, 1:2 * w:4] = rng.integers(100, 156, size=(h, w // 2))
    a[:, 3:2 * w:4] = rng.integers(100, 156, size=(h, w // 2))
    return a.astype(np.uint8).tobytes()
