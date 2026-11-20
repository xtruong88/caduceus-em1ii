#!/usr/bin/env python3
"""Validate and seal the E-M1 II port for OM's catalog firmware."""

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import struct


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import caduceus
from tools import build_package
from omdem1mk2_layout import BASE, loaded_sections

BASE_RELEASE = 'v0.4c15'
VERSION = 'v0.4c16'
COLOR_CREATOR_VERSION = 'v0.4c17'
CAMERA = 'em1mk2'
CATALOG_SECTION_END = 0x60257000
ASPECT_SECTION_END = 0x60257800
SECTION1_END_WORD = 0x60042B4D


def extract_for_build(stock):
    extracted = ROOT / 'em1mk2/extracted'
    extracted.mkdir(parents=True, exist_ok=True)
    components = {caduceus.kind(header): payload for _, header, payload, _ in caduceus.parse(stock)}
    for kind, filename in (
        (0x100, '00_0100_40560020.decoded.bin'),
        (0x101, '01_0101_42060020.decoded.bin'),
    ):
        path = extracted / filename
        if path.exists() and path.read_bytes() != components[kind]:
            raise ValueError(f'Existing extracted firmware differs from catalog stock: {path}')
        if not path.exists():
            path.write_bytes(components[kind])
    return components[0x100]


def catalog_spec(legacy, main):
    _, end = loaded_sections(main)[1]
    old = struct.pack('<I', CATALOG_SECTION_END)
    offset = SECTION1_END_WORD - BASE
    if end != CATALOG_SECTION_END or main[offset:offset + 4] != old:
        raise ValueError('Unexpected Section 1 end in the catalog firmware')
    padding = main[end - BASE:ASPECT_SECTION_END - BASE]
    if padding != b'\xff' * (ASPECT_SECTION_END - end):
        raise ValueError('Section 1 expansion overlaps non-padding content')
    section_end = {
        'kind': '0x100',
        'addr': hex(SECTION1_END_WORD),
        'expect': old.hex(),
        'new': struct.pack('<I', ASPECT_SECTION_END).hex(),
        'why': 'Load the Section 1 tail used by the v0.4c15 aspect code and labels',
    }
    return {
        **legacy,
        'version': VERSION,
        'stock_sha256': caduceus.EM1MK2_CATALOG_STOCK_SHA,
        'edits': [section_end, *legacy['edits']],
    }


def replace_color_creator_edits(spec):
    wheel = ROOT / 'patches/omdem1mk2/color_creator_wheel/edits.json'
    edits = json.loads(wheel.read_text(encoding='utf-8'))['edits']
    replacements = {(edit['kind'], edit['addr']): edit for edit in edits}
    if len(replacements) != len(edits):
        raise ValueError('Color Creator edits contain duplicate addresses')
    merged = []
    for edit in spec['edits']:
        patch = replacements.pop((edit['kind'], edit['addr']), None)
        if patch and not patch['expect'].startswith(edit['expect']):
            raise ValueError(f"Color Creator stock bytes changed at {edit['addr']}")
        merged.append(patch or edit)
    if replacements:
        raise ValueError('Color Creator changes must replace existing edits')
    if merged == spec['edits']:
        raise ValueError('Rebuild the Color Creator edits before sealing this release')
    return {**spec, 'version': COLOR_CREATOR_VERSION, 'edits': merged}


def validate(spec_path, version):
    checked = []

    def run(tool, *args, expected=None):
        cmd = [sys.executable, '-B', str(ROOT / 'tools' / f'omdem1mk2_{tool}.py'), *map(str, args)]
        print(f'Checking {tool} {" ".join(map(str, args))}', flush=True)
        if expected is None:
            subprocess.run(cmd, check=True, cwd=ROOT)
        else:
            result = subprocess.check_output(cmd, text=True, cwd=ROOT)
            print(result, end='', flush=True)
            if not all(line in result.splitlines() for line in expected):
                raise ValueError(f'Unexpected result from {tool}')
        checked.append(tool)

    run('check_loaded', spec_path)
    run('audit_opcodes', spec_path)
    run('emu_validator', expected=[
        f'sid {sid}: count 5 values [1, 3, 2, 4, 9]' for sid in (270, 511, 512)
    ])
    run('emu_validator', spec_path, expected=[
        f'sid {sid}: count 7 values [1, 3, 2, 4, 9, 6, 7]' for sid in (270, 511, 512)
    ])
    run('emu_rules', '-', expected=['offered values: [1, 2, 3, 4, 9]'])
    run('emu_rules', spec_path, expected=['offered values: [1, 2, 3, 4, 6, 7, 9]'])
    for tool in ('emu_aspect', 'emu_fixed_patches', 'emu_sdload', 'emu_af'):
        run(tool, spec_path)
    if version == COLOR_CREATOR_VERSION:
        run('emu_color_creator', spec_path)
    # Both releases preserve the camera-tested v0.4c15 aspect assets byte for byte.
    run('emu_scp', spec_path, '--reference', ROOT / 'releases' / CAMERA / BASE_RELEASE / 'edits.json')
    return sorted(set(checked))


def seal(stock_path, version):
    destination = ROOT / 'releases' / CAMERA / version
    if destination.exists():
        raise ValueError(f'Release already exists: {destination}')
    stock = stock_path.read_bytes()
    if caduceus.sha(stock) != caduceus.EM1MK2_CATALOG_STOCK_SHA:
        raise ValueError('The input must match the pinned E-M1 Mark II 3.70 OM catalog checksum')
    legacy, _, card, cam = caduceus.load_release(BASE_RELEASE, CAMERA)
    main = extract_for_build(stock)
    spec = catalog_spec(legacy, main)
    if version == COLOR_CREATOR_VERSION:
        spec = replace_color_creator_edits(spec)
    with tempfile.TemporaryDirectory(prefix='.catalog-release-', dir=destination.parent) as tmp:
        staging = Path(tmp) / version
        staging.mkdir()
        spec_path = staging / 'edits.json'
        spec_path.write_text(json.dumps(spec, indent=2) + '\n', encoding='utf-8', newline='\n')
        checked = validate(spec_path, version)
        patched, restore, info = build_package.build(spec, stock, camera=cam)
        if restore != stock or caduceus.apply_edits(spec, stock, camera=cam) != (patched, restore):
            raise ValueError('Independent package builders disagree or restore differs from stock')
        info.update(
            spec=f'releases/{CAMERA}/{version}/edits.json',
            spec_sha256=caduceus.sha(spec_path.read_bytes()),
            stock_sha256=spec['stock_sha256'],
            patched_sha256=caduceus.sha(patched),
            restore_sha256=caduceus.sha(restore),
            bytes=len(patched),
            camera_name=cam.name,
            camera_contacted=False,
            checks=checked,
        )
        meta = (json.dumps(info, indent=2) + '\n').encode('utf-8')
        (staging / 'build.json').write_bytes(meta)
        hashes = {
            cam.card_name: info['patched_sha256'],
            'restore-stock.pkg.bin': info['restore_sha256'],
            'edits.json': info['spec_sha256'],
            'build.json': caduceus.sha(meta),
        }
        for name, data in card.items():
            path = staging / 'card' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            hashes[f'card/{name}'] = caduceus.sha(data)
        sums = ''.join(f'{hashes[name]}  {name}\n' for name in sorted(hashes))
        (staging / 'SHA256SUMS').write_text(sums, encoding='utf-8', newline='\n')
        staging.rename(destination)
    print(f'Sealed {destination} from OM catalog stock')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', type=Path, required=True)
    parser.add_argument('--version', choices=(VERSION, COLOR_CREATOR_VERSION), default=VERSION)
    args = parser.parse_args()
    try:
        seal(args.stock, args.version)
    except (OSError, ValueError, caduceus.Refuse, subprocess.CalledProcessError) as error:
        sys.exit(f'error: {error}')
