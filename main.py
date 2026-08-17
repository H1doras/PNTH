"""
SoundWave Player — entry point.

Run with:
    python main.py
"""

from config.settings import apply_theme
from views.music_player import MusicPlayer


def main():
    apply_theme()
    app = MusicPlayer()
    app.mainloop()


if __name__ == "__main__":
    main()
