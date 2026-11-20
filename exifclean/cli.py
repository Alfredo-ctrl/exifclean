"""Command line: strip the metadata, or just show it."""

import argparse
import json
import sys
from pathlib import Path

from .core import clean, read_metadata

VERSION = "0.1.0"


def build_parser():
    p = argparse.ArgumentParser(
        prog="exifclean",
        description="Strip metadata (EXIF and friends) from images, or list it.",
    )
    p.add_argument("input", help="Image file (JPG, PNG or WebP)")
    p.add_argument("-o", "--output", help="Where to write the clean file (default: <name>_clean.<ext>)")
    p.add_argument("--in-place", action="store_true", help="Overwrite the input file instead of making a copy")
    p.add_argument("--list", action="store_true", help="Show the metadata as JSON and don't write anything")
    p.add_argument("--version", action="version", version=f"exifclean {VERSION}")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    src = Path(args.input)
    if not src.is_file():
        print(f"exifclean: no such file: {src}", file=sys.stderr)
        return 2
    if args.list:
        print(json.dumps(read_metadata(src), indent=2))
        return 0
    try:
        result = clean(src, output=args.output, in_place=args.in_place)
    except ValueError as e:
        print(f"exifclean: {e}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
