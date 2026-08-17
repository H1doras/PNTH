"""
App-wide configuration: theme colors, fonts, and constants.
Kept separate from UI/logic code so the look-and-feel can be tweaked
in one place without touching views/.
"""

import customtkinter as ctk

# ----------------------------------------------------------------------
# THEME - SoundCloud inspired palette
# ----------------------------------------------------------------------
BG_DARK = "#121212"
BG_PANEL = "#1c1c1c"
BG_CARD = "#232323"
BG_CARD_HOVER = "#2c2c2c"
ORANGE = "#ff5500"
ORANGE_HOVER = "#ff7733"
TEXT_MAIN = "#ffffff"
TEXT_DIM = "#a8a8a8"

# ----------------------------------------------------------------------
# APP
# ----------------------------------------------------------------------
APP_TITLE = "SoundWave Player"
APP_GEOMETRY = "880x600"
APP_MIN_SIZE = (760, 540)

SUPPORTED_EXTS = (".mp3", ".wav", ".ogg", ".flac")

DEFAULT_VOLUME = 0.7


def apply_theme():
    """Call once at startup before creating any CTk widgets."""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")  # base theme; colors overridden manually
