"""
SoundCloud-style Music Player window.

Built with CustomTkinter (UI) and pygame (audio engine).
"""

import time
import os
import customtkinter as ctk
from tkinter import filedialog
import pygame

from config.settings import (
    BG_DARK, BG_PANEL, BG_CARD, BG_CARD_HOVER,
    ORANGE, ORANGE_HOVER, TEXT_MAIN, TEXT_DIM,
    APP_TITLE, APP_GEOMETRY, APP_MIN_SIZE,
    SUPPORTED_EXTS, DEFAULT_VOLUME,
)
from views.track import Track, format_time


class MusicPlayer(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ---- pygame audio init ----
        pygame.mixer.init()
        pygame.mixer.music.set_volume(DEFAULT_VOLUME)

        # ---- window setup ----
        self.title(APP_TITLE)
        self.geometry(APP_GEOMETRY)
        self.minsize(*APP_MIN_SIZE)
        self.configure(fg_color=BG_DARK)

        # ---- state ----
        self.playlist = []          # list[Track]
        self.current_index = None
        self.is_playing = False
        self.is_paused = False
        self.track_length = 0.0
        self.seek_lock = False      # prevents progress loop from fighting user drag
        self.start_offset = 0.0     # seconds already elapsed when (re)starting playback
        self.play_started_at = None  # time.time() reference

        self._build_layout()
        self._poll_progress()

    # ------------------------------------------------------------------
    # LAYOUT
    # ------------------------------------------------------------------
    def _build_layout(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._build_sidebar()
        self._build_main_area()
        self._build_bottom_bar()

    # ---- Sidebar ----
    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=210, fg_color=BG_PANEL, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.grid_propagate(False)

        logo = ctk.CTkLabel(
            sidebar, text="SoundWave", font=ctk.CTkFont(size=22, weight="bold"),
            text_color=ORANGE
        )
        logo.pack(anchor="w", padx=20, pady=(24, 30))

        add_files_btn = ctk.CTkButton(
            sidebar, text="＋  Add Files", command=self.add_files,
            fg_color=BG_CARD, hover_color=BG_CARD_HOVER, text_color=TEXT_MAIN,
            anchor="w", height=38, corner_radius=8
        )
        add_files_btn.pack(fill="x", padx=16, pady=4)

        add_folder_btn = ctk.CTkButton(
            sidebar, text="📁  Add Folder", command=self.add_folder,
            fg_color=BG_CARD, hover_color=BG_CARD_HOVER, text_color=TEXT_MAIN,
            anchor="w", height=38, corner_radius=8
        )
        add_folder_btn.pack(fill="x", padx=16, pady=4)

        clear_btn = ctk.CTkButton(
            sidebar, text="🗑  Clear Playlist", command=self.clear_playlist,
            fg_color=BG_CARD, hover_color=BG_CARD_HOVER, text_color=TEXT_MAIN,
            anchor="w", height=38, corner_radius=8
        )
        clear_btn.pack(fill="x", padx=16, pady=4)

        # Volume control
        vol_label = ctk.CTkLabel(sidebar, text="Volume", text_color=TEXT_DIM,
                                  font=ctk.CTkFont(size=12))
        vol_label.pack(anchor="w", padx=20, pady=(30, 4))

        self.volume_slider = ctk.CTkSlider(
            sidebar, from_=0, to=1, number_of_steps=100,
            command=self.on_volume_change, progress_color=ORANGE,
            button_color=ORANGE, button_hover_color=ORANGE_HOVER,
            fg_color=BG_CARD
        )
        self.volume_slider.set(DEFAULT_VOLUME)
        self.volume_slider.pack(fill="x", padx=20, pady=(0, 20))

    # ---- Main area: playlist ----
    def _build_main_area(self):
        main = ctk.CTkFrame(self, fg_color=BG_DARK, corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(
            main, text="Your Tracks", font=ctk.CTkFont(size=20, weight="bold"),
            text_color=TEXT_MAIN, anchor="w"
        )
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 10))

        self.playlist_frame = ctk.CTkScrollableFrame(
            main, fg_color=BG_DARK, corner_radius=0,
            scrollbar_button_color=BG_CARD, scrollbar_button_hover_color=BG_CARD_HOVER
        )
        self.playlist_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 10))
        self.playlist_frame.grid_columnconfigure(0, weight=1)

        self.empty_label = ctk.CTkLabel(
            self.playlist_frame,
            text="No tracks yet.\nClick “Add Files” or “Add Folder” to get started.",
            text_color=TEXT_DIM, justify="center"
        )
        self.empty_label.grid(row=0, column=0, pady=60)

        self.track_row_widgets = []  # keep references to rebuild highlight state

    # ---- Bottom playback bar ----
    def _build_bottom_bar(self):
        bar = ctk.CTkFrame(self, height=110, fg_color=BG_PANEL, corner_radius=0)
        bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        bar.grid_propagate(False)
        bar.grid_columnconfigure(1, weight=1)

        # Now playing info
        info_frame = ctk.CTkFrame(bar, fg_color="transparent")
        info_frame.grid(row=0, column=0, rowspan=2, sticky="w", padx=20, pady=10)

        self.cover_label = ctk.CTkLabel(
            info_frame, text="♪", width=56, height=56, corner_radius=8,
            fg_color=BG_CARD, text_color=ORANGE, font=ctk.CTkFont(size=24, weight="bold")
        )
        self.cover_label.grid(row=0, column=0, rowspan=2, padx=(0, 12))

        self.now_playing_title = ctk.CTkLabel(
            info_frame, text="No track selected", text_color=TEXT_MAIN,
            font=ctk.CTkFont(size=14, weight="bold"), anchor="w"
        )
        self.now_playing_title.grid(row=0, column=1, sticky="w")

        self.now_playing_sub = ctk.CTkLabel(
            info_frame, text="—", text_color=TEXT_DIM,
            font=ctk.CTkFont(size=12), anchor="w"
        )
        self.now_playing_sub.grid(row=1, column=1, sticky="w")

        # Center: transport controls + progress bar
        center_frame = ctk.CTkFrame(bar, fg_color="transparent")
        center_frame.grid(row=0, column=1, rowspan=2, sticky="ew", padx=10, pady=8)
        center_frame.grid_columnconfigure(0, weight=1)

        controls_frame = ctk.CTkFrame(center_frame, fg_color="transparent")
        controls_frame.grid(row=0, column=0, pady=(0, 6))

        self.prev_btn = ctk.CTkButton(
            controls_frame, text="⏮", width=42, height=36, font=ctk.CTkFont(size=16),
            command=self.play_previous, fg_color="transparent", hover_color=BG_CARD,
            text_color=TEXT_MAIN
        )
        self.prev_btn.grid(row=0, column=0, padx=6)

        self.play_btn = ctk.CTkButton(
            controls_frame, text="▶", width=48, height=48, corner_radius=24,
            font=ctk.CTkFont(size=18, weight="bold"),
            command=self.toggle_play, fg_color=ORANGE, hover_color=ORANGE_HOVER,
            text_color="#ffffff"
        )
        self.play_btn.grid(row=0, column=1, padx=10)

        self.next_btn = ctk.CTkButton(
            controls_frame, text="⏭", width=42, height=36, font=ctk.CTkFont(size=16),
            command=self.play_next, fg_color="transparent", hover_color=BG_CARD,
            text_color=TEXT_MAIN
        )
        self.next_btn.grid(row=0, column=2, padx=6)

        self.stop_btn = ctk.CTkButton(
            controls_frame, text="⏹", width=42, height=36, font=ctk.CTkFont(size=14),
            command=self.stop_playback, fg_color="transparent", hover_color=BG_CARD,
            text_color=TEXT_MAIN
        )
        self.stop_btn.grid(row=0, column=3, padx=6)

        # Progress row
        progress_row = ctk.CTkFrame(center_frame, fg_color="transparent")
        progress_row.grid(row=1, column=0, sticky="ew")
        progress_row.grid_columnconfigure(1, weight=1)

        self.current_time_label = ctk.CTkLabel(
            progress_row, text="0:00", text_color=TEXT_DIM, font=ctk.CTkFont(size=11), width=40
        )
        self.current_time_label.grid(row=0, column=0, padx=(0, 6))

        self.progress_slider = ctk.CTkSlider(
            progress_row, from_=0, to=100, number_of_steps=1000,
            command=self.on_seek_drag, progress_color=ORANGE,
            button_color=ORANGE, button_hover_color=ORANGE_HOVER,
            fg_color=BG_CARD, height=14
        )
        self.progress_slider.set(0)
        self.progress_slider.grid(row=0, column=1, sticky="ew")
        self.progress_slider.bind("<ButtonPress-1>", self._on_seek_press)
        self.progress_slider.bind("<ButtonRelease-1>", self._on_seek_release)

        self.total_time_label = ctk.CTkLabel(
            progress_row, text="0:00", text_color=TEXT_DIM, font=ctk.CTkFont(size=11), width=40
        )
        self.total_time_label.grid(row=0, column=2, padx=(6, 0))

    # ------------------------------------------------------------------
    # PLAYLIST MANAGEMENT
    # ------------------------------------------------------------------
    def add_files(self):
        paths = filedialog.askopenfilenames(
            title="Select audio files",
            filetypes=[("Audio Files", "*.mp3 *.wav *.ogg *.flac"), ("All Files", "*.*")]
        )
        if paths:
            for p in paths:
                if p.lower().endswith(SUPPORTED_EXTS):
                    self.playlist.append(Track(p))
            self._refresh_playlist_ui()

    def add_folder(self):
        folder = filedialog.askdirectory(title="Select a folder of audio files")
        if folder:
            for fname in sorted(os.listdir(folder)):
                if fname.lower().endswith(SUPPORTED_EXTS):
                    self.playlist.append(Track(os.path.join(folder, fname)))
            self._refresh_playlist_ui()

    def clear_playlist(self):
        self.stop_playback()
        self.playlist.clear()
        self.current_index = None
        self._refresh_playlist_ui()
        self.now_playing_title.configure(text="No track selected")
        self.now_playing_sub.configure(text="—")

    def _refresh_playlist_ui(self):
        for w in self.playlist_frame.winfo_children():
            w.destroy()
        self.track_row_widgets = []

        if not self.playlist:
            self.empty_label = ctk.CTkLabel(
                self.playlist_frame,
                text="No tracks yet.\nClick “Add Files” or “Add Folder” to get started.",
                text_color=TEXT_DIM, justify="center"
            )
            self.empty_label.grid(row=0, column=0, pady=60)
            return

        for idx, track in enumerate(self.playlist):
            row = self._build_track_row(idx, track)
            self.track_row_widgets.append(row)

    def _build_track_row(self, idx, track):
        is_current = (idx == self.current_index)
        row_bg = BG_CARD if not is_current else "#3a2010"

        row = ctk.CTkFrame(self.playlist_frame, fg_color=row_bg, corner_radius=8, height=52)
        row.grid(row=idx, column=0, sticky="ew", pady=4, padx=2)
        row.grid_columnconfigure(1, weight=1)

        icon = "▶" if is_current and self.is_playing else "♪"
        icon_color = ORANGE if is_current else TEXT_DIM

        icon_label = ctk.CTkLabel(row, text=icon, text_color=icon_color, width=30,
                                   font=ctk.CTkFont(size=14))
        icon_label.grid(row=0, column=0, padx=(12, 4), pady=10)

        title_label = ctk.CTkLabel(
            row, text=track.name, text_color=(ORANGE if is_current else TEXT_MAIN),
            anchor="w", font=ctk.CTkFont(size=13, weight="bold" if is_current else "normal")
        )
        title_label.grid(row=0, column=1, sticky="ew", pady=10)

        remove_btn = ctk.CTkButton(
            row, text="✕", width=28, height=28, fg_color="transparent",
            hover_color="#4a2a1a", text_color=TEXT_DIM,
            command=lambda i=idx: self.remove_track(i)
        )
        remove_btn.grid(row=0, column=2, padx=10)

        # Clicking anywhere on the row (except remove button) plays the track
        for widget in (row, icon_label, title_label):
            widget.bind("<Button-1>", lambda e, i=idx: self.play_track(i))

        return row

    def remove_track(self, idx):
        was_current = (idx == self.current_index)
        self.playlist.pop(idx)
        if was_current:
            self.stop_playback()
            self.current_index = None
        elif self.current_index is not None and idx < self.current_index:
            self.current_index -= 1
        self._refresh_playlist_ui()

    # ------------------------------------------------------------------
    # PLAYBACK CONTROL
    # ------------------------------------------------------------------
    def play_track(self, idx):
        if idx < 0 or idx >= len(self.playlist):
            return
        track = self.playlist[idx]
        try:
            pygame.mixer.music.load(track.path)
        except Exception as e:
            self.now_playing_sub.configure(text=f"Error loading file: {e}")
            return

        self.current_index = idx
        self.start_offset = 0.0
        pygame.mixer.music.play()
        self.play_started_at = time.time()
        self.is_playing = True
        self.is_paused = False

        self.track_length = self._get_track_length(track)
        self.total_time_label.configure(text=format_time(self.track_length))
        self.progress_slider.configure(to=max(self.track_length, 1))
        self.progress_slider.set(0)

        self.now_playing_title.configure(text=track.name)
        self.now_playing_sub.configure(text="Playing")
        self.play_btn.configure(text="⏸")

        self._refresh_playlist_ui()

    def _get_track_length(self, track: Track):
        if track.length:
            return track.length
        try:
            snd = pygame.mixer.Sound(track.path)
            track.length = snd.get_length()
        except Exception:
            track.length = 0.0
        return track.length

    def toggle_play(self):
        if self.current_index is None:
            if self.playlist:
                self.play_track(0)
            return

        if self.is_playing and not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.is_playing = False
            self.play_btn.configure(text="▶")
            self.now_playing_sub.configure(text="Paused")
            # Freeze elapsed time
            self.start_offset += time.time() - self.play_started_at
        else:
            pygame.mixer.music.unpause()
            self.is_paused = False
            self.is_playing = True
            self.play_started_at = time.time()
            self.play_btn.configure(text="⏸")
            self.now_playing_sub.configure(text="Playing")

    def stop_playback(self):
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        self.start_offset = 0.0
        self.play_btn.configure(text="▶")
        self.progress_slider.set(0)
        self.current_time_label.configure(text="0:00")
        if self.current_index is not None:
            self.now_playing_sub.configure(text="Stopped")

    def play_next(self):
        if not self.playlist:
            return
        nxt = 0 if self.current_index is None else (self.current_index + 1) % len(self.playlist)
        self.play_track(nxt)

    def play_previous(self):
        if not self.playlist:
            return
        prev = 0 if self.current_index is None else (self.current_index - 1) % len(self.playlist)
        self.play_track(prev)

    def on_volume_change(self, value):
        pygame.mixer.music.set_volume(float(value))

    # ---- Seeking ----
    def _on_seek_press(self, event):
        self.seek_lock = True

    def _on_seek_release(self, event):
        if self.current_index is None:
            self.seek_lock = False
            return
        target = self.progress_slider.get()
        try:
            pygame.mixer.music.play(start=target)
            self.start_offset = target
            self.play_started_at = time.time()
            self.is_playing = True
            self.is_paused = False
            self.play_btn.configure(text="⏸")
            self.now_playing_sub.configure(text="Playing")
        except Exception:
            pass
        self.seek_lock = False

    def on_seek_drag(self, value):
        # Update the time label live while dragging; actual seek happens on release
        self.current_time_label.configure(text=format_time(float(value)))

    # ------------------------------------------------------------------
    # PROGRESS LOOP
    # ------------------------------------------------------------------
    def _poll_progress(self):
        if self.is_playing and not self.seek_lock and self.current_index is not None:
            elapsed = self.start_offset + (time.time() - self.play_started_at)

            if self.track_length and elapsed >= self.track_length:
                # Track finished -> auto-advance
                self.play_next()
            else:
                self.progress_slider.set(min(elapsed, self.track_length or elapsed))
                self.current_time_label.configure(text=format_time(elapsed))
                if not pygame.mixer.music.get_busy() and not self.is_paused:
                    # Song ended naturally (get_busy() becomes False)
                    self.play_next()

        self.after(300, self._poll_progress)
