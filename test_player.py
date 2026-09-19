import os
import wave
import math
import struct
import time
import pygame
from metadata_manager import extract_metadata, create_placeholder_cover
from library_manager import LibraryManager
from audio_engine import AudioEngine, PlayMode, PlaybackState
from gui import MusicPlayerGUI


def create_sample_wav(filename: str, duration_sec: float = 3.0, freq: float = 440.0):
    """Generates a simple sine wave WAV file for testing."""
    sample_rate = 44100
    n_samples = int(sample_rate * duration_sec)
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        for i in range(n_samples):
            sample = math.sin(2 * math.pi * freq * (i / sample_rate))
            scaled_sample = int(sample * 32767 * 0.5)
            data = struct.pack('<h', scaled_sample)
            wav_file.writeframesraw(data)


def test_genz_retro_player():
    print("--- 1. Testing Library Manager & Storage ---")
    test_json = os.path.join(os.path.dirname(__file__), "test_library.json")
    if os.path.exists(test_json):
        os.remove(test_json)

    lib = LibraryManager(storage_path=test_json)

    # Favourites & Playlists & Custom Albums
    track_path = "C:/synth_track.mp3"
    lib.toggle_favourite(track_path)
    lib.create_playlist("Cyber Synth 2026")
    lib.add_to_playlist("Cyber Synth 2026", track_path)
    lib.create_album("Aether Tape Deck")
    lib.add_to_album("Aether Tape Deck", track_path)
    lib.add_recently_played(track_path)

    print("[OK] LibraryManager Passed.")

    print("--- 2. Testing Audio Engine & Spectrum Visualizer Loop ---")
    test_wav = os.path.join(os.path.dirname(__file__), "test_sample.wav")
    create_sample_wav(test_wav, duration_sec=3.0, freq=523.25)

    engine = AudioEngine(library_manager=lib)
    engine.add_tracks([test_wav])
    engine.play(0)
    assert engine.state == PlaybackState.PLAYING
    engine.stop()

    print("--- 3. Testing Gen-Z Retro GUI Initialization & VU Meter ---")
    app = MusicPlayerGUI()
    app.update_idletasks()
    app.update()

    # Test switching Gen-Z Retro views
    app._switch_view("LIKED")
    app.update()
    app._switch_view("RECENT")
    app.update()
    app._switch_view("PLAYLIST", "Cyber Synth 2026")
    app.update()
    app._switch_view("ALBUM", "Aether Tape Deck")
    app.update()
    app._switch_view("ALL")
    app.update()

    # Verify spectrum bars count
    assert len(app.spectrum_bars) == 16, "Spectrum bars count should be 16!"

    app.destroy()

    # Cleanup
    pygame.mixer.music.unload()
    if os.path.exists(test_wav):
        os.remove(test_wav)
    if os.path.exists(test_json):
        os.remove(test_json)

    print("[OK] All Gen-Z Retro Fusion Tests Passed Successfully!")


if __name__ == "__main__":
    test_genz_retro_player()
