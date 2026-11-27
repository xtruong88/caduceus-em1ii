#!/usr/bin/env python3
"""Check the E-M1 Mark II halation stage setting (sid 961) in the MN103 emulator.

    python3 tools/omdem1mk2_emu_spare_setting.py [releases/em1mk2/<VERSION>/edits.json] [--sid 961]

Sid 961 (property key 0xF709, index 0; E-P7 "COLOR1 highlight", which this body never offers) is the spare remembered
setting chosen for the halation stage (plans/reports/research-261120-1400-em1ii-spare-setting.md). This harness runs
the camera's own code to show:
  1. the facade SetValue 0x60837170(sid, 0, v) returns 0 for v = 0..3 and GetValue 0x60836747 reads v back;
  2. the value lives in settings block 90 (RAM 0x624e2000..0x62522000, the block the stock store saves);
  3. none of the three per-boot reset paths changes it, while a control sid (267) is reset exactly where its
     list membership says: normal boot 0x602da762 (26-id list), the same with sid 10052 != 0 (628-id list + bank copy),
     and boot reasons 7/9 0x602da77a (6-id list).
Fixture boundaries: trace/log calls, two camera-state queries (idle), two post-set notifiers, and the lazily created
lock object (a fixture pointer). Not emulated: listeners, real camera-state rejections, the flash write itself.
"""
import argparse
import struct

import omdem1mk2_emu_rules as R
import omdem1mk2_emu_validator as V
from penf_emulator import Region, execute

STUBS = {
    0x607ABB7E: '00df800c', 0x60864039: 'dff014', 0x608647C0: 'df3030', 0x607ABB14: '00df8014',
    0x607A9436: 'dfa00c', 0x607B1CEA: 'df0004', 0x607B1F15: 'dff018', 0x607B4BA9: '9000df8004',
}
SID_TABLE, REGISTRY = 0x604F808C, 0xA2736C50
BLOCK90 = (0x624E2000, 0x62522000)
FACADE_OBJ, OUT, LOCK_SLOT, LOCK_OBJ = 0x627FE000, 0x627FF000, 0x61F9DFC4, 0x627FC000
CONTROL_SID, SID_10052_RAM = 267, 0x6225FF60
BOOT_PATHS = (  # name, entry, sid 10052 value, is the control sid reset?
    ('normal boot (26-id list)', 0x602DA762, 0, True),
    ('boot reason 7/9 (6-id list)', 0x602DA77A, 0, False),
    ('normal boot, sid 10052 != 0 (628-id list + bank copy)', 0x602DA762, 1, True),
)


class Emu(R.Emu):
    def __init__(self, spec):
        R.STUBS = {a: bytes.fromhex(b) for a, b in STUBS.items()}
        super().__init__(spec)
        img = bytearray(self.img)
        off = 0x60258000 + (LOCK_SLOT - 0x61F7D540) - V.B          # .data init image word of the lock pointer
        img[off:off + 4] = struct.pack('<I', LOCK_OBJ)
        self.img = bytes(img)
        self.call(0x6005D707, 0xF0, 48, {'d0': REGISTRY, 'a0': 0x600A29B8, 'a1': 0x624E2008})  # register block 90
        for key, slot in ((0x85D4, 0x6225E400), (0x8B64, 0x6225E404), (0x8B54, 0x6225E408)):
            self.write(slot, struct.pack('<I', self.call(0x6005E6A5, 0x00, 4, {'d0': key})['a0']))
        self.write(FACADE_OBJ, struct.pack('<II', 0, 0x627FD000))

    def call(self, target, mask, frame, regs, extra=()):
        """Run `target` from a synthetic caller. `extra` regions are added; captured ones land in self.captured."""
        if mask is None:   # `calls` target (no register mask)
            code, stop = b'\xfc\xff' + struct.pack('<i', target - V.CALLER) + b'\xcb', V.CALLER + 6
        else:
            code, stop = b'\xdd' + struct.pack('<i', target - V.CALLER) + bytes([mask, frame]) + b'\xcb', V.CALLER + 7
        return self.run(V.CALLER, stop, dict({'sp': V.SP}, **regs), (Region('caller', V.CALLER, code, 'rx'), *extra))

    def run(self, pc, stop, regs, extra=()):
        """Execute from `pc` until `stop` with `regs` (must include sp). Same regions, RAM capture and checks as call()."""
        tcb = bytearray(0x1000)
        struct.pack_into('<I', tcb, 4, R.KERN)
        regions = [Region('stack', V.STACK, bytes(0x1000), 'rw'),
                   *V.main_regions(self.img),
                   Region('ram', R.RAM[0], self.ram, 'rw', capture=True),
                   Region('ram_unc', R.RAM[0] + 0x40000000, self.ram, 'rw', alias_of='ram'),
                   Region('rom_memcpy', R.ROM_MEMCPY[0], bytes.fromhex(R.ROM_MEMCPY[1]), 'rx'),
                   Region('rom_memset', R.ROM_MEMSET[0], bytes.fromhex(R.ROM_MEMSET[1]), 'rx'),
                   Region('tcbtab', 0x8FF00000, bytes(tcb), 'r'),
                   Region('kern', R.KERN, R.kern() + bytes(0x10000 - 0x100), 'rw'),
                   Region('cpuid', 0x8050, bytes(4), 'r'),
                   Region('data', 0x61F7D540, self.img[0x60258000 - V.B:0x602AE000 - V.B], 'rw'),
                   Region('hwsem', 0x8FDFF000, bytes(0x2000), 'rw'),
                   Region('heap', 0x61A00000, bytes(0x57D000), 'rw'), *extra]
        r = execute(regions, dict({'pc': pc}, **regs), stop, limit=20_000_000)
        if r['fault'] or r['registers']['pc'] != stop:
            raise SystemExit(f'run from {pc:#x} stopped at {r["registers"]["pc"]:#x}: {r["fault"]}')
        captured = {c['name']: bytes.fromhex(c['hex']) for c in r['memory']}
        self.ram = captured.pop('ram')
        self.captured = captured
        return r['registers']

    def _offset(self, addr):
        off = (addr - 0x40000000 if addr >= 0xA0000000 else addr) - R.RAM[0]
        assert 0 <= off < len(self.ram), hex(addr)
        return off

    def read(self, addr, n):
        off = self._offset(addr)
        return self.ram[off:off + n]

    def write(self, addr, data):
        off = self._offset(addr)
        self.ram = self.ram[:off] + data + self.ram[off + len(data):]

    def set_value(self, sid, value):    # the facade call the look editor uses (Color Creator commit 0x60e4c0a7)
        return self.call(0x60837170, None, 0, {'d0': sid, 'd1': 0, 'a1': value & 0xFFFFFFFF, 'a0': FACADE_OBJ})['d0']

    def get_value(self, sid):
        self.write(OUT, b'\xee' * 4)
        ret = self.call(0x60836747, None, 0, {'d0': sid, 'a1': OUT, 'a0': FACADE_OBJ})['d0']
        return ret, struct.unpack('<i', self.read(OUT, 4))[0]

    def store_value(self, sid, value):  # core setter 0x60863a8a, used to seed the boot-path checks
        return self.call(0x60863A8A, 0xE0, 16, {'d0': sid, 'd1': value, 'a0': 0x627FD000})['d0']

    def data_address(self, sid):
        key, _ = struct.unpack_from('<HH', self.img, SID_TABLE + 4 * sid - V.B)
        return struct.unpack('<I', self.read(REGISTRY + (key >> 4) * 8 + 4, 4))[0]


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('spec', nargs='?')
    p.add_argument('--sid', type=int, default=961)
    a = p.parse_args()
    emu = Emu(a.spec)
    for v in range(4):
        ret, got = emu.set_value(a.sid, v), emu.get_value(a.sid)
        assert ret == 0 and got == (0, v), (v, ret, got)
    print(f'sid {a.sid}: facade SetValue 0..3 accepted, GetValue reads each back')
    data = emu.data_address(a.sid)
    assert BLOCK90[0] <= data < BLOCK90[1], hex(data)
    print(f'sid {a.sid}: stored at {data:#x}, inside settings block 90')
    for name, entry, flag, control_reset in BOOT_PATHS:
        emu.store_value(a.sid, 3)
        emu.store_value(CONTROL_SID, 2)
        emu.write(SID_10052_RAM, struct.pack('<I', flag))
        emu.call(entry, 0x80, 8, {})
        emu.write(SID_10052_RAM, bytes(4))
        sid_after, control_after = emu.get_value(a.sid)[1], emu.get_value(CONTROL_SID)[1]
        assert sid_after == 3, (name, sid_after)
        assert control_after == (0 if control_reset else 2), (name, control_after)
        print(f'{name}: sid {a.sid} kept 3; control sid {CONTROL_SID} -> {control_after}')
    print('RESULT PASS')


if __name__ == '__main__':
    main()
