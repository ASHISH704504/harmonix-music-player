import os
import io
import math
from typing import Dict, Any, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import mutagen
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis
from mutagen.mp4 import MP4


class TrackMetadata:
    """Class holding metadata information for an audio file."""
    def __init__(
        self,
        file_path: str,
        title: str,
        artist: str,
        album: str,
        genre: str,
        duration: float,
        cover_image: Optional[Image.Image] = None
    ):
        self.file_path = file_path
        self.title = title
        self.artist = artist
        self.album = album
        self.genre = genre
        self.duration = duration
        self.cover_image = cover_image

    @property
    def formatted_duration(self) -> str:
        """Returns duration formatted as MM:SS or HH:MM:SS."""
        total_seconds = int(self.duration)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"


def create_placeholder_cover(title: str, size: Tuple[int, int] = (400, 300)) -> Image.Image:
    """Generates a stylish Gen-Z Retro Cassette Tape illustration using Pillow (dynamically scalable)."""
    width, height = size
    image = Image.new("RGBA", size, (11, 12, 16, 255))
    draw = ImageDraw.Draw(image)

    # Margins relative to dimensions
    m_x = max(2, int(width * 0.05))
    m_y = max(2, int(height * 0.05))

    # Outer Cassette Body
    c_box = (m_x, m_y, width - m_x, height - m_y)
    draw.rounded_rectangle(c_box, radius=max(2, int(min(width, height) * 0.06)), fill=(24, 26, 36, 255), outline=(43, 46, 66, 255), width=2)

    # Top Sticker Gradient Bar
    s_x0 = m_x + max(2, int(width * 0.04))
    s_y0 = m_y + max(2, int(height * 0.04))
    s_x1 = width - m_x - max(2, int(width * 0.04))
    s_y1 = height // 2 + max(1, int(height * 0.02))

    if s_x1 > s_x0 and s_y1 > s_y0:
        draw.rounded_rectangle((s_x0, s_y0, s_x1, s_y1), radius=max(2, int(min(width, height) * 0.04)), fill=(139, 92, 246, 220), outline=(236, 72, 153, 255), width=1)

    # Tape Window
    win_w = max(10, int(width * 0.55))
    win_h = max(10, int(height * 0.35))
    win_box = (width // 2 - win_w // 2, height // 2 - win_h // 2 + 2, width // 2 + win_w // 2, height // 2 + win_h // 2 + 2)

    if win_box[2] > win_box[0] and win_box[3] > win_box[1]:
        draw.rounded_rectangle(win_box, radius=max(2, int(min(width, height) * 0.03)), fill=(11, 12, 16, 255), outline=(6, 182, 212, 200), width=1)

        # Reels
        reel_r = max(2, win_h // 2 - 2)
        left_center = (win_box[0] + win_w // 4, win_box[1] + win_h // 2)
        right_center = (win_box[2] - win_w // 4, win_box[1] + win_h // 2)

        draw.ellipse((left_center[0] - reel_r, left_center[1] - reel_r, left_center[0] + reel_r, left_center[1] + reel_r), fill=(30, 32, 45, 255), outline=(236, 72, 153, 255), width=1)
        draw.ellipse((right_center[0] - reel_r, right_center[1] - reel_r, right_center[0] + reel_r, right_center[1] + reel_r), fill=(30, 32, 45, 255), outline=(6, 182, 212, 255), width=1)

        # Connecting Tape Ribbon
        draw.line([(left_center[0], left_center[1] + reel_r), (right_center[0], right_center[1] + reel_r)], fill=(139, 92, 246, 255), width=2)

    return image.convert("RGB")


def extract_metadata(file_path: str) -> TrackMetadata:
    """Extracts metadata and embedded cover art from an audio file."""
    filename = os.path.basename(file_path)
    title = os.path.splitext(filename)[0].replace("_", " ").replace("-", " ")
    artist = "UNKNOWN_ARTIST"
    album = "RETRO_TAPES"
    genre = "SYNTH"
    duration = 0.0
    cover_image: Optional[Image.Image] = None

    try:
        audio = mutagen.File(file_path)
        if audio is not None:
            if hasattr(audio.info, "length"):
                duration = float(audio.info.length)

            if isinstance(audio, MP3) or hasattr(audio, "tags") and audio.tags is not None:
                tags = audio.tags
                if tags:
                    if "TIT2" in tags:
                        title = str(tags["TIT2"].text[0])
                    if "TPE1" in tags:
                        artist = str(tags["TPE1"].text[0])
                    if "TALB" in tags:
                        album = str(tags["TALB"].text[0])
                    if "TCON" in tags:
                        genre = str(tags["TCON"].text[0])

                    for key in tags.keys():
                        if key.startswith("APIC"):
                            image_data = tags[key].data
                            cover_image = Image.open(io.BytesIO(image_data)).convert("RGB")
                            break

            elif isinstance(audio, FLAC):
                if "title" in audio:
                    title = audio["title"][0]
                if "artist" in audio:
                    artist = audio["artist"][0]
                if "album" in audio:
                    album = audio["album"][0]
                if "genre" in audio:
                    genre = audio["genre"][0]
                if audio.pictures:
                    cover_image = Image.open(io.BytesIO(audio.pictures[0].data)).convert("RGB")

            elif isinstance(audio, MP4):
                if audio.tags:
                    if "\xa9nam" in audio.tags:
                        title = audio.tags["\xa9nam"][0]
                    if "\xa9ART" in audio.tags:
                        artist = audio.tags["\xa9ART"][0]
                    if "\xa9alb" in audio.tags:
                        album = audio.tags["\xa9alb"][0]
                    if "\xa9gen" in audio.tags:
                        genre = audio.tags["\xa9gen"][0]
                    if "covr" in audio.tags and audio.tags["covr"]:
                        cover_image = Image.open(io.BytesIO(audio.tags["covr"][0])).convert("RGB")

            elif isinstance(audio, OggVorbis):
                if "title" in audio:
                    title = audio["title"][0]
                if "artist" in audio:
                    artist = audio["artist"][0]
                if "album" in audio:
                    album = audio["album"][0]
                if "genre" in audio:
                    genre = audio["genre"][0]

    except Exception as e:
        print(f"Warning: Could not fully read metadata for '{file_path}': {e}")

    if cover_image is None:
        cover_image = create_placeholder_cover(title)

    return TrackMetadata(
        file_path=file_path,
        title=title,
        artist=artist,
        album=album,
        genre=genre,
        duration=duration,
        cover_image=cover_image
    )
