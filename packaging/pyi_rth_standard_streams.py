"""Initialize outputs before PyInstaller's dependency runtime hooks run."""

from vocal_splitter.infrastructure.standard_streams import ensure_standard_streams

ensure_standard_streams()
