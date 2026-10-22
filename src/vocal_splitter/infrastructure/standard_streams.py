"""Compatibility with dependencies that expect console streams in a GUI app."""

import os
import sys


def ensure_standard_streams() -> None:
    """Provide missing outputs before dependencies capture them during import.

    Windows GUI executables and pythonw set these streams to None. Keep valid
    console/redirection streams intact; application diagnostics use file logging.
    The replacements stay referenced by sys for the lifetime of the process.
    """
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")
