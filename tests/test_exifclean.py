import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image
from PIL.PngImagePlugin import PngInfo

from exifclean import clean, read_metadata


def _exif(make="TestCamera", model="TestModel", orientation=None):
    exif = Image.Exif()
    exif[271] = make
    exif[272] = model
    exif[306] = "2026:11:19 12:00:00"
    if orientation is not None:
        exif[274] = orientation
    return exif


class TestExifclean(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _jpg(self, name="photo.jpg", size=(40, 30), color=(200, 100, 50), **exif_kw):
        path = self.dir / name
        Image.new("RGB", size, color).save(path, exif=_exif(**exif_kw))
        return path

    def test_list_shows_exif(self):
        src = self._jpg()
        meta = read_metadata(src)
        self.assertEqual(meta["format"], "JPEG")
        self.assertEqual(meta["exif"]["Make"], "TestCamera")
        self.assertEqual(meta["exif"]["Model"], "TestModel")

    def test_clean_removes_exif(self):
        src = self._jpg()
        out = self.dir / "clean.jpg"
        result = clean(src, output=out)
        self.assertTrue(out.is_file())
        self.assertGreaterEqual(result["removed_exif_tags"], 3)
        self.assertEqual(read_metadata(out)["exif"], {})

    def test_clean_keeps_pixels(self):
        # PNG is lossless, so the pixels must come out byte-identical
        src = self.dir / "pic.png"
        Image.new("RGB", (20, 20), (10, 20, 30)).save(src)
        out = self.dir / "clean.png"
        clean(src, output=out)
        self.assertEqual(
            list(Image.open(src).getdata()),
            list(Image.open(out).getdata()),
        )

    def test_orientation_is_applied(self):
        # orientation 6 means "rotate 90 clockwise", so the size must flip
        src = self._jpg(size=(30, 40), orientation=6)
        out = self.dir / "clean.jpg"
        result = clean(src, output=out)
        self.assertEqual(result["size"], [40, 30])
        self.assertEqual(read_metadata(out)["exif"], {})

    def test_png_text_chunks_stripped(self):
        src = self.dir / "pic.png"
        info = PngInfo()
        info.add_text("Comment", "hello there")
        Image.new("RGB", (20, 20), (1, 2, 3)).save(src, pnginfo=info)
        self.assertEqual(read_metadata(src)["info"]["Comment"], "hello there")
        out = self.dir / "clean.png"
        result = clean(src, output=out)
        self.assertGreaterEqual(result["removed_info_keys"], 1)
        self.assertEqual(read_metadata(out)["info"], {})

    def test_webp_roundtrip(self):
        src = self.dir / "clip.webp"
        Image.new("RGB", (24, 24), (9, 9, 9)).save(src, exif=_exif().tobytes())
        out = self.dir / "clean.webp"
        result = clean(src, output=out)
        self.assertEqual(result["format"], "WEBP")
        self.assertEqual(read_metadata(out)["exif"], {})

    def test_in_place(self):
        src = self._jpg()
        clean(src, in_place=True)
        self.assertEqual(read_metadata(src)["exif"], {})

    def test_clean_refuses_both_output_and_in_place(self):
        src = self._jpg()
        with self.assertRaises(ValueError):
            clean(src, output=self.dir / "x.jpg", in_place=True)

    def test_unsupported_format_errors(self):
        src = self.dir / "anim.gif"
        Image.new("RGB", (10, 10)).save(src)
        with self.assertRaises(ValueError):
            clean(src, output=self.dir / "out.gif")

    def test_cli_list(self):
        src = self._jpg()
        r = subprocess.run(
            [sys.executable, "-m", "exifclean.cli", str(src), "--list"],
            capture_output=True, text=True,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        payload = json.loads(r.stdout)
        self.assertEqual(payload["exif"]["Make"], "TestCamera")

    def test_cli_clean(self):
        src = self._jpg()
        out = self.dir / "done.jpg"
        r = subprocess.run(
            [sys.executable, "-m", "exifclean.cli", str(src), "-o", str(out)],
            capture_output=True, text=True,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        payload = json.loads(r.stdout)
        self.assertEqual(payload["output"], str(out))
        self.assertTrue(out.is_file())

    def test_cli_missing_file(self):
        r = subprocess.run(
            [sys.executable, "-m", "exifclean.cli", str(self.dir / "nope.jpg"), "--list"],
            capture_output=True, text=True,
        )
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
