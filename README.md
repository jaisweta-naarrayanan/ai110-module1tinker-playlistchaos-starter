# Playlist Chaos

A smart playlist generator built with Streamlit. Songs are automatically sorted into mood-based playlists — **Hype**, **Chill**, or **Mixed** — based on energy levels, genre, and a customizable user profile.

---

## Features

- **Mood-based playlists** — songs are classified into Hype, Chill, or Mixed using energy level, genre keywords, and your favorite genre
- **Custom mood profile** — configure your own Hype/Chill energy thresholds and favorite genre from the sidebar
- **Add songs** — add songs with title, artist, genre, energy (1–10), and tags
- **Search** — filter any playlist by artist (case-insensitive, partial match)
- **Lucky pick** — get a random song from Hype, Chill, or any combined pool
- **Playlist stats** — see total songs, hype ratio, average energy, and most common artist
- **History** — track lucky pick history with a mood breakdown summary

---

## Project structure

```
playlist_chaos/
├── app.py                  # Streamlit UI — layout, sidebar, tabs, sections
├── playlist_logic.py       # Core logic — classification, search, stats, lucky pick
├── test_playlist_logic.py  # Pytest test suite for playlist_logic.py
├── requirements.txt        # Python dependencies
└── README.md
```

---

## Getting started

### 1. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
.venv\Scripts\activate           # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
streamlit run app.py
```

The app opens automatically in your browser at `http://localhost:8501`.

---

## Running tests

```bash
.venv/bin/python -m pytest test_playlist_logic.py -v
```

Tests cover:
- Song classification (Hype / Chill / Mixed) including boundary conditions
- Case-insensitive partial search
- Playlist statistics (total songs, average energy, hype ratio)
- Lucky pick mode isolation and empty-list safety
- Data normalization (whitespace, genre casing, energy parsing, tags)

---

## How song classification works

| Condition | Mood |
|---|---|
| Genre matches favorite genre, OR energy ≥ `hype_min_energy` (default 7), OR genre contains `rock`/`punk`/`party` | **Hype** |
| Energy ≤ `chill_max_energy` (default 3), OR title contains `lofi`/`ambient`/`sleep` | **Chill** |
| Everything else | **Mixed** |

Hype conditions are evaluated first — a low-energy rock song still goes to Hype if rock is your favorite genre.

---

## Tech stack

- [Streamlit](https://streamlit.io) — UI framework
- Python 3.10+
- pytest — testing
