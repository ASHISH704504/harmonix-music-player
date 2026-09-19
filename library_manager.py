import os
import json
from typing import List, Dict, Set


class LibraryManager:
    """Manages persistent library data including Favourites, Recently Played, Custom Playlists, and Custom Albums."""

    def __init__(self, storage_path: str = "library.json"):
        self.storage_path = storage_path
        self.favourites: Set[str] = set()
        self.recently_played: List[str] = []
        self.playlists: Dict[str, List[str]] = {}
        self.custom_albums: Dict[str, List[str]] = {}

        self.load_data()

    def load_data(self):
        """Loads persistent JSON library data from storage_path."""
        if not os.path.exists(self.storage_path):
            self.save_data()
            return

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.favourites = set(data.get("favourites", []))
                self.recently_played = data.get("recently_played", [])
                self.playlists = data.get("playlists", {})
                self.custom_albums = data.get("custom_albums", {})
        except Exception as e:
            print(f"Error loading library data: {e}")

    def save_data(self):
        """Saves library data to JSON file."""
        try:
            data = {
                "favourites": list(self.favourites),
                "recently_played": self.recently_played,
                "playlists": self.playlists,
                "custom_albums": self.custom_albums
            }
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving library data: {e}")

    # ==========================================
    # 1. FAVOURITES MANAGEMENT
    # ==========================================
    def toggle_favourite(self, file_path: str) -> bool:
        """Toggles favorite status for a track file path."""
        if file_path in self.favourites:
            self.favourites.remove(file_path)
            is_fav = False
        else:
            self.favourites.add(file_path)
            is_fav = True
        self.save_data()
        return is_fav

    def is_favourite(self, file_path: str) -> bool:
        """Returns True if track is marked as favourite."""
        return file_path in self.favourites

    # ==========================================
    # 2. RECENTLY PLAYED MANAGEMENT
    # ==========================================
    def add_recently_played(self, file_path: str):
        """Pushes track file path to recently played list (max 30 tracks)."""
        if file_path in self.recently_played:
            self.recently_played.remove(file_path)
        self.recently_played.insert(0, file_path)
        if len(self.recently_played) > 30:
            self.recently_played = self.recently_played[:30]
        self.save_data()

    # ==========================================
    # 3. PLAYLISTS MANAGEMENT
    # ==========================================
    def create_playlist(self, name: str) -> bool:
        """Creates a new empty playlist if it doesn't already exist."""
        name = name.strip()
        if not name or name in self.playlists:
            return False
        self.playlists[name] = []
        self.save_data()
        return True

    def delete_playlist(self, name: str) -> bool:
        """Deletes a custom playlist by name."""
        if name in self.playlists:
            del self.playlists[name]
            self.save_data()
            return True
        return False

    def add_to_playlist(self, playlist_name: str, file_path: str) -> bool:
        """Adds a track file path to a playlist."""
        if playlist_name in self.playlists:
            if file_path not in self.playlists[playlist_name]:
                self.playlists[playlist_name].append(file_path)
                self.save_data()
                return True
        return False

    def remove_from_playlist(self, playlist_name: str, file_path: str) -> bool:
        """Removes a track file path from a playlist."""
        if playlist_name in self.playlists and file_path in self.playlists[playlist_name]:
            self.playlists[playlist_name].remove(file_path)
            self.save_data()
            return True
        return False

    # ==========================================
    # 4. CUSTOM ALBUMS MANAGEMENT
    # ==========================================
    def create_album(self, name: str) -> bool:
        """Creates a new custom album."""
        name = name.strip()
        if not name or name in self.custom_albums:
            return False
        self.custom_albums[name] = []
        self.save_data()
        return True

    def delete_album(self, name: str) -> bool:
        """Deletes a custom album by name."""
        if name in self.custom_albums:
            del self.custom_albums[name]
            self.save_data()
            return True
        return False

    def add_to_album(self, album_name: str, file_path: str) -> bool:
        """Adds a track file path to a custom album."""
        if album_name in self.custom_albums:
            if file_path not in self.custom_albums[album_name]:
                self.custom_albums[album_name].append(file_path)
                self.save_data()
                return True
        return False

    def remove_from_album(self, album_name: str, file_path: str) -> bool:
        """Removes a track file path from a custom album."""
        if album_name in self.custom_albums and file_path in self.custom_albums[album_name]:
            self.custom_albums[album_name].remove(file_path)
            self.save_data()
            return True
        return False
