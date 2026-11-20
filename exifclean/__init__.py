"""exifclean: strip the metadata, keep the picture."""

from .core import clean, read_metadata

__version__ = "0.1.0"
__all__ = ["clean", "read_metadata"]
