"""Regression checks for published and locally generated release manifests."""

from contextlib import redirect_stdout
import io
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
import zlib

from caduceus import (
    EM1MK2_CATALOG_STOCK_SHA, Refuse, cmd_verify, copy_to_card, em1mk2_looks_ok, get_camera, latest_release,
    load_release, release_package_hashes, release_stock_hash, releases, vkey,
)


class ReleaseTests(unittest.TestCase):
    def test_verify_rejects_empty_manifest(self):
        with TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / 'SHA256SUMS').write_text('\n', encoding='utf-8')
            with self.assertRaisesRegex(Refuse, 'contains no file checksums'):
                cmd_verify(SimpleNamespace(dir=directory))

    def test_latest_em1_release_uses_numeric_revision(self):
        self.assertIn('em1mk2/v0.4c13', releases('em1mk2'))
        self.assertIn('em1mk2/v0.4c15', releases('em1mk2'))
        self.assertGreaterEqual(vkey(latest_release('em1mk2')), vkey('em1mk2/v0.4c15'))
        self.assertLess(vkey('em1mk2/v0.4c9'), vkey('em1mk2/v0.4c13'))
        self.assertLess(vkey('v0.31'), vkey('v0.31c'))

    def test_catalog_stock_pin_is_scoped_to_the_release_and_body(self):
        legacy, _, _, em1 = load_release('v0.4c15', 'em1mk2')
        catalog = {**legacy, 'stock_sha256': EM1MK2_CATALOG_STOCK_SHA}
        self.assertEqual(release_stock_hash(legacy, em1), get_camera('em1mk2').stock_sha)
        self.assertEqual(release_stock_hash(catalog, em1), EM1MK2_CATALOG_STOCK_SHA)
        with self.assertRaises(Refuse):
            release_stock_hash(catalog, get_camera('ep7'))

    def test_catalog_release_preserves_edits_and_seals_its_own_restore(self):
        legacy, _, legacy_card, _ = load_release('v0.4c15', 'em1mk2')
        catalog, sums, catalog_card, cam = load_release('v0.4c16', 'em1mk2')
        self.assertEqual(catalog['edits'][1:], legacy['edits'])
        self.assertEqual(catalog['edits'][0]['addr'], '0x60042b4d')
        self.assertEqual(catalog_card, legacy_card)
        self.assertEqual(cam.stock_sha, EM1MK2_CATALOG_STOCK_SHA)
        self.assertEqual(sums['restore-stock.pkg.bin'], cam.stock_sha)

    def test_em1_card_copy_keeps_only_a_pack_the_camera_can_read(self):
        _, _, card, cam = load_release('v0.4c17', 'em1mk2')
        bundled = card[f'{cam.mod_dir}/LOOKS.BIN']
        self.assertTrue(em1mk2_looks_ok(bundled))
        damaged = bytearray(bundled)
        damaged[-1] ^= 1
        legacy_em1b = b'EM1B' + bytes(2076)            # the retired v0.1-v0.3 file, 2,080 bytes
        user_pack = bytearray(bundled[:64 + 64])       # a valid one-look pack that differs from the bundled one
        user_pack[12:16] = (64).to_bytes(4, 'little')
        user_pack[24:26] = (1).to_bytes(2, 'little')
        user_pack[16:20] = (zlib.crc32(bytes(user_pack[:16] + user_pack[20:])) & 0xffffffff).to_bytes(4, 'little')
        self.assertTrue(em1mk2_looks_ok(bytes(user_pack)))
        for existing, kept in ((bytes(user_pack), True), (bytes(damaged), False), (legacy_em1b, False)):
            with self.subTest(size=len(existing), kept=kept), TemporaryDirectory() as tmp:
                build, sd = Path(tmp, 'build'), Path(tmp, 'sd')
                (build / 'DCOLYMP').mkdir(parents=True)
                (build / 'DCOLYMP' / cam.card_name).write_bytes(b'update')
                (build / cam.mod_dir).mkdir()
                (build / cam.mod_dir / 'LOOKS.BIN').write_bytes(bundled)
                (sd / cam.mod_dir).mkdir(parents=True)
                (sd / cam.mod_dir / 'LOOKS.BIN').write_bytes(existing)
                with redirect_stdout(io.StringIO()):
                    copy_to_card(build, sd, cam)
                self.assertEqual((sd / cam.mod_dir / 'LOOKS.BIN').read_bytes(), existing if kept else bundled)

    def test_accepts_camera_and_legacy_package_names(self):
        for release, camera, patched_key in (
            ('v0.4c15', 'em1mk2', 'E1259999.BIN'),
            ('v0.31c', 'ep7', 'patched.pkg.bin'),
        ):
            with self.subTest(release=release):
                _, sums, card, cam = load_release(release, camera)
                self.assertIn(f'{cam.mod_dir}/LOOKS.BIN', card)
                self.assertEqual(release_package_hashes(sums, cam), {
                    cam.update_path: sums[patched_key],
                    cam.restore_path: sums['restore-stock.pkg.bin'],
                })


if __name__ == '__main__':
    unittest.main()
