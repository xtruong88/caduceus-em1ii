#!/usr/bin/env python3
"""Check E-M1 Mark II look memory (sd_loader and color_creator_wheel built with EM1_LOOKMEM=1) in the MN103 emulator.

    python3 tools/omdem1mk2_emu_look_memory.py releases/em1mk2/<version>/edits.json [--reference <v0.4c24 edits.json>]

The editor stores the look chosen with the arrows in sid 965 (property 0xF719 index 1) as v = 1 + look + 32 * card.
After power-on, the first half-press (sd_loader lm_gate, after the LOOKS.BIN attempt) or the first editor entry
(color_creator_wheel lm_ensure) rebuilds the shared block P from v, in RAM only.

1. Setting (the camera's own property code, tools/omdem1mk2_emu_spare_setting.py fixtures): the facade stores and reads
   back 0..64 in sid 965; the raw getter 0x6005e6cf(0xF719, 1) the restore uses returns the same value; 1, 33 and 64
   survive all three per-boot reset paths; neighbouring sids 961 / 964 / 966 are untouched.
2. Half-press restore (tools/omdem1mk2_emu_sdload.py fixtures; file, heap and getter are stand-ins): built-in, card,
   mono, card not loaded yet (waits), card missing (dropped after the last attempt), index past the pack, 0 and
   out-of-range values (ignored), and a restore that already ran (not repeated). A colour look's P (S, hue, light,
   flags) equals what the editor computes when the same look is chosen with the arrows, and P_CCMODE = 9 (Color
   Creator). The facade fixture counts SetValue calls: a restored colour look makes exactly one (lm_refresh rewrites
   618 with its own value, which makes live view re-run the colour stage) and leaves every stored setting unchanged;
   mono, skipped and invalid cases make none.
3. Editor (tools/omdem1mk2_emu_color_creator.py fixtures): an arrow step stores v in sid 965; opening the editor after
   power-on keeps the remembered built-in look; opening it before the first half-press keeps a remembered card
   look stored (the automatic look 0 is not saved) and the half-press then restores it.
4. Without look memory (stock, and --reference, e.g. v0.4c24): a valid sid 965 changes nothing on a half-press.
Not emulated: the flash write of the settings block at power-off, and a live-view refresh after the restore.
"""
import argparse
import struct

import omdem1mk2_emu_color_creator as CC
import omdem1mk2_emu_sdload as SD
import omdem1mk2_emu_spare_setting as SS
import omdem1mk2_emu_validator as V
import ep7_looks_bin as looks
from penf_emulator import Region

SID, KEY, IDX = 965, 0xF719, 1
BUILTIN_ADDR = 0x60BC8150
P_SD_STATE, P_LOOK, P_INIT, P_ACTIVE, P_HLON, P_CCMODE, P_SAT, P_LMEM = 6, 16, 20, 30, 31, 32, 44, 83
CC_RAW = 9
FACADE = 0x608362C5


def p16(p, off):
    return struct.unpack_from('<H', p, off)[0]


def set_calls(model):
    """SetValue calls counted by the ui_set_log fixture (MODEL+8)."""
    return struct.unpack_from('<I', model, 8)[0]


def colour_state(p):
    """What the colour stage reads: S/hue/light (36 B), the H/L flag."""
    return bytes(p[P_SAT:P_SAT + 36]), p[P_HLON]


def check_setting(spec):
    emu = SS.Emu(spec)
    for v in range(65):
        assert emu.set_value(SID, v) == 0 and emu.get_value(SID) == (0, v), v
        raw = emu.call(0x6005E6CF, 0xC0, 12, {'d0': KEY, 'd1': IDX, 'a0': 0})['d0']
        assert raw == v, (v, raw)
    print(f'sid {SID}: facade stores and reads back 0..64; raw getter({KEY:#x}, {IDX}) returns the same value')
    for v in (1, 33, 64):
        for name, entry, flag, control_reset in SS.BOOT_PATHS:
            emu.store_value(SID, v)
            emu.store_value(SS.CONTROL_SID, 2)
            emu.write(SS.SID_10052_RAM, struct.pack('<I', flag))
            emu.call(entry, 0x80, 8, {})
            emu.write(SS.SID_10052_RAM, bytes(4))
            assert emu.get_value(SID)[1] == v, (name, v)
            assert emu.get_value(SS.CONTROL_SID)[1] == (0 if control_reset else 2), name
    assert [emu.get_value(s) for s in (961, 964, 966)] == [(0, 0)] * 3
    print(f'sid {SID}: 1, 33 and 64 survive the three boot reset paths (control sid reset as listed); 961/964/966 untouched')


class Editor(CC.Editor):
    """CC.Editor with the look memory getter (sid 965 = the model's word) and a facade on the half-press image."""

    def __init__(self, image, fixtures, remembered=0):
        super().__init__(image, fixtures)
        m = bytearray(self.model.ljust(0x1000, b'\0'))
        struct.pack_into('<I', m, 4, self.ui_syms['ui_set_log'])          # facade vtable[0]: counting SetValue
        self.model = bytes(m)
        self.set_sid(remembered)
        patched = bytearray(self.image)
        for address, name in ((0x60E8B9BD, 'ui_noop'), (0x60E543D6, 'ui_noop'), (0x60EE8CD1, 'ui_scp_format'),
                              (0x60DB275E, 'ui_scp_text'), (0x6005E6CF, 'ui_get_lookmem'), (FACADE, 'ui_facade')):
            off = address - V.B
            patched[off:off + 5] = b'\xdc' + struct.pack('<i', self.ui_syms[name] - address)
        self.regions = V.main_regions(bytes(patched))
        # Half-press image: file / heap / getter stand-ins (getter = ctl+24) and the counting facade fixture.
        hp = bytearray(self.image)
        off = FACADE - V.B
        hp[off:off + 5] = b'\xdc' + struct.pack('<i', self.ui_syms['ui_facade'] - FACADE)
        self.hp_image = bytes(hp)

    def sid(self):
        return struct.unpack_from('<i', self.model, 16 + 4 * SID)[0]

    def set_value(self, sid, v):
        m = bytearray(self.model)
        struct.pack_into('<i', m, 16 + 4 * sid, v)
        self.model = bytes(m)

    def set_sid(self, v):
        self.set_value(SID, v)

    def half_press(self, pack, ready_from=1):
        res, self.state, self.heap, self.model = presses(self, pack, self.sid(), 1, ready_from, self.state)
        assert len(res) == 1, res
        return res[0][0]


def presses(ed, pack, v, events, ready_from=1, state=None):
    """`events` half-presses from P = `state` (None: a fresh P, i.e. power-on) with sid 965 = v.
    Returns the per-press results, the final P, the heap (one run keeps the card buffer across presses) and the
    settings model after the presses."""
    extra = (Region('ui', CC.UI, ed.ui_code, 'rx'), Region('model', CC.MODEL, ed.model, 'rw', True))
    got = {}
    res, st, heap = SD.run_presses(ed.hp_image, ed.fs_code, ready_from, pack, 0, events=[SD.HALF] * events,
                                   state=state, lookmem=v, extra=extra, captured=got)
    assert all(isinstance(r[0], int) for r in res), res
    return res, st, heap, got.get('model', ed.model)


def refreshed_once(before, after):
    """One SetValue, and every stored setting word unchanged (618 rewritten with its own value)."""
    return set_calls(after) == set_calls(before) + 1 and after[16:] == before[16:]


def untouched(before, after):
    return after == before


def builtin_records(image):
    recs = [image[BUILTIN_ADDR - V.B + 64 * i:BUILTIN_ADDR - V.B + 64 * (i + 1)] for i in range(16)]
    return recs, [r[48:64].split(b'\0', 1)[0].decode() for r in recs]


def chosen_state(spec, fixtures, pack, index, card):
    """P after choosing look `index` with the arrows (UP) in a fresh editor (card loaded first when `card`)."""
    ed = Editor(V.image(spec), fixtures)
    if card:
        assert ed.half_press(pack) == 1
    ed.call(CC.CREATE)
    for _ in range(index):
        ed.call(CC.UP)
    assert p16(ed.state, P_LOOK) == index and p16(ed.state, P_INIT) == (2 if card else 1)
    return ed


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('spec')
    ap.add_argument('--reference', help='a release without look memory (e.g. v0.4c24): a valid sid 965 must do nothing')
    a = ap.parse_args()

    check_setting(a.spec)

    fixtures = (*SD.stubs(), *SD.assemble_fixture(SD.ROOT / 'tools/emu_fixtures/em1_color_creator_stubs.s', CC.UI,
                                                   MODEL=CC.MODEL))
    source = (SD.ROOT / 'releases/v0.31c/card/EP7MOD/LOOKS.BIN').read_bytes()
    pack = looks.make_file([looks.rec(source, index) for index in (0, 7)])   # Velvia, Bleach Byp.
    img = V.image(a.spec)
    recs, names = builtin_records(img)
    mono = [i for i, r in enumerate(recs) if r[45] == 1]
    colour = [i for i, r in enumerate(recs) if r[45] != 1 and i]
    assert mono and colour, (names, mono)
    k, m = colour[2], mono[0]

    # 2. half-press restore (stored vividness 618 = 2, so a refresh must write 2 back, not 0)
    want = chosen_state(a.spec, fixtures, pack, k, False)
    ed = Editor(img, fixtures)
    ed.set_value(618, 2)
    m0 = ed.model
    res, p, _, mod = presses(ed, pack, 1 + k, 1)
    assert p[P_LMEM] == 1 and p16(p, P_INIT) == 1 and p16(p, P_LOOK) == k and p[P_ACTIVE] == 1
    assert struct.unpack_from('<I', p, P_CCMODE)[0] == CC_RAW and colour_state(p) == colour_state(want.state)
    assert refreshed_once(m0, mod)
    print(f'built-in {names[k]!r} (v={1 + k}): restored on the first half-press, P = the editor\'s own result, '
          'CCMODE 9; one SetValue rewrites 618 = 2, no stored setting changes')

    want_card = chosen_state(a.spec, fixtures, pack, 1, True)
    res, p, _, mod = presses(ed, pack, 1 + 1 + 32, 1)
    assert res[0][0] == 1 and p[P_LMEM] == 1 and p16(p, P_INIT) == 2 and p16(p, P_LOOK) == 1 and p[P_ACTIVE] == 1
    assert colour_state(p) == colour_state(want_card.state) and refreshed_once(m0, mod)
    print('card look 1 (v=34): restored on the half-press that loads LOOKS.BIN, P = the editor\'s result, one refresh')

    res, p, _, mod = presses(ed, pack, 34, 3, ready_from=4)      # fopen succeeds on press 2 (slot D:)
    assert [r[0] for r in res] == [0, 1, 1] and p16(p, P_INIT) == 2 and p16(p, P_LOOK) == 1 and p[P_LMEM] == 1
    assert refreshed_once(m0, mod)                                 # once over three presses
    res1, p1, _, mod = presses(ed, pack, 34, 1, ready_from=4)
    assert p1[P_LMEM] == 0 and p1[P_ACTIVE] == 0 and p16(p1, P_INIT) == 0 and untouched(m0, mod)
    print('card look while the card is not read yet: waits (press 1 untouched), restored when the file loads (press 2)')

    res, p, _, mod = presses(ed, pack, 34, 9, ready_from=0)
    assert res[-1][0] == 0xFFFF and p[P_LMEM] == 1 and p[P_ACTIVE] == 0 and p16(p, P_INIT) == 0 and untouched(m0, mod)
    res, p, _, mod = presses(ed, pack, 1 + 5 + 32, 1)
    assert res[0][0] == 1 and p[P_LMEM] == 1 and p[P_ACTIVE] == 0 and p16(p, P_INIT) == 0 and untouched(m0, mod)
    print('card missing after all attempts, or index past the 2-look pack: dropped, nothing restored, no SetValue')

    res, p, _, mod = presses(ed, pack, 1 + m, 1)
    assert p[P_LMEM] == 1 and p16(p, P_LOOK) == m and p16(p, P_INIT) == 1 and p[P_ACTIVE] == 0 and untouched(m0, mod)
    print(f'mono built-in {names[m]!r}: index restored, colour stage stays off (stored vividness -4 renders it), '
          'no SetValue')

    for v in (0, 65, 127, -1, 0x80000000):
        res, p, _, mod = presses(ed, pack, v, 2)
        assert p[P_LMEM] == 1 and p[P_ACTIVE] == 0 and p16(p, P_INIT) == 0 and p16(p, P_LOOK) == 0, v
        assert untouched(m0, mod), v
    done = bytearray(want.state)
    done[P_LMEM] = 1
    struct.pack_into('<H', done, P_SD_STATE, 0)
    res, p, _, mod = presses(ed, pack, 1 + 1, 1, state=bytes(done))
    assert p16(p, P_LOOK) == k and colour_state(p) == colour_state(want.state) and untouched(m0, mod)
    print('v = 0, 65, 127, -1, 0x80000000: ignored; a restore that already ran is not repeated (no SetValue)')

    # 3. editor
    ed = Editor(img, fixtures)
    ed.call(CC.CREATE)
    assert ed.state[P_LMEM] == 1 and ed.sid() == 0                     # nothing remembered: invalid, done
    ed.call(CC.UP)
    assert ed.sid() == 2 and ed.state[P_LMEM] == 1
    ed.call(CC.DOWN)
    ed.call(CC.DOWN)
    assert ed.sid() == 16
    print('arrow steps store v: built-in 1 -> 2, built-in 15 -> 16')
    ed = Editor(img, fixtures)
    assert ed.half_press(pack) == 1
    ed.call(CC.CREATE)
    ed.call(CC.UP)
    assert ed.sid() == 34
    print('card look 1 chosen with the arrows -> 34')
    ed = Editor(img, fixtures)
    ed.call(CC.CREATE)
    for _ in range(5):
        ed.call(CC.UP)
    assert ed.sid() == 6
    assert ed.half_press(pack) == 1 and p16(ed.state, P_INIT) == 1      # chosen look kept, no restore over it
    ed.call(CC.CREATE)
    assert ed.call(CC.GUIDE).startswith('Velvia') and p16(ed.state, P_INIT) == 2 and ed.sid() == 33
    print('built-in look chosen before the card was read: reopening after the card loads switches to card look 0 '
          'and stores it (33), so the next power-on restores the look on screen')

    ed = Editor(img, fixtures, remembered=1 + k)
    ed.set_value(618, 2)
    m0 = ed.model
    ed.call(CC.CREATE)
    banner = ed.call(CC.GUIDE)
    assert banner.startswith(names[k]) and p16(ed.state, P_LOOK) == k and ed.state[P_ACTIVE] == 1, banner
    assert colour_state(ed.state) == colour_state(want.state) and ed.sid() == 1 + k
    assert refreshed_once(m0, ed.model)
    print(f'editor opened after power-on with v={1 + k}: shows {names[k]!r}, same P, sid unchanged, one 618 refresh')

    ed = Editor(img, fixtures, remembered=34)
    ed.call(CC.CREATE)
    assert ed.call(CC.GUIDE).startswith(names[0]) and ed.state[P_LMEM] == 0 and ed.sid() == 34
    assert ed.half_press(pack) == 1
    assert p16(ed.state, P_INIT) == 2 and p16(ed.state, P_LOOK) == 1 and ed.state[P_LMEM] == 1
    assert ed.call(CC.GUIDE).startswith('Bleach Byp.') and colour_state(ed.state) == colour_state(want_card.state)
    ed.call(CC.CREATE)
    assert ed.call(CC.GUIDE).startswith('Bleach Byp.') and ed.sid() == 34
    print('editor opened before the first half-press with card v=34: built-in look 0 shown and not saved; the '
          'half-press restores Bleach Byp., reopening keeps it')

    # 4. builds without look memory
    for label, spec in (('stock', None), ('reference', a.reference)):
        if label == 'reference' and not spec:
            continue
        ed = Editor(V.image(spec), fixtures)
        res, p, _, mod = presses(ed, pack, 1 + k, 2)
        assert p[P_LMEM] == 0 and p[P_ACTIVE] == 0 and p16(p, P_INIT) == 0 and untouched(ed.model, mod), label
        print(f'{label}: a valid sid 965 changes nothing on a half-press')
    print('RESULT PASS')


if __name__ == '__main__':
    main()
