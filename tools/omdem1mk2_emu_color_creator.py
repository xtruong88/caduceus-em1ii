#!/usr/bin/env python3
"""Run Color Creator's init, banner, SCP label, arrows and SD hook on E-M1 II 3.70.

    python3 tools/omdem1mk2_emu_color_creator.py releases/em1mk2/<version>/edits.json

The display, stock widget initialization, settings facade and card driver are
fixture boundaries. The released look bytes, controller dispatch pointers,
SD state, color/tone preparation and UTF-16 banner writer run as in the image.
"""

import struct
import sys

import ep7_looks_bin as looks
import omdem1mk2_emu_sdload as SD
import omdem1mk2_emu_validator as V
from penf_emulator import Region, execute


UI, MODEL, WIDGET = 0x9F100000, 0x9F110000, 0x9F120000
CREATE, UP, DOWN, GUIDE = 0x61259C44, 0x61259C4C, 0x61259C50, 0x60297FB4
SCP_CALL = 0x60E25EC8
SIDS = (384, 692, 383, 618)


class Editor:
    def __init__(self, image, fixtures):
        self.fs_code, fs_syms, self.ui_code, self.ui_syms = fixtures
        self.image = SD.image_with_stubs(image, fs_syms)
        main = bytearray(self.image)
        for address, name in ((0x60E8B9BD, 'ui_noop'), (0x60E543D6, 'ui_noop'),
                              (0x60EE8CD1, 'ui_scp_format'), (0x60DB275E, 'ui_scp_text'),
                              (0x6005E6CF, 'ui_get_mode'), (0x608362C5, 'ui_facade')):
            off = address - V.B
            main[off:off + 5] = b'\xdc' + struct.pack('<i', self.ui_syms[name] - address)
        self.regions = V.main_regions(bytes(main))
        self.state = struct.pack('<IH', 0x50314D45, SD.HANDLE).ljust(0x200, b'\0')
        self.model = struct.pack('<4I', MODEL + 4, self.ui_syms['ui_set'], 0,
                                 self.ui_syms['ui_get']).ljust(0xC00, b'\0')
        self.heap = bytes(0x4000)

    def half_press(self, pack):
        result, self.state, self.heap = SD.run_presses(self.image, self.fs_code, 1, pack, 1, state=self.state)
        assert len(result) == 1 and isinstance(result[0][0], int), result
        return result[0][0]

    def call(self, pointer):
        target, = struct.unpack_from('<I', self.image, pointer - V.B)
        return self.run_ui(UI, self.ui_syms['ui_return'], target)

    def scp(self):
        return self.run_ui(SCP_CALL, SCP_CALL + 7, WIDGET + 128)

    def run_ui(self, entry, stop, arg):
        handle = bytearray(0x1000)
        struct.pack_into('<H', handle, 0x4AE, SD.HANDLE)
        widget = bytearray(0x100)
        struct.pack_into('<I', widget, 132, WIDGET)
        regions = (*self.regions, Region('ui', UI, self.ui_code, 'rx'),
                   Region('model', MODEL, self.model, 'rw', True),
                   Region('widget', WIDGET, bytes(widget), 'rw', True),
                   Region('p', SD.P, self.state, 'rw', True),
                   Region('p_handle', SD.P_RAM, bytes(handle), 'r'),
                   Region('heap', SD.HEAP, self.heap, 'r'),
                   Region('stk', SD.STK, bytes(0x2000), 'rw'))
        regs = {'pc': entry, 'sp': SD.STK + 0x1000, 'a0': WIDGET, 'a1': arg}
        result = execute(regions, regs, stop, limit=15_000)
        assert result['status'] == 'returned' and result['registers']['sp'] == regs['sp'], (
            result['status'], result['registers'], result['fault'])
        memory = {r['name']: bytes.fromhex(r['hex']) for r in result['memory']}
        self.state, self.model = memory['p'], memory['model']
        return memory['widget'][48:114].decode('utf-16le').split('\0', 1)[0]

    def rendered_settings(self):
        tone_and_vivid = tuple(struct.unpack_from('<i', self.model, 16 + 4 * sid)[0] for sid in SIDS)
        return tone_and_vivid, self.state[44:80]


def main(spec):
    fixture_path = SD.ROOT / 'tools/emu_fixtures/em1_color_creator_stubs.s'
    fixtures = (*SD.stubs(), *SD.assemble_fixture(fixture_path, UI, MODEL=MODEL))
    source = (SD.ROOT / 'releases/v0.31c/card/EP7MOD/LOOKS.BIN').read_bytes()
    pack = looks.make_file([looks.rec(source, index) for index in (0, 7)])
    assert not looks.check_file(pack)

    stock = Editor(V.image(None), fixtures)
    unchanged = stock.rendered_settings()
    assert stock.half_press(pack) == 0
    stock.call(CREATE)
    assert stock.call(GUIDE) == '' and stock.scp() == '' and stock.rendered_settings() == unchanged
    print('Stock: no SD look and no Caduceus settings')

    patched = V.image(spec)
    early = Editor(patched, fixtures)
    assert early.half_press(pack) == 1
    early.call(CREATE)
    assert early.call(GUIDE).startswith('Velvia C1.1')
    assert early.scp() == 'Velvia'
    velvia = early.rendered_settings()
    early.call(UP)
    assert early.call(GUIDE).startswith('Bleach Byp. C1.1')
    bleach = early.rendered_settings()
    assert velvia != bleach
    early.call(CREATE)
    assert early.call(GUIDE).startswith('Bleach Byp. C1.1') and early.rendered_settings() == bleach
    print('Card loaded before opening: both looks apply; reopening preserves the selection')

    # Stepping while the card is the source wraps within the card's own count (2), never into built-in looks 2..15.
    early.call(UP)
    banner = early.call(GUIDE)
    assert banner.startswith('Velvia C1.1') and early.rendered_settings() == velvia, banner
    assert struct.unpack_from('<H', early.state, 16)[0] == 0
    early.call(DOWN)
    banner = early.call(GUIDE)
    assert banner.startswith('Bleach Byp. C1.1') and early.rendered_settings() == bleach, banner
    assert struct.unpack_from('<H', early.state, 16)[0] == 1
    assert early.scp() == 'Bleach Byp.'
    print('Card source: UP from the last card look wraps to look 0, DOWN from look 0 wraps to the last')

    late = Editor(patched, fixtures)
    late.call(CREATE)
    builtin = late.call(GUIDE)
    assert builtin.startswith('Provia C0.0'), builtin
    builtin_settings = late.rendered_settings()
    assert builtin_settings != velvia
    assert late.half_press(pack) == 1
    banner = late.call(GUIDE)
    print(f'Card loaded while open: {builtin!r} -> {banner!r}, '
          f'built-in settings retained = {late.rendered_settings() == builtin_settings}', flush=True)
    assert banner.startswith('Provia C1.1') and late.rendered_settings() == builtin_settings, banner
    assert late.scp() == 'Provia'
    late.call(CREATE)
    banner = late.call(GUIDE)
    assert banner.startswith('Velvia C1.1') and late.rendered_settings() == velvia, banner
    assert late.scp() == 'Velvia'
    print('Reopening selects card look 0 and applies its exact tone and color settings')

    late = Editor(patched, fixtures)
    late.call(CREATE)
    late.call(DOWN)
    selected = late.call(GUIDE).partition(' C')[0]
    assert struct.unpack_from('<H', late.state, 16)[0] == 15
    assert late.half_press(pack) == 1
    assert late.call(GUIDE).startswith(selected + ' C1.1')
    late.call(UP)
    assert late.call(GUIDE).startswith('Provia C1.1') and late.rendered_settings() == builtin_settings
    late.call(DOWN)
    assert late.call(GUIDE).startswith(selected + ' C1.1')
    late.call(CREATE)
    assert late.call(GUIDE).startswith('Velvia C1.1') and late.rendered_settings() == velvia
    print('A built-in selection beyond the two-look card pack switches to card look 0 on reentry')
    print('RESULT PASS')


if __name__ == '__main__':
    main(sys.argv[1])
