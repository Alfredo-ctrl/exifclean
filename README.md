# exifclean

Strip the metadata out of an image — EXIF, text chunks, profiles — and keep the pixels. A CLI built for AI agents: any agent can drive it — Muse, Antigravity, Codex, Claude Code, or a local model.

## Install

```sh
pip install exifclean
```

Needs Python 3.10+ and Pillow.

## Use it

```sh
# see what's inside, as JSON
exifclean photo.jpg --list

# strip it, save next to the original
exifclean photo.jpg
# -> photo_clean.jpg

# overwrite the original
exifclean photo.jpg --in-place
```

JPG, PNG and WebP. The orientation tag is applied before stripping, so the picture looks the same afterwards. Output is JSON, so it is easy to parse.

## Use it from Python

```python
from exifclean import clean, read_metadata

print(read_metadata("photo.jpg"))
clean("photo.jpg", output="photo_clean.jpg")
```

## License

MIT
