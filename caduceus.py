#!/usr/bin/env python3
"""Caduceus user-side builder for Olympus / OM System firmware patches.

Supports multiple camera bodies (PEN E-P7, OM-D E-M1 Mark II, etc.).
We do not redistribute OM Digital Solutions firmware. This script downloads the
stock update from OM's own server (or uses a local copy), checks its SHA-256,
applies a release's edit list (releases/.../edits.json) and writes the update
files for your SD card. Every output hash must match the release's SHA256SUMS
exactly, otherwise nothing is written.

  python3 caduceus.py [--release VERSION] [--sd CARD]
  python3 caduceus.py build --release v0.4c24 [--out DIR] [--stock FILE]
  python3 caduceus.py verify DIR
  python3 caduceus.py list

Python 3.10+, standard library only. Never talks to a camera.

Container format (scrambled "OE" blocks: byte inversion + 16-byte lane
permutation, additive 32-bit checksum) as documented publicly by Altsoph and
mx3 in CHDK forum thread 2471.
"""
import re, argparse
from dataclasses import dataclass, replace
import hashlib
import html
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
import time
from typing import Dict, List, Optional, Tuple
import urllib.request
import xml.etree.ElementTree as ET
from array import array
from pathlib import Path

FROZEN = getattr(sys, 'frozen', False)
DATA_ROOT = Path(sys._MEIPASS) if FROZEN else Path(__file__).resolve().parent
APP_ROOT = Path(sys.executable).resolve().parent if FROZEN else DATA_ROOT
RELEASES = DATA_ROOT / 'releases'
INSTALL_CAMERA = 'em1mk2'
RECOMMENDED_RELEASE = 'v0.4c24'
INSTALL_GUIDE = ('https://github.com/xtruong88/caduceus-em1ii/blob/main/'
                 'docs/huong-dan-firmware-em1-ii.md')
CATALOG = 'https://fw01.om-digitalsolutions.net/ww_inform/fcache.do'
EM1MK2_CATALOG_STOCK_SHA = '691a8a8e90af75b3848b70856a3a49ef24d72394cdfd2766fa37bdfe6325de70'

# ---------------------------------------------------------------- camera models
@dataclass(frozen=True)
class Camera:
    id: str                         # 'ep7', 'em1mk2'
    name: str                       # 'Olympus PEN E-P7', 'Olympus OM-D E-M1 Mark II'
    model_id: str                   # '1420', '1250'
    model_code: int                 # 0x1420, 0x1250
    version: str                    # '1.1', '3.70'
    version_code: int               # 0x1100, 0x3700
    main_base: int                  # CPU address of main-component payload byte 0
    card_name: str                  # SD update payload name, e.g. 'E1429999.BIN'
    mod_dir: str                    # Mod folder on SD card, e.g. 'EP7MOD', 'EM1MOD'
    stock_name: str                 # Official stock file name
    stock_sha: str                  # SHA-256 of official stock file
    stock_size: int                 # Byte size
    catalog_hard_code: str          # Hardware info code in OM catalog requests
    catalog_firmware_version: str   # Firmware version in OM catalog requests
    alt_stock_names: Tuple[str, ...] = ()

    @property
    def update_path(self) -> str:
        return f'DCOLYMP/{self.card_name}'

    @property
    def restore_path(self) -> str:
        return f'restore/{self.card_name}'


CAMERAS: Dict[str, Camera] = {
    'ep7': Camera(
        id='ep7',
        name='Olympus PEN E-P7',
        model_id='1420',
        model_code=0x1420,
        version='1.1',
        version_code=0x1100,
        main_base=0x60020020,
        card_name='E1429999.BIN',
        mod_dir='EP7MOD',
        stock_name='OLY_E_142_1100_0000_0000.BIN',
        stock_sha='9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb',
        stock_size=111017984,
        catalog_hard_code='OLYE142000000000',
        catalog_firmware_version='00001000',
        alt_stock_names=('E1429999.BIN',),
    ),
    'em1mk2': Camera(
        id='em1mk2',
        name='Olympus OM-D E-M1 Mark II',
        model_id='1250',
        model_code=0x1250,
        version='3.70',
        version_code=0x3700,
        main_base=0x60021020,
        card_name='E1259999.BIN',
        mod_dir='EM1MOD',
        stock_name='OLY_E_125_3700_0000_0000.BIN',
        stock_sha='f0c25dd80e3fe2f38af0bc515f250692c47c42758eef411dfaef1f9674dd66dc',
        stock_size=93050944,
        catalog_hard_code='OLYE125000000000',
        catalog_firmware_version='00003000',
        alt_stock_names=('E1259999.BIN',),
    ),
    'em10iv': Camera(
        id='em10iv',
        name='Olympus OM-D E-M10 Mark IV',
        model_id='1400',
        model_code=0x1400,
        version='1.1',
        version_code=0x1100,
        main_base=0x60020020,
        card_name='E1409999.BIN',
        mod_dir='EM10MOD',
        stock_name='OLY_E_140_1100_0000_0000.BIN',
        stock_sha='4f9ea315a6b7d2db3cb8c11e74f88e404bfda3b76921bc1e3cb6441bf97e9aac',
        stock_size=111017984,
        catalog_hard_code='OLYE140000000000',
        catalog_firmware_version='00001000',
        alt_stock_names=('E1409999.BIN',),
    ),
}

DEFAULT_CAM = CAMERAS['ep7']


def get_camera(cam_id: Optional[str] = None) -> Camera:
    if not cam_id:
        return DEFAULT_CAM
    k = cam_id.lower().strip()
    aliases = {
        'e-p7': 'ep7',
        'e-m1mk2': 'em1mk2',
        'em1-mk2': 'em1mk2',
        'em1ii': 'em1mk2',
        'e-m1ii': 'em1mk2',
        'em1mark2': 'em1mk2',
        'e-m10iv': 'em10iv',
        'em10-iv': 'em10iv',
    }
    k = aliases.get(k, k)
    if k not in CAMERAS:
        valid = ', '.join(CAMERAS.keys())
        raise Refuse(f'unknown camera {cam_id!r}. Supported cameras: {valid}')
    return CAMERAS[k]


class Refuse(Exception):
    pass


def sha(b):
    return hashlib.sha256(b).hexdigest()


# ---------------------------------------------------------------- container
LANES = (1, 3, 0, 2, 6, 4, 7, 5, 11, 10, 9, 8, 13, 14, 12, 15)
INV = bytes(i ^ 0xFF for i in range(256))


def decode(data):
    out = bytearray(len(data))
    for o, i in enumerate(LANES):
        out[o::16] = data[i::16].translate(INV)
    return bytes(out)


def encode(data):
    out = bytearray(len(data))
    for i, o in enumerate(LANES):
        out[o::16] = data[i::16].translate(INV)
    return bytes(out)


def sum32(data):
    w = array('I')
    if w.itemsize != 4:
        return sum(x for (x,) in struct.iter_unpack('<I', data)) & 0xFFFFFFFF
    w.frombytes(data)
    if sys.byteorder != 'little':
        w.byteswap()
    return sum(w) & 0xFFFFFFFF


def parse(data):
    """-> list of (offset, header, payload, trailer); payload decoded."""
    blocks, off, model = [], 0, None
    while off < len(data):
        if len(data) - off < 64:
            raise Refuse(f'container: truncated block at {off:#x}')
        hdr = data[off:off + 32]
        if hdr[:2] != b'OE' or struct.unpack_from('<I', hdr, 20)[0] == 0:
            raise Refuse(f'container: unsupported block at {off:#x}')
        model = model or hdr[2:4]
        size = struct.unpack_from('<I', hdr, 12)[0]
        end = off + size + 64
        if hdr[2:4] != model or not size or size % 16 or end > len(data):
            raise Refuse(f'container: bad block header at {off:#x}')
        trl = data[end - 32:end]
        if hdr[:28] != trl[:28] or hdr[28:] != b'\0' * 4:
            raise Refuse(f'container: header/trailer mismatch at {off:#x}')
        pay = decode(data[off + 32:end - 32])
        if (sum32(hdr) + sum32(pay) + sum32(trl)) & 0xFFFFFFFF:
            raise Refuse(f'container: checksum mismatch at {off:#x}')
        blocks.append((off, hdr, pay, trl))
        off = end
    return blocks


def kind(hdr):
    return struct.unpack_from('<H', hdr, 20)[0]


def reseal(hdr, pay, trl):
    t = bytearray(trl)
    t[28:] = b'\0' * 4
    struct.pack_into('<I', t, 28, -(sum32(hdr) + sum32(pay) + sum32(t)) & 0xFFFFFFFF)
    return bytes(t)


# ---------------------------------------------------------------- build
def apply_edits(spec, stock, camera: Optional[Camera] = None):
    """Same rules and checks as tools/build_package.py. -> (patched, restore)."""
    cam = camera or get_camera(spec.get('camera'))
    blocks = parse(stock)
    by_kind = {kind(h): (o, h, p, t) for o, h, p, t in blocks}
    kinds = [int(k, 16) for k in spec['components']]
    if (0x100 in kinds and kinds[0] != 0x100) or len(set(kinds)) != len(kinds) \
            or any(k not in by_kind for k in kinds):
        raise Refuse('edits.json: bad component list')
    pays = {k: bytearray(by_kind[k][2]) for k in kinds}
    spans, total = {}, 0
    for e in spec['edits']:
        k = int(e['kind'], 16)
        a = e['addr']
        if k not in pays:
            raise Refuse(f'edits.json: edit {a} targets a component not in the package')
        if a.startswith('off:'):
            off = int(a[4:], 16)
        elif k == 0x100:
            off = int(a, 16) - cam.main_base
        else:
            raise Refuse(f'edits.json: edit {a}: CPU address on a non-main component')
        exp, new = bytes.fromhex(e['expect']), bytes.fromhex(e['new'])
        if len(exp) != len(new) or not new or not 0 <= off <= len(pays[k]) - len(new):
            raise Refuse(f'edits.json: edit {a}: bad length or range')
        if any(off < y and x < off + len(new) for x, y in spans.get(k, [])):
            raise Refuse(f'edits.json: edit {a}: overlaps another edit')
        if by_kind[k][2][off:off + len(exp)] != exp:
            raise Refuse(f'edits.json: edit {a}: stock bytes differ from expected')
        spans.setdefault(k, []).append((off, off + len(new)))
        pays[k][off:off + len(new)] = new
        total += sum(x != y for x, y in zip(exp, new))
    parts = []
    for k in kinds:
        _, h, p, t = by_kind[k]
        np_ = bytes(pays[k])
        parts.append(h + encode(np_) + (reseal(h, np_, t) if np_ != p else t))
    patched = b''.join(parts)
    restore = b''.join(stock[o:o + 64 + len(p)] for o, h, p, t in (by_kind[k] for k in kinds))
    # re-verify outputs from scratch
    rp, rr = parse(patched), parse(restore)
    if [kind(b[1]) for b in rp] != kinds or [kind(b[1]) for b in rr] != kinds:
        raise Refuse('internal: output component list wrong')
    changed = 0
    for (_, h, p, t), (_, sh, sp, st), (_, rh, rpay, rt) in zip(rp, (by_kind[k] for k in kinds), rr):
        if h != sh or t[:28] != st[:28] or rh != sh or rpay != sp:
            raise Refuse('internal: output metadata/restore differs from stock')
        changed += sum(x != y for x, y in zip(p, sp))
    if changed != total:
        raise Refuse(f'internal: changed bytes {changed} != edited bytes {total}')
    return patched, restore


# ---------------------------------------------------------------- download
def fetch_stock(camera: Optional[Camera] = None, *, accept_license: bool = False):
    cam = camera or DEFAULT_CAM
    t = time.strftime('%Y%m%d%H%M%S', time.gmtime())
    req = (f"<?xml version='1.0' encoding='utf-8'?><firmware_demand><revision>0001</revision>"
           f"<mac_address>00-00-00-00-00-00</mac_address><time>{t}</time><language>ENU</language>"
           f"<application>FWUT</application><type>0000</type><version>00005000</version><os>WIN</os>"
           f"<country_code>0001</country_code><hardwares><firmup_mode>0</firmup_mode><hardware_info>"
           f"<hard_code>{cam.catalog_hard_code}</hard_code><firmware_version>{cam.catalog_firmware_version}</firmware_version>"
           f"<serial_no>000000000</serial_no></hardware_info></hardwares></firmware_demand>")
    hdrs = {'User-Agent': 'Olympus', 'Content-Type': 'text/xml; Charset=UTF-8'}
    print(f'Asking OM Digital Solutions for {cam.name} {cam.version} firmware ...')
    try:
        with urllib.request.urlopen(urllib.request.Request(CATALOG, req.encode(), hdrs), timeout=60) as r:
            catalog = ET.fromstring(r.read())
        info = catalog.find('.//firmware_info')
        if info is None or info.findtext('model_id') != cam.model_id:
            raise Refuse(f'OM server did not offer {cam.name} firmware {cam.version} (it may have moved). '
                         f'Download {cam.stock_name} yourself and use --stock FILE.')
        url = info.findtext('url')
        if not url or not url.startswith(('https://', 'http://')):
            raise Refuse('OM did not provide a firmware download URL. Use --stock FILE with a local copy.')
        license_text = catalog.findtext('.//license_agreement', '').strip()
        if not license_text:
            raise Refuse('OM did not provide its firmware license. Use --stock FILE with a local copy.')
        print('\nOM Digital Solutions firmware license\n')
        print(html.unescape(license_text).replace(r'\n', '\n'))
        if not accept_license:
            if not (sys.stdin and sys.stdin.isatty()):
                raise Refuse('review the OM license above and use --accept-license to confirm acceptance.')
            try:
                answer = input('\nType yes to accept the OM license and download: ').strip().lower()
            except EOFError:
                answer = ''
            if answer != 'yes':
                raise Refuse('OM license declined. No firmware was downloaded.')
        print(f'Downloading {cam.stock_name} from {url.split("/")[2]}')
        buf = bytearray()
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Olympus'}),
                                    timeout=120) as r:
            while chunk := r.read(1 << 20):
                buf += chunk
                print(f'\r  {len(buf) >> 20} / {cam.stock_size >> 20} MiB', end='', flush=True)
        print()
        return bytes(buf)
    except (OSError, ET.ParseError) as e:
        raise Refuse(f'download failed: {e}\nIf this keeps happening, download {cam.stock_name} '
                     f'another way and pass --stock FILE. See {INSTALL_GUIDE}.')


# ---------------------------------------------------------------- releases
def read_sums(path):
    sums = {}
    for line in path.read_text().splitlines():
        if line.strip():
            h, name = line.split(maxsplit=1)
            sums[name.lstrip('*')] = h.lower()
    return sums


def release_package_hashes(sums, cam: Camera):
    """Resolve package checksums named either generically or by the camera's updater."""
    patched = sums.get('patched.pkg.bin', sums.get(cam.card_name))
    restore = sums.get('restore-stock.pkg.bin')
    if not patched or not restore:
        raise Refuse(f'release SHA256SUMS is missing a package checksum for {cam.name}.')
    return {cam.update_path: patched, cam.restore_path: restore}


def release_stock_hash(spec, cam: Camera):
    expected = spec.get('stock_sha256', cam.stock_sha)
    if expected != cam.stock_sha and not (cam.id == 'em1mk2' and expected == EM1MK2_CATALOG_STOCK_SHA):
        raise Refuse(f'Unsupported stock firmware checksum for {cam.name}: {expected!r}')
    return expected


def _release_entry(d: Path) -> Optional[Tuple[str, Path, str]]:
    """Return (release_name, dir_path, camera_id) if valid release dir."""
    edits_file = d / 'edits.json'
    sums_file = d / 'SHA256SUMS'
    if not (edits_file.is_file() and sums_file.is_file()):
        return None
    try:
        spec = json.loads(edits_file.read_text())
        if not isinstance(spec, dict):
            return None
        cam = get_camera(spec.get('camera') or ('em1mk2' if 'em1mk2' in d.name else 'ep7'))
        release_package_hashes(read_sums(sums_file), cam)
    except (Refuse, ValueError):
        return None
    return d.name, d, cam.id


def releases(camera_id: Optional[str] = None):
    results = []
    if RELEASES.is_dir():
        for d in sorted(RELEASES.iterdir()):
            if d.is_dir():
                # Subdirectory per camera (e.g. releases/em1mk2/v0.1)
                if d.name in CAMERAS:
                    for sub in sorted(d.iterdir()):
                        res = _release_entry(sub)
                        if res:
                            results.append((f"{d.name}/{res[0]}", res[1], res[2]))
                else:
                    res = _release_entry(d)
                    if res:
                        results.append((res[0], res[1], res[2]))

    # Also check body folders (e.g. em1mk2/releases/v0.1)
    for cam_id in CAMERAS:
        cam_rel = DATA_ROOT / cam_id / 'releases'
        if cam_rel.is_dir():
            for d in sorted(cam_rel.iterdir()):
                res = _release_entry(d)
                if res and (f"{cam_id}/{res[0]}" not in [r[0] for r in results]):
                    results.append((f"{cam_id}/{res[0]}", res[1], cam_id))

    if camera_id:
        target_cam = get_camera(camera_id).id
        return sorted(r[0] for r in results if r[2] == target_cam)
    return sorted(r[0] for r in results)


def find_release_dir(name: str, camera_id: Optional[str] = None) -> Tuple[Path, Camera]:
    """Find release directory and determine its camera profile."""
    prefix, separator, version = name.rpartition('/')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', version) or (separator and prefix not in CAMERAS):
        raise Refuse(f'invalid release name {name!r}. Choose a release shown by list.')
    # Direct path checks
    candidates = []
    if camera_id:
        c = get_camera(camera_id)
        candidates.extend([
            RELEASES / c.id / name,
            DATA_ROOT / c.id / 'releases' / name,
            RELEASES / f"{c.id}-{name}",
            RELEASES / name,
        ])
    else:
        # Check if name has camera prefix
        if '/' in name:
            cam_part, rel_part = name.split('/', 1)
            if cam_part in CAMERAS:
                candidates.extend([
                    RELEASES / cam_part / rel_part,
                    DATA_ROOT / cam_part / 'releases' / rel_part,
                ])
        candidates.extend([
            RELEASES / name,
        ])
        for c in CAMERAS.values():
            candidates.extend([
                RELEASES / c.id / name,
                DATA_ROOT / c.id / 'releases' / name,
                RELEASES / f"{c.id}-{name}",
            ])

    for d in candidates:
        if d.is_dir() and (d / 'edits.json').is_file() and (d / 'SHA256SUMS').is_file():
            spec = json.loads((d / 'edits.json').read_text())
            legacy_em1 = d.parent.name == 'em1mk2' or d.name.startswith('em1mk2-')
            spec_cam = spec.get('camera') or ('em1mk2' if legacy_em1 else 'ep7')
            cam = get_camera(spec_cam)
            if camera_id is None or cam.id == get_camera(camera_id).id:
                return d, cam

    avail = ', '.join(releases(camera_id)) or 'none'
    raise Refuse(f'unknown release {name!r}. Available: {avail}')


def load_release(name: str, camera_id: Optional[str] = None):
    d, cam = find_release_dir(name, camera_id)
    sums = read_sums(d / 'SHA256SUMS')
    spec_bytes = (d / 'edits.json').read_bytes()
    if 'edits.json' in sums and sha(spec_bytes) != sums['edits.json']:
        raise Refuse(f'{d}/edits.json does not match {d}/SHA256SUMS '
                     '(repository out of sync; update your copy).')
    spec = json.loads(spec_bytes)
    expected_stock = release_stock_hash(spec, cam)
    if 'stock_sha256' in spec and (
        'edits.json' not in sums or sums.get('restore-stock.pkg.bin') != expected_stock
    ):
        raise Refuse(f'{d}: the stock checksum must be sealed with the edits and the full stock restore.')
    cam = replace(cam, stock_sha=expected_stock)
    card = {}
    for n, h in sums.items():
        if n.startswith('card/'):
            f = d / n
            if not f.is_file():
                raise Refuse(f'missing {d}/{n}')
            b = f.read_bytes()
            if sha(b) != h:
                raise Refuse(f'{d}/{n} does not match SHA256SUMS')
            card[n[len('card/'):]] = b
    return spec, sums, card, cam


def find_stock(camera: Optional[Camera] = None):
    """Find a local OM file matching the selected release's stock checksum."""
    cam = camera or DEFAULT_CAM
    names = [cam.stock_name] + list(cam.alt_stock_names)
    search_dirs = [
        APP_ROOT,
        APP_ROOT / 'stock_firmware',
        APP_ROOT / 'stock_firmware' / cam.id,
        APP_ROOT / 'stock_firmware' / f"omd{cam.id}",
        APP_ROOT / cam.id / 'firmware',
        APP_ROOT / 'cache' / cam.stock_sha,
        APP_ROOT / 'cache',
        Path.home() / 'Downloads',
    ]
    for d in search_dirs:
        for n in names:
            p = d / n
            try:
                if p.is_file() and p.stat().st_size == cam.stock_size and sha(p.read_bytes()) == cam.stock_sha:
                    return p
            except OSError:
                pass
    return None


def cmd_build(a):
    out = Path(a.out)
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise Refuse(f'{out} already exists and is not empty; choose another --out or remove it.')
    spec, sums, card, cam = load_release(a.release, getattr(a, 'camera', None))
    package_hashes = release_package_hashes(sums, cam)
    if a.stock:
        p = Path(a.stock)
        if not p.is_file():
            raise Refuse(f'--stock: no such file {p}')
        stock = p.read_bytes()
    else:
        local_stock = find_stock(cam)
        if local_stock:
            print(f'Using local stock file for {cam.name}: {local_stock}')
            stock = local_stock.read_bytes()
        else:
            stock = fetch_stock(cam, accept_license=getattr(a, 'accept_license', False))

    if sha(stock) != cam.stock_sha:
        raise Refuse(f'stock firmware SHA-256 is {sha(stock)}\nexpected {cam.stock_sha}\n'
                     f'This package differs from the stock {cam.name} {cam.version} image pinned for this release. Nothing written.')
    print(f'Stock firmware for {cam.name} OK. Applying {len(spec["edits"])} edits ...')
    patched, restore = apply_edits(spec, stock, camera=cam)
    files = {cam.update_path: patched, cam.restore_path: restore, **card}
    for rel_name, expected in package_hashes.items():
        actual = sha(files[rel_name])
        if actual != expected:
            raise Refuse(f'{rel_name}: built hash {actual} != release {expected}. Nothing written.')
    # write into a temp dir next to the target, then move into place
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix='.caduceus-', dir=out.parent))
    try:
        for rel, data in files.items():
            f = tmp / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(data)
        (tmp / 'SHA256SUMS').write_text(''.join(f'{sha(d)}  {r}\n' for r, d in sorted(files.items())))
        (tmp / 'RELEASE').write_text(a.release + '\n')
        (tmp / 'CAMERA').write_text(cam.id + '\n')
        if out.exists():
            out.rmdir()
        os.replace(tmp, out)
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    print(f'\nCaduceus [{cam.name}] {a.release} written to {out}:')
    for r in sorted(files):
        print(f'  {r}')
    print(f'  SHA256SUMS\nAll hashes match the release. Next: copy DCOLYMP/ and {cam.mod_dir}/ to your SD card;'
          ' keep restore/ on your computer.')
    return 0


def cmd_verify(a):
    d = Path(a.dir)
    man = d / 'SHA256SUMS'
    if not man.is_file():
        raise Refuse(f'{man} not found; is {d} a caduceus build directory?')
    sums, bad = read_sums(man), 0
    if not sums:
        raise Refuse(f'{man} contains no file checksums.')
    for rel, h in sorted(sums.items()):
        f = d / rel
        ok = f.is_file() and sha(f.read_bytes()) == h
        bad += not ok
        print(f'  {"OK  " if ok else "FAIL"}  {rel}')
    rel_name = (d / 'RELEASE').read_text().strip() if (d / 'RELEASE').is_file() else None
    cam_name = (d / 'CAMERA').read_text().strip() if (d / 'CAMERA').is_file() else None
    if rel_name:
        try:
            rel_dir, cam = find_release_dir(rel_name, cam_name)
        except Refuse as e:
            print(f'  note: {e}; checked the local manifest only')
        else:
            rs = read_sums(rel_dir / 'SHA256SUMS')
            want = release_package_hashes(rs, cam)
            want.update({n[len('card/'):]: h for n, h in rs.items() if n.startswith('card/')})
            if want != sums:
                bad += 1
                print(f'  FAIL  file list/hashes differ from {rel_dir}/SHA256SUMS')
            else:
                print(f'  OK    matches {rel_dir}/SHA256SUMS')
    else:
        print(f'  note: no RELEASE metadata found; checked the local manifest only')
    if bad:
        raise Refuse(f'{bad} problem(s). Do not flash these files; rebuild them.')
    print('All good.')
    return 0


def cmd_list(a):
    cam_filter = getattr(a, 'camera', None)
    rels = releases(cam_filter)
    if not rels:
        print(f"No releases found{' for ' + cam_filter if cam_filter else ''}.")
        return 0
    for name in rels:
        labels = []
        if name == f'{INSTALL_CAMERA}/{RECOMMENDED_RELEASE}':
            labels.append('(recommended)')
        if name.endswith('t'):
            labels.append('(test)')
        if name.startswith(f'{INSTALL_CAMERA}/'):
            directory, cam = find_release_dir(name, cam_filter)
            spec = json.loads((directory / 'edits.json').read_text())
            if release_stock_hash(spec, cam) != EM1MK2_CATALOG_STOCK_SHA:
                labels.append('(requires old stock)')
        print(name, *labels)
    return 0


# ---------------------------------------------------------------- one-press mode
def vkey(name):
    clean = name.split('/')[-1]
    m = re.fullmatch(r'v(\d+(?:\.\d+)*)(?:([a-z])(\d*))?', clean)
    if not m:
        return (), '', 0
    version, suffix, revision = m.groups()
    return tuple(map(int, version.split('.'))), suffix or '', int(revision or 0)


def latest_release(camera_id: Optional[str] = None):
    rs = [r for r in releases(camera_id) if r.split('/')[-1].startswith('v')]
    if not rs:
        raise Refuse('no releases found next to caduceus.py (is the download complete?)')
    return max(rs, key=vkey)


def _scan_cards(found):
    if os.name == 'nt':
        import ctypes, string
        for L in string.ascii_uppercase:
            r = Path(f'{L}:\\')
            try:
                if ctypes.windll.kernel32.GetDriveTypeW(f'{L}:\\') == 2 and (r / 'DCIM').is_dir():
                    found.append(r)
            except OSError:
                pass
        return
    user = os.environ.get('USER', '')
    for base in (Path('/Volumes'), Path('/media') / user, Path('/run/media') / user, Path('/media')):
        try:
            entries = list(base.iterdir()) if base.is_dir() else []
        except OSError:
            continue
        for r in entries:
            try:
                if r.is_dir() and (r / 'DCIM').is_dir() and r not in found:
                    found.append(r)
            except OSError:
                pass


def sd_cards(limit=10.0):
    env = os.environ.get('CADUCEUS_CARD_DIRS')
    if env is not None:
        return [Path(x) for x in env.split(os.pathsep) if x and (Path(x) / 'DCIM').is_dir()]
    import threading
    found = []
    t = threading.Thread(target=_scan_cards, args=(found,), daemon=True)
    t.start()
    t.join(limit)
    if t.is_alive():
        print('  (card search took too long; skipped slow drives)')
    return list(found)


def card_path(value):
    if os.name == 'nt' and re.fullmatch(r'[A-Za-z]:', value):
        value += '\\'
    card = Path(value).resolve()
    if not (card / 'DCIM').is_dir():
        raise Refuse(f'{card} has no DCIM folder. Select the root of an SD card used in your camera.')
    return card


def select_card():
    cards = sd_cards()
    if len(cards) <= 1:
        return cards[0] if cards else None
    if not (sys.stdin and sys.stdin.isatty()):
        return None
    for number, card in enumerate(cards, 1):
        print(f'  {number}. {card}')
    try:
        selected = int(input('Choose an SD card number (Enter to skip): '))
    except (EOFError, ValueError):
        return None
    return cards[selected - 1] if 1 <= selected <= len(cards) else None


def ask(q, default=True):
    try:
        if not (sys.stdin and sys.stdin.isatty()):
            print(f'{q} -> no terminal to ask, so: no')
            return False
        a = input(f'{q} [{"Y/n" if default else "y/N"}] ').strip().lower()
    except (EOFError, OSError, RuntimeError):
        return False
    return default if not a else a.startswith('y')


def pause():
    if os.environ.get('CADUCEUS_LAUNCHER'):
        return
    try:
        if sys.stdin and sys.stdin.isatty():
            input('\nPress Enter to close...')
    except (EOFError, OSError, RuntimeError, KeyboardInterrupt):
        pass


def copy_synced(src, dst):
    with tempfile.TemporaryDirectory(prefix='.caduceus-', dir=dst.parent) as temporary:
        pending = Path(temporary) / dst.name
        with open(src, 'rb') as i, pending.open('wb') as o:
            shutil.copyfileobj(i, o, 1 << 20)
            o.flush()
            if sys.platform == 'darwin':
                try:
                    import fcntl
                    fcntl.fcntl(o.fileno(), fcntl.F_FULLFSYNC)
                except (OSError, AttributeError):
                    os.fsync(o.fileno())
            else:
                os.fsync(o.fileno())
        if sha(pending.read_bytes()) != sha(src.read_bytes()):
            raise Refuse(f'copy check failed for {dst}. Do not flash.')
        os.replace(pending, dst)


def em1mk2_looks_ok(data: bytes) -> bool:
    """True if the E-M1 II card loader (sd_loader.s sd_check) would accept this LOOKS.BIN: E-P7 v3 header and CRC."""
    size = len(data)
    if not 128 <= size <= 2112 or size % 64:
        return False
    magic, version, hdr_len = data[:4], *struct.unpack_from('<HH', data, 4)
    payload, crc = struct.unpack_from('<II', data, 12)
    n, rec_len = struct.unpack_from('<HH', data, 24)
    if (magic, version, hdr_len, rec_len) != (b'EP7B', 3, 64, 64) or payload != size - 64 or n != payload // 64:
        return False
    return zlib.crc32(data[:16] + data[20:]) & 0xffffffff == crc


def copy_to_card(build, card, camera: Camera):
    """Copy the update and starter files, keeping the user's camera settings."""
    card = card_path(str(card))
    dco = card / 'DCOLYMP'
    try:
        dco.mkdir(exist_ok=True)
    except PermissionError:
        raise Refuse(f'not allowed to write to {card}.' + (
            ' On macOS: System Settings > Privacy & Security > Files and Folders (or Full Disk Access), allow '
            'Terminal to access Removable Volumes, then run this again, or drag the folders across in Finder.'
            if sys.platform == 'darwin' else ' Check the card is not write-locked (the small switch on the card).'))
    for old in dco.glob('*.BIN'):
        if old.name.upper() != camera.card_name.upper():
            print(f'  note: {old} is another update file; remove it before flashing.')
    mod = card / camera.mod_dir
    mod.mkdir(exist_ok=True)
    looks = build / camera.mod_dir / 'LOOKS.BIN'
    if looks.is_file():
        card_looks = mod / 'LOOKS.BIN'
        keep = camera.id == 'em1mk2' and card_looks.is_file() and em1mk2_looks_ok(card_looks.read_bytes())
        if keep:
            print(f'  kept your existing {camera.mod_dir}/LOOKS.BIN (your saved looks)')
        else:
            if camera.id == 'em1mk2' and card_looks.exists():
                print(f'  replaced {camera.mod_dir}/LOOKS.BIN: this firmware cannot read it (old format or damaged)')
            copy_synced(looks, card_looks)
    extras = () if camera.id == 'em1mk2' else (
        ('BUNDLES.BIN', 'looks'), ('MOVIE.BIN', 'Movie colour settings'), ('AP.BIN', 'AP Custom colour settings'),
    )
    for name, what in extras:
        if (build / camera.mod_dir / name).exists():
            if (mod / name).exists():
                print(f'  kept your existing {camera.mod_dir}/{name} (your {what})')
            else:
                copy_synced(build / camera.mod_dir / name, mod / name)
    print('  copying the update (about 100 MB) ...')
    copy_synced(build / 'DCOLYMP' / camera.card_name, dco / camera.card_name)
    print(f'  copied and checked on {card}')


def open_folder(p):
    try:
        if os.name == 'nt':
            os.startfile(p)
            return
        cmd = ['open', str(p)] if sys.platform == 'darwin' else ['xdg-open', str(p)]
        subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True)
    except OSError:
        pass


def cmd_easy(a):
    rel = getattr(a, 'release', None) or RECOMMENDED_RELEASE
    _, sums, _, cam = load_release(rel, INSTALL_CAMERA)
    card = card_path(a.sd) if getattr(a, 'sd', None) else None
    clean_rel = rel.split('/')[-1]
    print(f'Caduceus [{cam.name}] one-press build: {clean_rel}\n')
    out = APP_ROOT / 'out' / f'{cam.id}-{clean_rel}'
    expected = release_package_hashes(sums, cam)
    expected.update({name[len('card/'):]: digest for name, digest in sums.items() if name.startswith('card/')})
    if all((out / name).is_file() and sha((out / name).read_bytes()) == digest
           for name, digest in expected.items()):
        print(f'Using verified build at {out}')
    else:
        stock = find_stock(cam)
        if stock is None:
            data = fetch_stock(cam, accept_license=getattr(a, 'accept_license', False))
            actual = sha(data)
            if actual != cam.stock_sha:
                raise Refuse(f'Downloaded stock firmware SHA-256 is {actual}; expected {cam.stock_sha}.')
            stock = APP_ROOT / 'cache' / cam.stock_sha / cam.stock_name
            stock.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(dir=stock.parent) as temporary:
                pending = Path(temporary) / stock.name
                pending.write_bytes(data)
                os.replace(pending, stock)
        cmd_build(argparse.Namespace(out=out, release=rel, camera=cam.id, stock=stock))
    if card is None:
        print('\nLooking for a camera SD card ...')
        card = select_card()
    if card is not None and ask(f'Copy the update to the SD card at {card}?', default=False):
        try:
            copy_to_card(out, card, cam)
        except (Refuse, OSError) as e:
            raise Refuse(f'could not copy to the card: {e}\nDo not flash until the copy is complete. '
                         f'The verified files are in {out}.') from e
        print('\nNow eject the card, put it in the camera, then: full battery, hold OK and switch on.\n'
              f'LED steady = writing, ~2 Hz blink = done. See {INSTALL_GUIDE}.')
    else:
        print(f'\nCopy DCOLYMP and {cam.mod_dir} to the card, and keep restore/ on your computer.')
        open_folder(out)
    return 0


def main(argv=None):
    if sys.version_info < (3, 10):
        sys.exit('Python 3.10 or newer is required.')
    ap = argparse.ArgumentParser(prog='caduceus-build.exe' if FROZEN else 'caduceus.py',
                                 description='Build Caduceus firmware files for the Olympus OM-D E-M1 Mark II.')
    ap.add_argument('--camera', choices=[INSTALL_CAMERA], default=INSTALL_CAMERA)
    ap.add_argument('--release', help=f'one-press release (default: {RECOMMENDED_RELEASE})')
    ap.add_argument('--sd', help='one-press SD card root (for example E: or /Volumes/CAMERA). '
                                 'Copying requires confirmation in an interactive terminal.')
    license_help = 'confirm acceptance of the OM firmware license for unattended downloads'
    ap.add_argument('--accept-license', action='store_true', help=license_help)
    sub = ap.add_subparsers(dest='cmd')
    b = sub.add_parser('build', help='download stock, apply a release, write card files')
    b.add_argument('--camera', choices=[INSTALL_CAMERA], default=INSTALL_CAMERA)
    b.add_argument('--release', required=True, help='release name (for example v0.4c24)')
    b.add_argument('--out', default=APP_ROOT / 'out' if FROZEN else 'out',
                   help='new or empty output directory (default: out)')
    b.add_argument('--stock', help='use an already downloaded stock file instead of downloading')
    b.add_argument('--accept-license', action='store_true', default=argparse.SUPPRESS, help=license_help)
    b.set_defaults(fn=cmd_build)
    v = sub.add_parser('verify', help='re-check a build directory')
    v.add_argument('dir')
    v.set_defaults(fn=cmd_verify)
    l = sub.add_parser('list', help='list available releases')
    l.add_argument('--camera', choices=[INSTALL_CAMERA], default=INSTALL_CAMERA)
    l.set_defaults(fn=cmd_list)
    a = ap.parse_args(argv)
    for f in (sys.stdout, sys.stderr):
        try:
            f.reconfigure(line_buffering=True)
        except (AttributeError, ValueError):
            pass
    easy = a.cmd is None
    if easy:
        a.fn = cmd_easy
    try:
        return a.fn(a)
    except (Refuse, OSError) as e:
        print(f'refused: {e}', file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('interrupted.', file=sys.stderr)
        return 130
    finally:
        if easy:
            pause()


if __name__ == '__main__':
    sys.exit(main())
