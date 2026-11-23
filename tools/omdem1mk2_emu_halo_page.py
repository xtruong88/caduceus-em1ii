#!/usr/bin/env python3
"""Run the Color Creator Halo page (color_creator_wheel built with EM1_CC_HALO=1) in the MN103 emulator.

    python3 tools/omdem1mk2_emu_halo_page.py [SPEC]

SPEC: a release edits.json that holds the Halo page (default: built here as below).

The release spec is v0.4c17 with the wheel edits replaced by patches/omdem1mk2/color_creator_wheel/edits_halo.json and the
halation edits added (they make Section 6 load the 100 KB gap where the page code lives at 0x612f0000). The editor runs
from its controller record as in tools/omdem1mk2_emu_color_creator.py: display, widget init, settings facade (a memory
model) and card driver are fixtures. Checks:
  - INFO steps the pages 0..4 and wraps to 0; page 4's guide reads "Halo Off" / "Low" / "Med" / "High" from sid 961;
  - RIGHT / LEFT on page 4 step sid 961 through the facade, clamped to 0..3; a stored value outside 0..3 shows and
    steps as Off;
  - page 3 still steps Strength, and the built-in look on page 0 is unchanged.
"""
import json
import struct
import sys
import tempfile

import omdem1mk2_emu_color_creator as CC
import omdem1mk2_emu_halation_route as HR
import omdem1mk2_emu_sdload as SD
import omdem1mk2_emu_validator as V

LEFT, RIGHT, INFO = 0x61259C54, 0x61259C58, 0x61259C6C
SID_HALO = 961
WHEEL_HALO = V.ROOT / 'patches/omdem1mk2/color_creator_wheel/edits_halo.json'


def spec_path():
    base = json.load(open(HR.BASE_SPEC))
    halo = json.load(open(WHEEL_HALO))['edits']
    by_addr = {e['addr']: e for e in halo}
    edits = [by_addr.pop(e['addr'], e) for e in base['edits']]
    assert list(by_addr) == ['0x612f0000'], list(by_addr)     # only the page section is new
    hl, _, _ = HR.load_build().make_edits(0, 0)
    base['edits'] = hl['edits'] + edits + list(by_addr.values())
    f = tempfile.NamedTemporaryFile('w', suffix='.json', delete=False)
    json.dump(base, f)
    f.close()
    return f.name


class Editor(CC.Editor):
    def __init__(self, image, fixtures):
        super().__init__(image, fixtures)
        self.model = self.model.ljust(16 + 4 * 1024, b'\0')      # room for sid 961 in the facade model

    def halo(self):
        return struct.unpack_from('<i', self.model, 16 + 4 * SID_HALO)[0]

    def set_halo(self, v):
        m = bytearray(self.model)
        struct.pack_into('<i', m, 16 + 4 * SID_HALO, v)
        self.model = bytes(m)

    def page(self):
        return struct.unpack_from('<H', self.state, 18)[0]


def main():
    fixtures = (*SD.stubs(), *SD.assemble_fixture(SD.ROOT / 'tools/emu_fixtures/em1_color_creator_stubs.s', CC.UI,
                                                   MODEL=CC.MODEL))
    ed = Editor(V.image(sys.argv[1] if len(sys.argv) > 1 else spec_path()), fixtures)
    ed.call(CC.CREATE)
    look = ed.call(CC.GUIDE)
    assert look.startswith('Provia'), look
    for _ in range(4):
        ed.call(INFO)
    assert ed.page() == 4 and ed.call(CC.GUIDE) == 'Halo Off', (ed.page(), ed.call(CC.GUIDE))
    names = ['Off', 'Low', 'Med', 'High']
    for want in (1, 2, 3, 3):
        ed.call(RIGHT)
        assert ed.halo() == want and ed.call(CC.GUIDE) == f'Halo {names[want]}', (ed.halo(), ed.call(CC.GUIDE))
    for want in (2, 1, 0, 0):
        ed.call(LEFT)
        assert ed.halo() == want and ed.call(CC.GUIDE) == f'Halo {names[want]}', (ed.halo(), ed.call(CC.GUIDE))
    print('page 4: guide "Halo Off/Low/Med/High" from sid 961; RIGHT / LEFT step it through the facade, clamped 0..3')
    ed.set_halo(7)
    assert ed.call(CC.GUIDE) == 'Halo Off'
    ed.call(RIGHT)
    assert ed.halo() == 1
    print('a stored 7 shows as Off and RIGHT goes to Low')
    ed.call(INFO)
    assert ed.page() == 0 and ed.call(CC.GUIDE).startswith('Provia')
    for _ in range(3):
        ed.call(INFO)
    strength = ed.state[80]
    ed.call(RIGHT)
    assert ed.page() == 3 and ed.state[80] != strength and ed.halo() == 1
    print('INFO wraps from page 4 to 0 (look guide unchanged); page 3 still steps Strength, sid 961 untouched')
    print('RESULT PASS')


if __name__ == '__main__':
    main()
