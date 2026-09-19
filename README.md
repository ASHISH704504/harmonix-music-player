# [ HARMONIX // CYBER_DECK_V2 ]

Gen-Z dark minimalistic retro-fusion **desktop music player** built with Python (CustomTkinter + pygame), plus a **browser-based web player** in `web_app/`.

## Features

- Load audio files or whole folders (mp3/wav/ogg/flac/m4a/aac)
- Play / pause / next / prev, seek bar, volume + mute
- Play modes: normal / repeat track / repeat all / shuffle
- Favourites, Recently played, custom Playlists & Albums (persisted to `library.json`)
- Live 16-bar spectrum analyzer + hero cassette deck card
- Live search, cyberpunk retro UI (CustomTkinter)

## Run the desktop app

```
pip install -r requirements.txt
python main.py
```

## Demo tracks

Regenerate the built-in synth demo tracks:

```
python create_demo_tracks.py
```

## Web version

See `web_app/README.md` — a Flask + vanilla-JS single-page player serving the same demo tracks.

## Tests

```
python test_player.py
```

CI runs this on every push via GitHub Actions (`.github/workflows/ci.yml`).