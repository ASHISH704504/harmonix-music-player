import os
import random
import math
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional, List, Dict
import customtkinter as ctk
from PIL import Image

from audio_engine import AudioEngine, PlaybackState, PlayMode
from library_manager import LibraryManager
from metadata_manager import TrackMetadata, create_placeholder_cover
from retro_theme import RetroTheme as RT


ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class MusicPlayerGUI(ctk.CTk):
    """Gen-Z Dark Minimalistic Retro-Fusion Desktop Player."""

    def __init__(self):
        super().__init__()

        self.title("[ HARMONIX // CYBER_DECK_V2 ]")
        self.geometry("1220x820")
        self.minsize(1000, 700)
        self.configure(fg_color=RT.BG_VOID)

        # Managers
        self.library_manager = LibraryManager()
        self.engine = AudioEngine(library_manager=self.library_manager)

        # Active Navigation View State
        # Views: "ALL", "LIKED", "RECENT", "PLAYLIST", "ALBUM"
        self.current_view_type = "ALL"
        self.active_target_name: Optional[str] = None

        self.search_query = ""
        self.displayed_tracks: List[TrackMetadata] = []

        # Audio Visualizer Bar Progressors (16 Spectrum Bars)
        self.spectrum_bars: List[ctk.CTkProgressBar] = []

        # Build UI Architecture
        self._setup_grid()
        self._build_header_bar()
        self._build_main_split_view()
        self._build_cyber_player_bar()

        # Load initial demo tracks if empty
        self._seed_initial_demo_tracks()

        # Render Table
        self._switch_view("ALL")

        # Bind periodic update loop (100ms for smooth VU meter animation!)
        self.after(100, self._periodic_update)

    def _setup_grid(self):
        self.grid_rowconfigure(0, weight=0) # Header
        self.grid_rowconfigure(1, weight=1) # Split View Area
        self.grid_rowconfigure(2, weight=0) # Player Bar
        self.grid_columnconfigure(0, weight=1)

    def _seed_initial_demo_tracks(self):
        demo_dir = os.path.join(os.path.dirname(__file__), "demo_music")
        if os.path.exists(demo_dir):
            demo_files = [os.path.join(demo_dir, f) for f in os.listdir(demo_dir) if f.endswith(".wav")]
            if demo_files and not self.engine.playlist:
                self.engine.add_tracks(demo_files)

    # ==========================================
    # 1. TOP RETRO HEADER BAR
    # ==========================================
    def _build_header_bar(self):
        self.header_frame = ctk.CTkFrame(self, height=54, corner_radius=0, fg_color=RT.BG_VOID)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 10))
        self.header_frame.grid_columnconfigure(1, weight=1)

        # Brand Tag
        brand_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        brand_box.grid(row=0, column=0, sticky="w")

        logo_lbl = ctk.CTkLabel(
            brand_box,
            text="[ HARMONIX // RETRO_DECK ]",
            font=ctk.CTkFont(family="Courier", size=18, weight="bold"),
            text_color=RT.NEON_PURPLE
        )
        logo_lbl.pack(side="left", padx=(0, 15))

        status_lbl = ctk.CTkLabel(
            brand_box,
            text="● AUDIO_ONLINE",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=RT.NEON_LIME
        )
        status_lbl.pack(side="left")

        # Live Search & Action Buttons (Right)
        actions_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        actions_box.grid(row=0, column=2, sticky="e")

        self.search_entry = ctk.CTkEntry(
            actions_box,
            placeholder_text="🔍 SEARCH_TRACKS...",
            font=ctk.CTkFont(family="Courier", size=12),
            fg_color=RT.BG_PANEL,
            border_color=RT.NEON_CYAN,
            border_width=1,
            text_color=RT.TEXT_MAIN,
            width=220,
            height=34,
            corner_radius=8
        )
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self._action_search_type)

        ctk.CTkButton(
            actions_box, text="[+ LOAD_FILES]", font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=RT.NEON_PURPLE, hover_color="#7C3AED", text_color="#FFFFFF", height=34, corner_radius=8,
            command=self._action_add_files
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            actions_box, text="[📁 LOAD_FOLDER]", font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=RT.BG_CARD, hover_color=RT.BG_CARD_HOVER, border_color=RT.BORDER_CYBER, border_width=1, text_color=RT.TEXT_MAIN, height=34, corner_radius=8,
            command=self._action_add_folder
        ).pack(side="left", padx=4)

    # ==========================================
    # 2. MAIN SPLIT VIEW (HERO CASSETTE CARD | TRACK LIST)
    # ==========================================
    def _build_main_split_view(self):
        self.split_container = ctk.CTkFrame(self, fg_color="transparent")
        self.split_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 10))
        self.split_container.grid_columnconfigure(0, weight=0) # Left Hero Card (Fixed 340px)
        self.split_container.grid_columnconfigure(1, weight=1) # Right Track Container
        self.split_container.grid_rowconfigure(0, weight=1)

        # --- LEFT: HERO CASSETTE DECK CARD ---
        self.hero_card = ctk.CTkFrame(self.split_container, width=350, fg_color=RT.BG_PANEL, corner_radius=16, border_color=RT.BORDER_CYBER, border_width=1)
        self.hero_card.grid(row=0, column=0, sticky="nsew", padx=(0, 15), pady=0)
        self.hero_card.grid_propagate(False)

        # Cover Image Label
        self.cover_label = ctk.CTkLabel(self.hero_card, text="")
        self.cover_label.pack(padx=20, pady=(20, 10))
        self._update_cover_display(create_placeholder_cover("Aether Deck"))

        # Track Title & Artist Stack
        self.hero_title = ctk.CTkLabel(
            self.hero_card, text="NO_TRACK_PLAYING",
            font=ctk.CTkFont(family="Courier", size=18, weight="bold"),
            text_color=RT.NEON_PURPLE, wraplength=310, anchor="w"
        )
        self.hero_title.pack(fill="x", padx=20, pady=(5, 2))

        self.hero_artist = ctk.CTkLabel(
            self.hero_card, text="LOAD AUDIO TO START",
            font=ctk.CTkFont(size=12), text_color=RT.NEON_PINK, wraplength=310, anchor="w"
        )
        self.hero_artist.pack(fill="x", padx=20, pady=(0, 10))

        # Telemetry Badge Badges
        telemetry_box = ctk.CTkFrame(self.hero_card, fg_color=RT.BG_CARD, corner_radius=10)
        telemetry_box.pack(fill="x", padx=20, pady=(0, 15))

        self.t_bpm = ctk.CTkLabel(telemetry_box, text="[BPM: 124]", font=ctk.CTkFont(family="Courier", size=11), text_color=RT.NEON_CYAN)
        self.t_bpm.grid(row=0, column=0, padx=10, pady=6)

        self.t_fmt = ctk.CTkLabel(telemetry_box, text="[STEREO 320KBPS]", font=ctk.CTkFont(family="Courier", size=11), text_color=RT.NEON_AMBER)
        self.t_fmt.grid(row=0, column=1, padx=10, pady=6)

        # --- LIVE AUDIO SPECTRUM VISUALIZER (16 VU Meter Bars) ---
        viz_hdr = ctk.CTkLabel(self.hero_card, text="[ LIVE_SPECTRUM_ANALYZER ]", font=ctk.CTkFont(family="Courier", size=11, weight="bold"), text_color=RT.TEXT_MUTED)
        viz_hdr.pack(anchor="w", padx=20, pady=(0, 5))

        self.viz_container = ctk.CTkFrame(self.hero_card, fg_color=RT.BG_CARD, corner_radius=10, height=75)
        self.viz_container.pack(fill="x", padx=20, pady=(0, 15))
        self.viz_container.pack_propagate(False)

        # Create 16 vertical progress bars inside container
        self.spectrum_bars.clear()
        for b in range(16):
            bar = ctk.CTkProgressBar(
                self.viz_container, orientation="vertical", width=12,
                progress_color=RT.NEON_PURPLE if b % 2 == 0 else RT.NEON_CYAN,
                fg_color="#12141F"
            )
            bar.pack(side="left", fill="y", expand=True, padx=2, pady=10)
            bar.set(0.1)
            self.spectrum_bars.append(bar)

        # --- RIGHT: TRACK CONTAINER & NAVIGATION TABS ---
        self.right_container = ctk.CTkFrame(self.split_container, fg_color=RT.BG_PANEL, corner_radius=16, border_color=RT.BORDER_CYBER, border_width=1)
        self.right_container.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.right_container.grid_rowconfigure(2, weight=1)
        self.right_container.grid_columnconfigure(0, weight=1)

        # Navigation Pill Tabs
        self.tab_nav_frame = ctk.CTkFrame(self.right_container, fg_color="transparent")
        self.tab_nav_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 5))

        self.tabs_box = ctk.CTkFrame(self.tab_nav_frame, fg_color="transparent")
        self.tabs_box.pack(side="left")

        self.btn_tab_all = self._create_nav_pill(self.tabs_box, "⚡ ALL_TRACKS", lambda: self._switch_view("ALL"), "ALL")
        self.btn_tab_liked = self._create_nav_pill(self.tabs_box, "💖 LIKED_TAPES", lambda: self._switch_view("LIKED"), "LIKED")
        self.btn_tab_recent = self._create_nav_pill(self.tabs_box, "🕒 RECENT_LOGS", lambda: self._switch_view("RECENT"), "RECENT")

        # Sub Action Bar (Create Playlist / Album)
        sub_action_box = ctk.CTkFrame(self.right_container, fg_color="transparent")
        sub_action_box.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 10))

        ctk.CTkButton(
            sub_action_box, text="[+ PLAYLIST]", font=ctk.CTkFont(size=11), width=90, height=26, corner_radius=6,
            fg_color=RT.BG_CARD, hover_color=RT.BG_CARD_HOVER, text_color=RT.NEON_CYAN, border_color=RT.BORDER_CYBER, border_width=1,
            command=self._action_create_playlist
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            sub_action_box, text="[+ ALBUM]", font=ctk.CTkFont(size=11), width=85, height=26, corner_radius=6,
            fg_color=RT.BG_CARD, hover_color=RT.BG_CARD_HOVER, text_color=RT.NEON_PINK, border_color=RT.BORDER_CYBER, border_width=1,
            command=self._action_create_album
        ).pack(side="left")

        # Render custom playlist/album pill tabs dynamically
        self.dynamic_pills_frame = ctk.CTkFrame(sub_action_box, fg_color="transparent")
        self.dynamic_pills_frame.pack(side="left", padx=10)

        # Scrollable Track List Table
        self.track_scroll = ctk.CTkScrollableFrame(self.right_container, fg_color="transparent")
        self.track_scroll.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 15))
        self.track_scroll.grid_columnconfigure(0, weight=1)

    def _create_nav_pill(self, parent, text: str, command, view_key: str):
        is_act = (self.current_view_type == view_key and self.active_target_name is None)
        btn = ctk.CTkButton(
            parent, text=text, font=ctk.CTkFont(family="Courier", size=12, weight="bold" if is_act else "normal"),
            fg_color=RT.NEON_PURPLE if is_act else RT.BG_CARD, hover_color=RT.BG_CARD_HOVER,
            text_color="#FFFFFF" if is_act else RT.TEXT_MUTED, height=32, corner_radius=8,
            command=command
        )
        btn.pack(side="left", padx=4)
        return btn

    # ==========================================
    # 3. BOTTOM CYBER PLAYER BAR
    # ==========================================
    def _build_cyber_player_bar(self):
        self.player_bar = ctk.CTkFrame(self, height=88, corner_radius=0, fg_color=RT.BG_PANEL, border_color=RT.BORDER_CYBER, border_width=1)
        self.player_bar.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        self.player_bar.grid_columnconfigure(0, weight=1)
        self.player_bar.grid_columnconfigure(1, weight=2)
        self.player_bar.grid_columnconfigure(2, weight=1)

        # Left Track Info
        self.mini_info_frame = ctk.CTkFrame(self.player_bar, fg_color="transparent")
        self.mini_info_frame.grid(row=0, column=0, sticky="w", padx=20, pady=10)

        self.mini_cover_label = ctk.CTkLabel(self.mini_info_frame, text="")
        self.mini_cover_label.pack(side="left", padx=(0, 12))
        self._update_mini_cover(create_placeholder_cover("Aether", size=(52, 52)))

        self.mini_text_frame = ctk.CTkFrame(self.mini_info_frame, fg_color="transparent")
        self.mini_text_frame.pack(side="left", anchor="w")

        self.mini_title = ctk.CTkLabel(self.mini_text_frame, text="NO_AUDIO_PLAYING", font=ctk.CTkFont(family="Courier", size=13, weight="bold"), text_color=RT.NEON_PURPLE, anchor="w")
        self.mini_title.pack(anchor="w")

        self.mini_artist = ctk.CTkLabel(self.mini_text_frame, text="CYBER_DECK_V2", font=ctk.CTkFont(size=11), text_color=RT.TEXT_MUTED, anchor="w")
        self.mini_artist.pack(anchor="w")

        self.bar_heart_btn = ctk.CTkButton(
            self.mini_info_frame, text="💖", width=28, height=28, corner_radius=14,
            fg_color="transparent", hover_color=RT.BG_CARD_HOVER, font=ctk.CTkFont(size=13),
            command=self._action_toggle_current_favourite
        )
        self.bar_heart_btn.pack(side="left", padx=8)

        # Center Controls & Seek Bar
        self.center_frame = ctk.CTkFrame(self.player_bar, fg_color="transparent")
        self.center_frame.grid(row=0, column=1, sticky="ew", padx=10, pady=6)

        self.btn_row = ctk.CTkFrame(self.center_frame, fg_color="transparent")
        self.btn_row.pack(pady=(0, 2))

        self.shuffle_btn = ctk.CTkButton(self.btn_row, text="[🔀]", width=34, height=32, corner_radius=6, fg_color="transparent", hover_color=RT.BG_CARD_HOVER, text_color=RT.TEXT_MUTED, font=ctk.CTkFont(size=12), command=self._action_toggle_mode)
        self.shuffle_btn.pack(side="left", padx=3)

        self.prev_btn = ctk.CTkButton(self.btn_row, text="[◄◄]", width=42, height=32, corner_radius=6, fg_color=RT.BG_CARD, hover_color=RT.BG_CARD_HOVER, text_color=RT.TEXT_MAIN, font=ctk.CTkFont(size=12, weight="bold"), command=self._action_previous)
        self.prev_btn.pack(side="left", padx=4)

        # Gradient Electric Purple Play Button
        self.play_btn = ctk.CTkButton(
            self.btn_row, text="[ ▶ PLAY ]", width=90, height=36, corner_radius=8,
            font=ctk.CTkFont(family="Courier", size=13, weight="bold"), fg_color=RT.NEON_PURPLE, hover_color="#7C3AED", text_color="#FFFFFF",
            command=self._action_toggle_play_pause
        )
        self.play_btn.pack(side="left", padx=6)

        self.next_btn = ctk.CTkButton(self.btn_row, text="[NEXT ►►]", width=75, height=32, corner_radius=6, fg_color=RT.BG_CARD, hover_color=RT.BG_CARD_HOVER, text_color=RT.TEXT_MAIN, font=ctk.CTkFont(size=12, weight="bold"), command=self._action_next)
        self.next_btn.pack(side="left", padx=4)

        self.repeat_btn = ctk.CTkButton(self.btn_row, text="[🔁]", width=34, height=32, corner_radius=6, fg_color="transparent", hover_color=RT.BG_CARD_HOVER, text_color=RT.TEXT_MUTED, font=ctk.CTkFont(size=12), command=self._action_toggle_mode)
        self.repeat_btn.pack(side="left", padx=3)

        # Seek Bar
        self.seek_row = ctk.CTkFrame(self.center_frame, fg_color="transparent")
        self.seek_row.pack(fill="x", padx=10)

        self.time_elapsed_label = ctk.CTkLabel(self.seek_row, text="00:00", font=ctk.CTkFont(family="Courier", size=11), text_color=RT.NEON_CYAN, width=45)
        self.time_elapsed_label.pack(side="left", padx=(0, 8))

        self.seek_slider = ctk.CTkSlider(
            self.seek_row, from_=0, to=100, number_of_steps=1000,
            button_color=RT.NEON_CYAN, progress_color=RT.NEON_PURPLE, fg_color="#1F2433", height=12,
            command=self._action_seek_release
        )
        self.seek_slider.pack(side="left", fill="x", expand=True)
        self.seek_slider.set(0)

        self.time_total_label = ctk.CTkLabel(self.seek_row, text="00:00", font=ctk.CTkFont(family="Courier", size=11), text_color=RT.TEXT_MUTED, width=45)
        self.time_total_label.pack(side="right", padx=(8, 0))

        # Right Volume Slider
        self.right_volume_frame = ctk.CTkFrame(self.player_bar, fg_color="transparent")
        self.right_volume_frame.grid(row=0, column=2, sticky="e", padx=20, pady=10)

        self.mute_btn = ctk.CTkButton(self.right_volume_frame, text="🔊", width=32, height=32, corner_radius=16, font=ctk.CTkFont(size=14), fg_color="transparent", hover_color=RT.BG_CARD_HOVER, command=self._action_toggle_mute)
        self.mute_btn.pack(side="left", padx=(0, 4))

        self.volume_slider = ctk.CTkSlider(
            self.right_volume_frame, from_=0.0, to=1.0, number_of_steps=100, width=90,
            button_color=RT.NEON_PURPLE, progress_color=RT.NEON_PINK, fg_color="#1F2433",
            command=self._action_volume_changed
        )
        self.volume_slider.pack(side="left", padx=4)
        self.volume_slider.set(self.engine.volume)

    # ==========================================
    # 4. VIEW RENDERING & SECTIONS
    # ==========================================
    def _switch_view(self, view_type: str, target: Optional[str] = None):
        self.current_view_type = view_type
        self.active_target_name = target

        # Update pill tab styles
        self.btn_tab_all.configure(fg_color=RT.NEON_PURPLE if view_type == "ALL" else RT.BG_CARD, text_color="#FFFFFF" if view_type == "ALL" else RT.TEXT_MUTED)
        self.btn_tab_liked.configure(fg_color=RT.NEON_PURPLE if view_type == "LIKED" else RT.BG_CARD, text_color="#FFFFFF" if view_type == "LIKED" else RT.TEXT_MUTED)
        self.btn_tab_recent.configure(fg_color=RT.NEON_PURPLE if view_type == "RECENT" else RT.BG_CARD, text_color="#FFFFFF" if view_type == "RECENT" else RT.TEXT_MUTED)

        self._render_dynamic_pill_tabs()
        self._render_track_table()

    def _render_dynamic_pill_tabs(self):
        """Renders pill tabs for Playlists and Custom Albums in sub-bar."""
        for w in self.dynamic_pills_frame.winfo_children():
            w.destroy()

        for pl_name in self.library_manager.playlists.keys():
            is_act = (self.current_view_type == "PLAYLIST" and self.active_target_name == pl_name)
            btn = ctk.CTkButton(
                self.dynamic_pills_frame, text=f"📜 {pl_name}", font=ctk.CTkFont(size=11), height=26, corner_radius=6,
                fg_color=RT.NEON_CYAN if is_act else "transparent", hover_color=RT.BG_CARD_HOVER,
                text_color="#000000" if is_act else RT.NEON_CYAN,
                command=lambda name=pl_name: self._switch_view("PLAYLIST", name)
            )
            btn.pack(side="left", padx=2)

        for alb_name in self.library_manager.custom_albums.keys():
            is_act = (self.current_view_type == "ALBUM" and self.active_target_name == alb_name)
            btn = ctk.CTkButton(
                self.dynamic_pills_frame, text=f"💿 {alb_name}", font=ctk.CTkFont(size=11), height=26, corner_radius=6,
                fg_color=RT.NEON_PINK if is_act else "transparent", hover_color=RT.BG_CARD_HOVER,
                text_color="#FFFFFF" if is_act else RT.NEON_PINK,
                command=lambda name=alb_name: self._switch_view("ALBUM", name)
            )
            btn.pack(side="left", padx=2)

    def _get_active_tracks(self) -> List[TrackMetadata]:
        all_map = {t.file_path: t for t in self.engine.playlist}

        if self.current_view_type == "ALL":
            return self.engine.playlist

        elif self.current_view_type == "LIKED":
            return [t for t in self.engine.playlist if self.library_manager.is_favourite(t.file_path)]

        elif self.current_view_type == "RECENT":
            recent_paths = self.library_manager.recently_played
            return [all_map[p] for p in recent_paths if p in all_map]

        elif self.current_view_type == "PLAYLIST" and self.active_target_name:
            paths = self.library_manager.playlists.get(self.active_target_name, [])
            return [all_map[p] for p in paths if p in all_map]

        elif self.current_view_type == "ALBUM" and self.active_target_name:
            paths = self.library_manager.custom_albums.get(self.active_target_name, [])
            return [all_map[p] for p in paths if p in all_map]

        return self.engine.playlist

    def _render_track_table(self):
        """Renders the scrollable track table rows."""
        for w in self.track_scroll.winfo_children():
            w.destroy()

        base_tracks = self._get_active_tracks()
        self.displayed_tracks = []
        query = self.search_query.lower()

        for track in base_tracks:
            if query and not (query in track.title.lower() or query in track.artist.lower() or query in track.album.lower()):
                continue
            self.displayed_tracks.append(track)

        for idx, track in enumerate(self.displayed_tracks):
            engine_idx = -1
            for e_i, t in enumerate(self.engine.playlist):
                if t.file_path == track.file_path:
                    engine_idx = e_i
                    break

            is_active = (engine_idx == self.engine.current_index and engine_idx != -1)
            is_fav = self.library_manager.is_favourite(track.file_path)

            bg_col = "#242738" if is_active else RT.BG_CARD
            border_col = RT.NEON_PURPLE if is_active else RT.BORDER_CYBER

            row = ctk.CTkFrame(self.track_scroll, fg_color=bg_col, corner_radius=8, height=46, border_color=border_col, border_width=1)
            row.pack(fill="x", pady=3)
            row.grid_columnconfigure(0, weight=0) # Fav & #
            row.grid_columnconfigure(1, weight=3) # Title & Artist
            row.grid_columnconfigure(2, weight=2) # Album
            row.grid_columnconfigure(3, weight=1) # Actions & Time

            # Fav & Index Box
            idx_box = ctk.CTkFrame(row, fg_color="transparent")
            idx_box.grid(row=0, column=0, padx=6)

            heart_btn = ctk.CTkButton(
                idx_box, text="💖" if is_fav else "🤍", width=24, height=24, corner_radius=12,
                fg_color="transparent", hover_color=RT.BG_CARD_HOVER, font=ctk.CTkFont(size=12),
                command=lambda path=track.file_path: self._action_toggle_favourite(path)
            )
            heart_btn.pack(side="left", padx=2)

            idx_txt = "►" if is_active and self.engine.state == PlaybackState.PLAYING else f"{idx + 1:02d}"
            idx_lbl = ctk.CTkLabel(idx_box, text=idx_txt, font=ctk.CTkFont(family="Courier", size=12, weight="bold"), text_color=RT.NEON_LIME if is_active else RT.TEXT_MUTED, width=30)
            idx_lbl.pack(side="left")

            # Title & Artist Stack
            t_box = ctk.CTkFrame(row, fg_color="transparent")
            t_box.grid(row=0, column=1, sticky="w", padx=10)

            t_lbl = ctk.CTkLabel(t_box, text=track.title, font=ctk.CTkFont(family="Courier", size=13, weight="bold" if is_active else "normal"), text_color=RT.NEON_PURPLE if is_active else RT.TEXT_MAIN, anchor="w")
            t_lbl.pack(anchor="w")
            a_lbl = ctk.CTkLabel(t_box, text=track.artist, font=ctk.CTkFont(size=10), text_color=RT.TEXT_MUTED, anchor="w")
            a_lbl.pack(anchor="w")

            # Album
            alb_lbl = ctk.CTkLabel(row, text=track.album, font=ctk.CTkFont(size=11), text_color=RT.TEXT_MUTED, anchor="w")
            alb_lbl.grid(row=0, column=2, sticky="w", padx=10)

            # Actions & Time
            act_box = ctk.CTkFrame(row, fg_color="transparent")
            act_box.grid(row=0, column=3, sticky="e", padx=10)

            time_lbl = ctk.CTkLabel(act_box, text=track.formatted_duration, font=ctk.CTkFont(family="Courier", size=11), text_color=RT.TEXT_MUTED)
            time_lbl.pack(side="left", padx=(0, 8))

            add_opt_btn = ctk.CTkButton(
                act_box, text="➕", width=24, height=24, corner_radius=12,
                fg_color="#12141F", hover_color=RT.BG_CARD_HOVER, text_color=RT.TEXT_MAIN, font=ctk.CTkFont(size=10),
                command=lambda path=track.file_path: self._action_show_add_to_dialog(path)
            )
            add_opt_btn.pack(side="left", padx=2)

            del_btn = ctk.CTkButton(
                act_box, text="✕", width=24, height=24, corner_radius=12,
                fg_color="transparent", hover_color="#991B1B", text_color=RT.TEXT_MUTED,
                command=lambda e_idx=engine_idx, path=track.file_path: self._action_remove_track_context(e_idx, path)
            )
            del_btn.pack(side="left")

            if engine_idx != -1:
                row.bind("<Double-Button-1>", lambda event, e_idx=engine_idx: self._action_play_index(e_idx))
                t_lbl.bind("<Double-Button-1>", lambda event, e_idx=engine_idx: self._action_play_index(e_idx))

    # ==========================================
    # 5. USER ACTIONS & DIALOGS
    # ==========================================
    def _update_cover_display(self, pil_image: Image.Image):
        resized = pil_image.resize((270, 190), Image.Resampling.LANCZOS)
        ctk_img = ctk.CTkImage(light_image=resized, dark_image=resized, size=(270, 190))
        self.cover_label.configure(image=ctk_img)

    def _update_mini_cover(self, pil_image: Image.Image):
        resized = pil_image.resize((52, 52), Image.Resampling.LANCZOS)
        ctk_img = ctk.CTkImage(light_image=resized, dark_image=resized, size=(52, 52))
        self.mini_cover_label.configure(image=ctk_img)

    def _update_now_playing_display(self, track: Optional[TrackMetadata]):
        if track is None:
            placeholder = create_placeholder_cover("Harmonix")
            self._update_cover_display(placeholder)
            self._update_mini_cover(placeholder)

            self.hero_title.configure(text="NO_TRACK_PLAYING")
            self.hero_artist.configure(text="LOAD AUDIO TO START")
            self.t_bpm.configure(text="[BPM: --]")
            self.t_fmt.configure(text="[STEREO --KBPS]")

            self.mini_title.configure(text="NO_AUDIO_PLAYING")
            self.mini_artist.configure(text="CYBER_DECK_V2")
            self.bar_heart_btn.configure(text="🤍")
            self.time_elapsed_label.configure(text="00:00")
            self.time_total_label.configure(text="00:00")
            self.seek_slider.set(0)
            self.play_btn.configure(text="[ ▶ PLAY ]")
        else:
            self._update_cover_display(track.cover_image)
            self._update_mini_cover(track.cover_image)

            self.hero_title.configure(text=track.title.upper())
            self.hero_artist.configure(text=track.artist.upper())
            self.t_bpm.configure(text=f"[BPM: {120 + abs(hash(track.title)) % 30}]")
            self.t_fmt.configure(text=f"[{track.genre.upper()} // 320KBPS]")

            self.mini_title.configure(text=track.title.upper())
            self.mini_artist.configure(text=track.artist.upper())
            self.time_total_label.configure(text=track.formatted_duration)

            is_fav = self.library_manager.is_favourite(track.file_path)
            self.bar_heart_btn.configure(text="💖" if is_fav else "🤍")

            if self.engine.state == PlaybackState.PLAYING:
                self.play_btn.configure(text="[ ⏸ PAUSE ]")
            else:
                self.play_btn.configure(text="[ ▶ PLAY ]")

        self._render_track_table()

    def _action_create_playlist(self):
        dialog = ctk.CTkInputDialog(text="Enter new playlist name:", title="Create Playlist")
        name = dialog.get_input()
        if name and name.strip():
            if self.library_manager.create_playlist(name.strip()):
                self._switch_view("PLAYLIST", name.strip())

    def _action_create_album(self):
        dialog = ctk.CTkInputDialog(text="Enter new custom album name:", title="Create Album")
        name = dialog.get_input()
        if name and name.strip():
            if self.library_manager.create_album(name.strip()):
                self._switch_view("ALBUM", name.strip())

    def _action_toggle_favourite(self, file_path: str):
        self.library_manager.toggle_favourite(file_path)
        self._update_now_playing_display(self.engine.current_track)

    def _action_toggle_current_favourite(self):
        if self.engine.current_track:
            self._action_toggle_favourite(self.engine.current_track.file_path)

    def _action_show_add_to_dialog(self, file_path: str):
        popup = ctk.CTkToplevel(self)
        popup.title("Add Track To...")
        popup.geometry("380x360")
        popup.configure(fg_color=RT.BG_PANEL)
        popup.grab_set()

        ctk.CTkLabel(popup, text="➕ Add Track to Playlist / Album", font=ctk.CTkFont(size=14, weight="bold"), text_color=RT.NEON_PURPLE).pack(pady=15)

        tabview = ctk.CTkTabview(popup, width=340, height=240, fg_color=RT.BG_CARD)
        tabview.pack(padx=15, pady=5)
        tabview.add("Playlists")
        tabview.add("Albums")

        pl_frame = ctk.CTkScrollableFrame(tabview.tab("Playlists"), fg_color="transparent")
        pl_frame.pack(fill="both", expand=True)

        if not self.library_manager.playlists:
            ctk.CTkLabel(pl_frame, text="No playlists created yet.", text_color=RT.TEXT_MUTED).pack(pady=20)
        else:
            for pl_name in self.library_manager.playlists.keys():
                btn = ctk.CTkButton(
                    pl_frame, text=f"📜 Add to '{pl_name}'", fg_color="#12141F", hover_color=RT.NEON_PURPLE, text_color=RT.TEXT_MAIN,
                    command=lambda name=pl_name: (
                        self.library_manager.add_to_playlist(name, file_path),
                        popup.destroy(),
                        self._render_track_table()
                    )
                )
                btn.pack(fill="x", pady=4)

        alb_frame = ctk.CTkScrollableFrame(tabview.tab("Albums"), fg_color="transparent")
        alb_frame.pack(fill="both", expand=True)

        if not self.library_manager.custom_albums:
            ctk.CTkLabel(alb_frame, text="No custom albums created yet.", text_color=RT.TEXT_MUTED).pack(pady=20)
        else:
            for alb_name in self.library_manager.custom_albums.keys():
                btn = ctk.CTkButton(
                    alb_frame, text=f"💿 Add to '{alb_name}'", fg_color="#12141F", hover_color=RT.NEON_PINK, text_color=RT.TEXT_MAIN,
                    command=lambda name=alb_name: (
                        self.library_manager.add_to_album(name, file_path),
                        popup.destroy(),
                        self._render_track_table()
                    )
                )
                btn.pack(fill="x", pady=4)

    def _action_remove_track_context(self, engine_idx: int, file_path: str):
        if self.current_view_type == "PLAYLIST" and self.active_target_name:
            self.library_manager.remove_from_playlist(self.active_target_name, file_path)
        elif self.current_view_type == "ALBUM" and self.active_target_name:
            self.library_manager.remove_from_album(self.active_target_name, file_path)
        elif self.current_view_type == "LIKED":
            self.library_manager.toggle_favourite(file_path)
        else:
            if engine_idx != -1:
                self.engine.remove_track(engine_idx)
        self._update_now_playing_display(self.engine.current_track)

    def _action_add_files(self):
        file_paths = filedialog.askopenfilenames(
            title="Select Audio Files",
            filetypes=[("Audio Files", "*.mp3 *.wav *.ogg *.flac *.m4a *.aac"), ("All Files", "*.*")]
        )
        if file_paths:
            self.engine.add_tracks(list(file_paths))
            self._render_track_table()
            if self.engine.state == PlaybackState.STOPPED and len(self.engine.playlist) > 0 and self.engine.current_index == -1:
                track = self.engine.play(0)
                self._update_now_playing_display(track)

    def _action_add_folder(self):
        folder = filedialog.askdirectory(title="Select Folder with Music")
        if folder:
            audio_files = []
            for root, _, files in os.walk(folder):
                for f in files:
                    if f.lower().split('.')[-1] in ['mp3', 'wav', 'ogg', 'flac', 'm4a', 'aac']:
                        audio_files.append(os.path.join(root, f))
            if audio_files:
                self.engine.add_tracks(audio_files)
                self._render_track_table()
                if self.engine.state == PlaybackState.STOPPED and len(self.engine.playlist) > 0 and self.engine.current_index == -1:
                    track = self.engine.play(0)
                    self._update_now_playing_display(track)

    def _action_play_index(self, index: int):
        track = self.engine.play(index)
        self._update_now_playing_display(track)

    def _action_toggle_play_pause(self):
        if not self.engine.playlist:
            return

        if self.engine.state == PlaybackState.PLAYING:
            self.engine.pause()
            self.play_btn.configure(text="[ ▶ PLAY ]")
        elif self.engine.state == PlaybackState.PAUSED:
            self.engine.resume()
            self.play_btn.configure(text="[ ⏸ PAUSE ]")
        else:
            track = self.engine.play()
            self._update_now_playing_display(track)

    def _action_next(self):
        track = self.engine.next_track()
        self._update_now_playing_display(track)

    def _action_previous(self):
        track = self.engine.previous_track()
        self._update_now_playing_display(track)

    def _action_toggle_mode(self):
        mode = self.engine.cycle_play_mode()
        self.shuffle_btn.configure(text_color=RT.NEON_CYAN if mode == PlayMode.SHUFFLE else RT.TEXT_MUTED)
        self.repeat_btn.configure(text_color=RT.NEON_PINK if mode in [PlayMode.REPEAT_ONE, PlayMode.REPEAT_ALL] else RT.TEXT_MUTED)

    def _action_toggle_mute(self):
        muted = self.engine.toggle_mute()
        if muted:
            self.mute_btn.configure(text="🔇")
            self.volume_slider.set(0)
        else:
            self.mute_btn.configure(text="🔊")
            self.volume_slider.set(self.engine.volume)

    def _action_volume_changed(self, value: float):
        self.engine.set_volume(value)
        self.engine.is_muted = False
        self.mute_btn.configure(text="🔊" if value > 0 else "🔇")

    def _action_seek_release(self, value: float):
        if self.engine.current_track:
            target_sec = (value / 100.0) * self.engine.current_track.duration
            self.engine.seek(target_sec)

    def _action_search_type(self, event=None):
        self.search_query = self.search_entry.get().strip()
        self._render_track_table()

    # ==========================================
    # 6. PERIODIC UPDATE & LIVE VU VISUALIZER LOOP
    # ==========================================
    def _periodic_update(self):
        try:
            # Auto advance check
            if self.engine.check_playback_auto_advance():
                self._update_now_playing_display(self.engine.current_track)

            # Update seek bar & time label
            if self.engine.state == PlaybackState.PLAYING and self.engine.current_track:
                elapsed = self.engine.get_elapsed_time()
                duration = self.engine.current_track.duration
                if duration > 0:
                    pct = min(100.0, (elapsed / duration) * 100.0)
                    self.seek_slider.set(pct)

                m = int(elapsed // 60)
                s = int(elapsed % 60)
                self.time_elapsed_label.configure(text=f"{m:02d}:{s:02d}")

                # --- ANIMATE LIVE VU AUDIO SPECTRUM BARS ---
                t = elapsed * 8.0
                for idx, bar in enumerate(self.spectrum_bars):
                    # Compute dynamic wave value using sine / cosine combination
                    amp = (math.sin(t + idx * 0.4) + math.cos(t * 1.5 + idx * 0.8) + 2.0) / 4.0
                    val = max(0.1, min(0.98, amp * random.uniform(0.7, 1.0)))
                    bar.set(val)
            else:
                # Reset visualizer when idle/paused
                for bar in self.spectrum_bars:
                    bar.set(0.08)

        except Exception as e:
            print(f"Error in periodic update loop: {e}")

        # Schedule next tick (100ms for smooth VU meter animation)
        self.after(100, self._periodic_update)
