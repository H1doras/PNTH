"""
Track model: represents a single audio file in the playlist.
"""

import os


def format_time(seconds: float) -> str:
    """Format a seconds value as M:SS for display."""
    if seconds is None or seconds < 0:
        seconds = 0
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


class Track:
    """A single playable audio file."""

    def __init__(self, path: str):
        self.path = path
        self.name = os.path.splitext(os.path.basename(path))[0]
        self.length = 0.0  # seconds, filled in lazily on first play
