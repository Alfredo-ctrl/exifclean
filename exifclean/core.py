"""Read or strip image metadata. The pixels stay, everything else goes."""

from pathlib import Path

from PIL import Image, ImageOps
from PIL.ExifTags import TAGS

_FORMATS = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP"}


def _json_safe(value):
    # EXIF values come in all shapes, make them JSON-friendly
    if isinstance(value, bytes):
        if len(value) > 200:
            return f"<{len(value)} bytes>"
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            return value.hex()
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_safe(v) for v in value]
    if hasattr(value, "numerator") and hasattr(value, "denominator"):
        return float(value)  # IFDRational and friends
    return value


def read_metadata(path):
    """Everything Pillow knows about the file, as plain data."""
    with Image.open(path) as img:
        img.load()
        meta = {
            "file": str(path),
            "format": img.format,
            "mode": img.mode,
            "size": list(img.size),
            "exif": {},
            "info": {},
        }
        for tag_id, value in img.getexif().items():
            meta["exif"][TAGS.get(tag_id, str(tag_id))] = _json_safe(value)
        for key, value in img.info.items():
            if key == "exif":
                continue  # already in "exif" above
            meta["info"][str(key)] = _json_safe(value)
        return meta


def clean(path, output=None, in_place=False):
    """Strip every bit of metadata, keep the pixels exactly as they look."""
    if in_place and output:
        raise ValueError("pick one: --in-place or -o, not both")
    src = Path(path)
    if output is None:
        output = src if in_place else src.with_name(f"{src.stem}_clean{src.suffix}")
    output = Path(output)
    with Image.open(src) as img:
        img.load()
        fmt = img.format or _FORMATS.get(src.suffix.lower())
        if fmt not in ("JPEG", "PNG", "WEBP"):
            raise ValueError(f"exifclean handles JPG, PNG and WebP, not {fmt or 'this file'}")
        removed_exif = len(img.getexif())
        removed_info = len([k for k in img.info if k != "exif"])
        # apply the orientation tag first, or the picture comes out sideways
        img = ImageOps.exif_transpose(img)
        # rebuild from pixels only: no exif, no text chunks, no profiles
        fresh = Image.new(img.mode, img.size)
        if img.mode == "P" and img.getpalette():
            fresh.putpalette(img.getpalette())
        fresh.putdata(list(img.getdata()))
        if img.mode == "P" and "transparency" in img.info:
            fresh.info["transparency"] = img.info["transparency"]
        fresh.save(output, format=fmt)
        return {
            "output": str(output),
            "format": fmt,
            "size": list(fresh.size),
            "removed_exif_tags": removed_exif,
            "removed_info_keys": removed_info,
        }
