# Contributing

exifclean is one small job: read the metadata, or strip it. Keep it that way.

Rules:

- One function does one thing. Few comments, and only where the code is not obvious.
- Never break the JSON contract: `--list` prints JSON, `clean` prints JSON.
- Add a test in `tests/test_exifclean.py` for anything new.
- Run `python -m unittest discover -s tests` before opening a PR.

That's it.
