import random
import time
from enum import Enum
from typing import List, Optional
import pygame
from metadata_manager import TrackMetadata, extract_metadata
from library_manager import LibraryManager


class PlayMode(Enum):
    NORMAL = "Normal"
    REPEAT_ONE = "Repeat Track"
    REPEAT_ALL = "Repeat All"
    SHUFFLE = "Shuffle"


class PlaybackState(Enum):
    STOPPED = "Stopped"
    PLAYING = "Playing"
    PAUSED = "Paused"


class AudioEngine:
    """Audio playback engine wrapper for pygame.mixer.music with LibraryManager integration."""
    
    def __init__(self, library_manager: Optional[LibraryManager] = None):
        # Initialize Pygame mixer with high-quality parameters
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
        
        self.library_manager = library_manager if library_manager is not None else LibraryManager()
        self.playlist: List[TrackMetadata] = []
        self.current_index: int = -1
        self.state: PlaybackState = PlaybackState.STOPPED
        self.play_mode: PlayMode = PlayMode.NORMAL
        
        self.volume: float = 0.7  # Default volume 70%
        self.is_muted: bool = False
        self.previous_volume: float = 0.7
        
        self.start_offset: float = 0.0  # Seconds offset when seeking
        self.start_ticks: float = 0.0   # Timestamp when play/seek started
        
        pygame.mixer.music.set_volume(self.volume)

    def add_tracks(self, file_paths: List[str]) -> List[TrackMetadata]:
        """Adds list of file paths to playlist after extracting metadata."""
        added = []
        existing_paths = {t.file_path for t in self.playlist}
        for path in file_paths:
            ext = path.lower().split('.')[-1]
            if ext in ['mp3', 'wav', 'ogg', 'flac', 'm4a', 'aac'] and path not in existing_paths:
                metadata = extract_metadata(path)
                self.playlist.append(metadata)
                added.append(metadata)
                existing_paths.add(path)
        return added

    def remove_track(self, index: int):
        """Removes a track from playlist by index."""
        if 0 <= index < len(self.playlist):
            if index == self.current_index:
                self.stop()
                self.current_index = -1
            elif index < self.current_index:
                self.current_index -= 1
            self.playlist.pop(index)

    def clear_playlist(self):
        """Clears all tracks from playlist and stops playback."""
        self.stop()
        self.playlist.clear()
        self.current_index = -1

    def play(self, index: Optional[int] = None) -> Optional[TrackMetadata]:
        """Plays track at specified index or current index."""
        if not self.playlist:
            return None
            
        if index is not None:
            if 0 <= index < len(self.playlist):
                self.current_index = index
            else:
                return None

        if self.current_index == -1:
            self.current_index = 0

        track = self.playlist[self.current_index]

        try:
            pygame.mixer.music.load(track.file_path)
            pygame.mixer.music.play(start=0.0)
            self.state = PlaybackState.PLAYING
            self.start_offset = 0.0
            self.start_ticks = time.time()

            # Record in Recently Played
            self.library_manager.add_recently_played(track.file_path)

            return track
        except Exception as e:
            print(f"Error playing file '{track.file_path}': {e}")
            self.state = PlaybackState.STOPPED
            return None

    def pause(self):
        """Pauses audio playback."""
        if self.state == PlaybackState.PLAYING:
            pygame.mixer.music.pause()
            self.state = PlaybackState.PAUSED

    def resume(self):
        """Resumes audio playback."""
        if self.state == PlaybackState.PAUSED:
            pygame.mixer.music.unpause()
            self.state = PlaybackState.PLAYING

    def stop(self):
        """Stops audio playback."""
        pygame.mixer.music.stop()
        self.state = PlaybackState.STOPPED
        self.start_offset = 0.0

    def next_track(self) -> Optional[TrackMetadata]:
        """Advances to the next track based on play_mode."""
        if not self.playlist:
            return None

        if self.play_mode == PlayMode.REPEAT_ONE:
            return self.play(self.current_index)
        elif self.play_mode == PlayMode.SHUFFLE:
            next_idx = random.randint(0, len(self.playlist) - 1)
            return self.play(next_idx)
        else:
            next_idx = self.current_index + 1
            if next_idx >= len(self.playlist):
                if self.play_mode == PlayMode.REPEAT_ALL:
                    next_idx = 0
                else:
                    self.stop()
                    return None
            return self.play(next_idx)

    def previous_track(self) -> Optional[TrackMetadata]:
        """Goes to the previous track or restarts track if > 3s played."""
        if not self.playlist:
            return None

        if self.get_elapsed_time() > 3.0:
            return self.play(self.current_index)

        if self.play_mode == PlayMode.SHUFFLE:
            prev_idx = random.randint(0, len(self.playlist) - 1)
            return self.play(prev_idx)
        else:
            prev_idx = self.current_index - 1
            if prev_idx < 0:
                prev_idx = len(self.playlist) - 1 if self.play_mode == PlayMode.REPEAT_ALL else 0
            return self.play(prev_idx)

    def seek(self, position_seconds: float):
        """Seeks to a specific position in seconds."""
        if self.state in [PlaybackState.PLAYING, PlaybackState.PAUSED] and self.current_track:
            pos = max(0.0, min(position_seconds, self.current_track.duration))
            try:
                pygame.mixer.music.play(start=pos)
                if self.state == PlaybackState.PAUSED:
                    pygame.mixer.music.pause()
                self.start_offset = pos
                self.start_ticks = time.time()
            except Exception as e:
                print(f"Error seeking: {e}")

    def set_volume(self, level: float):
        """Sets volume (0.0 to 1.0)."""
        self.volume = max(0.0, min(1.0, level))
        if not self.is_muted:
            pygame.mixer.music.set_volume(self.volume)

    def toggle_mute(self) -> bool:
        """Toggles mute state and returns current mute status."""
        if self.is_muted:
            self.is_muted = False
            pygame.mixer.music.set_volume(self.volume)
        else:
            self.is_muted = True
            self.previous_volume = self.volume
            pygame.mixer.music.set_volume(0.0)
        return self.is_muted

    def cycle_play_mode(self) -> PlayMode:
        """Cycles to the next PlayMode."""
        modes = list(PlayMode)
        current_idx = modes.index(self.play_mode)
        self.play_mode = modes[(current_idx + 1) % len(modes)]
        return self.play_mode

    def get_elapsed_time(self) -> float:
        """Returns elapsed playback time in seconds."""
        if self.state == PlaybackState.STOPPED or self.current_index == -1:
            return 0.0

        if self.state == PlaybackState.PAUSED:
            return self.start_offset

        pos_ms = pygame.mixer.music.get_pos()
        if pos_ms < 0:
            return self.start_offset

        return self.start_offset + (pos_ms / 1000.0)

    @property
    def current_track(self) -> Optional[TrackMetadata]:
        """Returns currently selected TrackMetadata."""
        if 0 <= self.current_index < len(self.playlist):
            return self.playlist[self.current_index]
        return None

    def check_playback_auto_advance(self) -> bool:
        """Checks if current track finished playing to trigger next track."""
        if self.state == PlaybackState.PLAYING:
            if not pygame.mixer.music.get_busy():
                self.next_track()
                return True
        return False
