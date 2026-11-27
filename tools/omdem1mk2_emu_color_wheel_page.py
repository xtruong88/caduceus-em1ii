#!/usr/bin/env python3
"""Drive the Color Creator Wheel page (EM1_CC_WHEEL=1) through key sequences in the emulator.

    python3 tools/omdem1mk2_emu_color_wheel_page.py WHEEL_SPEC [BASE_SPEC]

WHEEL_SPEC: a spec with the wheel build (color_creator_wheel/edits_halo_lookmem_wheel.json + color_wheel/edits.json on
the release it replaces); BASE_SPEC (default releases/em1mk2/v0.4c26t/edits.json): the same release without the wheel
page, for the before/after comparison of Chroma / Luminance / Strength / Halo.

Pages: Film 0, Wheel 1, Chroma 2, Luminance 3, Strength 4, Halo 5. On the Wheel page Down and TRASH step the axis
S -> H -> L -> S (draw only); Up, Left, Right and the dials do nothing.

The editor handlers run as in the image (cc_init, cc_info, cc_page, the arrows, cc_guide, scp_cc_label, the .cwui
code). Fixtures (tools/emu_fixtures/em1_cc_wheel_fw_stubs.s, on top of omdem1mk2_emu_color_creator's): the fwOpe API
object 0x6082602c with logging slots +28 start / +32 stop / +48 draw, and the stock record handlers +36 0x60e8cc69 and
+40 0x60e8ce8c (logged, then return). The GUI flag 0x61fbfbcc is mapped (0, then 1 to check d1 = 2). A dial detent is
modelled as the stock dial loop delivers it: cc_up / cc_down / cc_left / cc_right with P_DIAL = 1 (set by
cc_dial1 / cc_dial2 around the loop, which calls the parent's +44..+56 handlers once per detent).

Checked on every sequence: a C3d surface model starting with type 0 open (the GUI opens it for the editor):
stop needs an open surface and closes it, start needs none open (phase 01: start on an open surface hangs the C3d
API task), draw needs one open; P_WON returns to 0 and type 0 is open again whenever the editor leaves the Wheel page.
"""
import struct
import sys

import omdem1mk2_emu_color_creator as CC
import omdem1mk2_emu_sdload as SD
import omdem1mk2_emu_validator as V
from penf_emulator import Region, execute

FW, FWLOG, GUI = 0x9F180000, 0x9F190000, 0x61FBF000
INFO, PAGE, OK = 0x61259C6C, 0x61259C64, 0x61259C68
LEFT, RIGHT = 0x61259C54, 0x61259C58
EV_INFO, EV_TRASH, EV_MENU, EV_OK = 0x9014, 0x9016, 0x900E, 0x9015
P_PAGE, P_CHR, P_DIAL, P_STR, P_WON, P_WAXIS, P_WCUR = 18, 25, 26, 80, 84, 85, 86
SLOT = {28: 'start', 32: 'stop', 48: 'draw', 0x36: 'stock+36', 0x40: 'stock+40', 0x5C: 'child_sync', 0x0C: 'child'}
NAMES = ['Film', 'Wheel', 'Chroma', 'Luminance', 'Strength', 'Halo']
ENTER, LEAVE, DRAW = [(32, 0), (28, 4), (48, 5)], [(32, 4), (28, 0), (48, 5)], [(48, 5)]


class WheelEditor(CC.Editor):
    def __init__(self, image, fixtures, fw, disp2=0):
        super().__init__(image, fixtures)
        self.fw_code, syms = fw
        main = bytearray(self.image)
        for address, name in ((0x6082602C, 'fw_iface'), (0x60E8CC69, 'stock_page'), (0x60E8CE8C, 'stock_ok'),
                              (0x60E4A59C, 'child_sync')):
            main[address - V.B:address - V.B + 5] = b'\xdc' + struct.pack('<i', syms[name] - address)
        for address, name in ((0x60E8B9BD, 'ui_noop'), (0x60E543D6, 'ui_noop'), (0x60EE8CD1, 'ui_scp_format'),
                              (0x60DB275E, 'ui_scp_text'), (0x6005E6CF, 'ui_get_mode'), (0x608362C5, 'ui_facade')):
            main[address - V.B:address - V.B + 5] = b'\xdc' + struct.pack('<i', self.ui_syms[name] - address)
        self.regions = V.main_regions(bytes(main))
        gui = bytearray(0x1000)
        struct.pack_into('<I', gui, 0xBCC, disp2)
        self.gui = bytes(gui)
        self.calls = []
        self.child_obj = syms['child_obj']
        self.children = False            # parent +124 / +128 hold logging child widgets
        self.last = []

    def run_ui(self, entry, stop, arg, d0=0):
        handle = bytearray(0x1000)
        struct.pack_into('<H', handle, 0x4AE, SD.HANDLE)
        widget = bytearray(0x100)
        struct.pack_into('<I', widget, 132, CC.WIDGET)
        if self.children:
            struct.pack_into('<II', widget, 124, self.child_obj, self.child_obj)
        log = bytearray(0x1000)
        struct.pack_into('<I', log, 0, FWLOG + 16)
        regions = (*self.regions, Region('ui', CC.UI, self.ui_code, 'rx'),
                   Region('model', CC.MODEL, self.model, 'rw', True),
                   Region('widget', CC.WIDGET, bytes(widget), 'rw', True),
                   Region('p', SD.P, self.state, 'rw', True),
                   Region('p_handle', SD.P_RAM, bytes(handle), 'r'),
                   Region('heap', SD.HEAP, self.heap, 'r'),
                   Region('stk', SD.STK, bytes(0x2000), 'rw'),
                   Region('fw', FW, self.fw_code, 'rx'), Region('fwlog', FWLOG, bytes(log), 'rw', True),
                   Region('gui', GUI, self.gui, 'r'))
        regs = {'pc': entry, 'sp': SD.STK + 0x1000, 'a0': CC.WIDGET, 'a1': arg, 'd0': d0}
        result = execute(regions, regs, stop, limit=60_000)
        assert result['status'] == 'returned' and result['registers']['sp'] == regs['sp'], (
            result['status'], hex(result['registers']['pc']), result['fault'])
        memory = {r['name']: bytes.fromhex(r['hex']) for r in result['memory']}
        self.state, self.model = memory['p'], memory['model']
        out = memory['fwlog']
        end = struct.unpack_from('<I', out, 0)[0] - FWLOG
        self.last = [struct.unpack_from('<3I', out, o) for o in range(16, end, 12)]
        self.calls += self.last
        self.ret = result['registers']['d0']
        return memory['widget'][48:114].decode('utf-16le').split('\0', 1)[0]

    def key(self, pointer, d0=0):
        """Run a record handler; returns its fwOpe calls as (slot, d0)."""
        target, = struct.unpack_from('<I', self.image, pointer - V.B)
        self.run_ui(CC.UI, self.ui_syms['ui_return'], target, d0)
        self.kret = self.ret
        return [(s, a) for s, a, _ in self.last]

    def guide(self):
        target, = struct.unpack_from('<I', self.image, CC.GUIDE - V.B)
        return self.run_ui(CC.UI, self.ui_syms['ui_return'], target)

    def p(self, off, signed=False):
        v = self.state[off]
        return v - 256 if signed and v > 127 else v

    def set_p(self, off, value):
        s = bytearray(self.state)
        s[off] = value
        self.state = bytes(s)

    def page(self):
        return struct.unpack_from('<H', self.state, P_PAGE)[0]


class Surface:
    """C3d surface model for the stop-before-start rule."""
    def __init__(self):
        self.open = 0                            # the GUI has type 0 (Color Creator ring) open

    def feed(self, calls):
        for slot, d0 in calls:
            if slot == 32:
                assert self.open is not None, 'stop with nothing open'
                assert self.open == d0, f'stop type {d0} while type {self.open} is open'
                self.open = None
            elif slot == 28:
                assert self.open is None, f'start type {d0} while type {self.open} is open (C3d API hangs)'
                self.open = d0
            elif slot == 48:
                assert self.open is not None and d0 == 5, 'draw without an open surface'
        return calls


def fmt(calls):
    return ' '.join(f'{SLOT[s]}({d0})' if s in (28, 32, 48) else SLOT[s] for s, d0 in calls) or '-'


def main(wheel_spec, base_spec=str(SD.ROOT / 'releases/em1mk2/v0.4c26t/edits.json')):
    fixtures = (*SD.stubs(), *SD.assemble_fixture(SD.ROOT / 'tools/emu_fixtures/em1_color_creator_stubs.s', CC.UI,
                                                  MODEL=CC.MODEL))
    fw = SD.assemble_fixture(SD.ROOT / 'tools/emu_fixtures/em1_cc_wheel_fw_stubs.s', FW, FWLOG=FWLOG)
    wheel_img, base_img = V.image(wheel_spec), V.image(base_spec)

    def fresh(img, disp2=0):
        ed = WheelEditor(img, fixtures, fw, disp2)
        assert not ed.key(CC.CREATE) and ed.page() == 0 and ed.p(P_WON) == 0
        return ed, Surface()

    def on_wheel(disp2=0):
        ed, surf = fresh(wheel_img, disp2)
        assert surf.feed(ed.key(INFO, EV_INFO)) == ENTER
        return ed, surf

    for event, label in ((EV_INFO, 'INFO'),):
        ed, surf = fresh(wheel_img)
        print(f'{label} x6:')
        steps = []
        for _ in range(6):
            calls = surf.feed(ed.key(INFO if event == EV_INFO else PAGE, event))
            pg = ed.page()
            guide, scp = ed.guide(), ed.scp()
            print(f'   -> page {pg} {NAMES[pg]:9s} P_WON {ed.p(P_WON)} axis {ed.p(P_WAXIS)} cur {ed.p(P_WCUR)}  '
                  f'fwOpe: {fmt(calls):26s} guide {guide!r}  scp {scp!r}')
            steps.append((pg, calls))
            assert ed.p(P_WON) == (pg == 1)
            if pg == 1:
                assert ed.p(P_WAXIS) == 0 and ed.p(P_WCUR) == 255
                assert guide == 'Wheel S Provia' and scp == 'Color Wheel', (guide, scp)
        assert steps == [(1, ENTER), (2, LEAVE), (3, []), (4, []), (5, []), (0, [])], steps
        assert surf.open == 0 and all(d1 == 1 for _, _, d1 in ed.calls)

    for label, ptr, ev in (('Down', CC.DOWN, 0), ('TRASH', PAGE, EV_TRASH)):
        print(f'{label} on the Wheel page x4:')
        ed, surf = on_wheel()
        for want in (1, 2, 0, 1):
            calls = surf.feed(ed.key(ptr, ev))
            guide = ed.guide()
            print(f'   axis {ed.p(P_WAXIS)} P_WON {ed.p(P_WON)} fwOpe {fmt(calls):8s} guide {guide!r} scp {ed.scp()!r}')
            assert calls == DRAW and ed.kret == 1 and ed.page() == 1 and ed.p(P_WON) == 1 and ed.p(P_WCUR) == 255
            assert ed.p(P_WAXIS) == want and guide == f'Wheel {"SHL"[want]} Provia', guide
        assert surf.feed(ed.key(INFO, EV_INFO)) == LEAVE and surf.open == 0 and ed.p(P_WON) == 0
        print('   then INFO leaves: stop(4) start(0) draw(5); re-entering starts on S again')
        for _ in range(4):
            surf.feed(ed.key(INFO, EV_INFO))
        assert surf.feed(ed.key(INFO, EV_INFO)) == ENTER and ed.p(P_WAXIS) == 0 and ed.guide() == 'Wheel S Provia'

    print('TRASH on the other pages steps the page as before:')
    ed, surf = fresh(wheel_img)
    assert surf.feed(ed.key(PAGE, EV_TRASH)) == ENTER and ed.page() == 1        # Film -> Wheel
    assert surf.feed(ed.key(INFO, EV_INFO)) == LEAVE and ed.page() == 2         # INFO leaves to Chroma
    for want in (3, 4, 5, 0, 1):
        calls = surf.feed(ed.key(PAGE, EV_TRASH))
        assert ed.page() == want and calls == (ENTER if want == 1 else []), (want, calls)
    print('   Film -TRASH-> Wheel (enter), INFO -> Chroma (leave), TRASH: Luminance, Strength, Halo, Film, Wheel')

    print('Keys that do nothing on the Wheel page:')
    ed, surf = on_wheel()
    surf.feed(ed.key(CC.DOWN))                                        # axis H, so a stray step would show
    before = (bytes(ed.model), bytes(ed.state))
    for name, ptr, dial in (('Up', CC.UP, 0), ('Left', LEFT, 0), ('Right', RIGHT, 0), ('rear dial +', CC.UP, 1),
                            ('rear dial -', CC.DOWN, 1), ('front dial +', LEFT, 1), ('front dial -', RIGHT, 1)):
        ed.set_p(P_DIAL, dial)
        ref = (bytes(ed.model), bytes(ed.state))
        calls = ed.key(ptr)
        assert not calls and ed.kret == 1 and (bytes(ed.model), bytes(ed.state)) == ref, name
        ed.set_p(P_DIAL, 0)
        print(f'   {name:13s}: no fwOpe call, no setting or P change, returns 1')
    assert (bytes(ed.model), bytes(ed.state)) == before and ed.p(P_WAXIS) == 1

    print('Exits from the Wheel page (axis S, H, L):')
    for axis in (0, 1, 2):
        for how in ('OK', 'MENU', 'cc_init'):
            ed, surf = on_wheel()
            for _ in range(axis):
                surf.feed(ed.key(CC.DOWN))
            if how == 'OK':
                calls = surf.feed(ed.key(OK, EV_OK))
                want = LEAVE + [(0x40, EV_OK)]
            elif how == 'MENU':
                calls = surf.feed(ed.key(PAGE, EV_MENU))
                want = LEAVE + [(0x36, EV_MENU)]
            else:
                calls = ed.key(CC.CREATE)        # P_WON cleared only; the GUI starts type 0 for the editor itself
                want = []
            print(f'   {"SHL"[axis]} {how:8s}: fwOpe {fmt(calls):40s} page {ed.page()} P_WON {ed.p(P_WON)}')
            assert calls == want and ed.p(P_WON) == 0 and ed.page() == 0
            if how != 'cc_init':
                assert surf.open == 0
    for how, ptr, ev in (('OK', OK, EV_OK), ('MENU', PAGE, EV_MENU)):
        ed, _ = fresh(wheel_img)
        assert ed.key(ptr, ev) == [(0x40 if how == 'OK' else 0x36, ev)]
    print('   on Film: OK / MENU go straight to the stock handler (no fwOpe call)')

    print('Other record+36 events from the Wheel page (children present): leave, refresh the view, then stock:')
    refresh = [(0x5C, None), (0x0C, 0x900C)] * 2
    for ev in (0x972B, 0x903E, 0x900D, EV_MENU, 0x1234):
        ed, surf = on_wheel()
        surf.feed(ed.key(CC.DOWN))
        ed.children = True
        calls = surf.feed(ed.key(PAGE, ev))
        guide = ed.guide()
        shape = [(s, None if s == 0x5C else a) for s, a in calls]
        print(f'   event {ev:#06x}: fwOpe {fmt(calls):58s} page {ed.page()} P_WON {ed.p(P_WON)} guide {guide!r}')
        assert shape == LEAVE + refresh + [(0x36, ev)], shape
        assert ed.p(P_WON) == 0 and ed.page() == 0 and surf.open == 0 and guide == 'Provia C0.0', guide
    ed, surf = on_wheel()
    ed.children = True
    assert surf.feed(ed.key(OK, EV_OK)) == LEAVE + [(0x40, EV_OK)]
    print('   OK with children present: no refresh before the stock commit')

    ed, surf = on_wheel(disp2=1)
    surf.feed(ed.key(CC.DOWN))
    assert [d1 for _, _, d1 in ed.calls] == [2, 2, 2, 2]
    print('GUI flag 0x61fbfbcc set: every fwOpe call passes d1 = 2')

    print('Chroma / Luminance / Strength / Halo at the new page numbers vs the base build:')
    for name, wheel_pg, base_pg, keyptr in (('Chroma', 2, 1, LEFT), ('Luminance', 3, 2, CC.UP),
                                            ('Strength', 4, 3, RIGHT), ('Halo', 5, 4, RIGHT)):
        result = []
        for img, pg in ((wheel_img, wheel_pg), (base_img, base_pg)):
            ed, _ = fresh(img)
            for _ in range(pg):
                ed.key(INFO, EV_INFO)
            assert ed.page() == pg
            g0 = ed.guide()
            calls = ed.key(keyptr)
            g1 = ed.guide()
            result.append((g0, g1, ed.p(P_CHR, True), ed.p(P_STR), ed.rendered_settings(),
                           struct.unpack_from('<i', ed.model, 16 + 4 * 961)[0], ed.scp(), calls))
        print(f'   {name:9s} wheel page {wheel_pg}: {result[0][0]!r} -> {result[0][1]!r}   base page {base_pg}: '
              f'{result[1][0]!r} -> {result[1][1]!r}')
        assert result[0] == result[1], (result[0], result[1])
    print('RESULT PASS')


if __name__ == '__main__':
    main(*sys.argv[1:])
