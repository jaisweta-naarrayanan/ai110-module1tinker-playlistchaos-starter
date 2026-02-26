"""
Tests for playlist_logic.py based on the Intended Behavior Overview.

Run with: .venv/bin/python -m pytest test_playlist_logic.py -v
"""

import pytest

from playlist_logic import (
    DEFAULT_PROFILE,
    build_playlists,
    classify_song,
    compute_playlist_stats,
    lucky_pick,
    normalize_song,
    search_songs,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_song(title="Test Song", artist="Test Artist", genre="pop", energy=5, tags=None):
    return {"title": title, "artist": artist, "genre": genre, "energy": energy, "tags": tags or []}


def default_profile(**overrides):
    profile = dict(DEFAULT_PROFILE)
    profile.update(overrides)
    return profile


# ---------------------------------------------------------------------------
# 1. Song Classification
# ---------------------------------------------------------------------------

class TestClassifySong:

    # --- Hype: energy >= hype_min_energy ---

    def test_hype_by_high_energy(self):
        song = make_song(genre="jazz", energy=7)
        assert classify_song(song, default_profile()) == "Hype"

    def test_hype_at_exact_min_energy_boundary(self):
        # energy exactly equal to hype_min_energy (default 7) should be Hype
        song = make_song(genre="jazz", energy=7)
        assert classify_song(song, default_profile(hype_min_energy=7)) == "Hype"

    def test_hype_above_min_energy(self):
        song = make_song(genre="jazz", energy=10)
        assert classify_song(song, default_profile()) == "Hype"

    # --- Hype: genre matches favorite_genre ---

    def test_hype_by_favorite_genre(self):
        # rock is the default favorite genre; a low-energy rock song is still Hype
        song = make_song(genre="rock", energy=2)
        assert classify_song(song, default_profile(favorite_genre="rock")) == "Hype"

    def test_hype_by_favorite_genre_non_rock(self):
        song = make_song(genre="jazz", energy=3)
        assert classify_song(song, default_profile(favorite_genre="jazz")) == "Hype"

    # --- Hype: genre contains a hype keyword ---

    def test_hype_by_genre_keyword_rock(self):
        song = make_song(genre="rock", energy=5)
        assert classify_song(song, default_profile(favorite_genre="pop")) == "Hype"

    def test_hype_by_genre_keyword_punk(self):
        song = make_song(genre="punk", energy=5)
        assert classify_song(song, default_profile(favorite_genre="pop")) == "Hype"

    def test_hype_by_genre_keyword_party(self):
        song = make_song(genre="party", energy=5)
        assert classify_song(song, default_profile(favorite_genre="pop")) == "Hype"

    # --- Chill: energy <= chill_max_energy ---

    def test_chill_by_low_energy(self):
        song = make_song(genre="jazz", energy=3)
        assert classify_song(song, default_profile()) == "Chill"

    def test_chill_at_exact_max_energy_boundary(self):
        # energy exactly equal to chill_max_energy (default 3) should be Chill
        song = make_song(genre="pop", energy=3)
        assert classify_song(song, default_profile(chill_max_energy=3)) == "Chill"

    def test_chill_below_max_energy(self):
        song = make_song(genre="pop", energy=1)
        assert classify_song(song, default_profile()) == "Chill"

    # --- Chill: title contains a chill keyword ---

    def test_chill_by_title_keyword_lofi(self):
        # Per spec: chill keywords (lofi, ambient, sleep) are matched against title
        song = make_song(title="My Lofi Dreams", genre="pop", energy=5)
        assert classify_song(song, default_profile(favorite_genre="jazz")) == "Chill"

    def test_chill_by_title_keyword_ambient(self):
        song = make_song(title="Ambient Waves", genre="pop", energy=5)
        assert classify_song(song, default_profile(favorite_genre="jazz")) == "Chill"

    def test_chill_by_title_keyword_sleep(self):
        song = make_song(title="Deep Sleep Sounds", genre="pop", energy=5)
        assert classify_song(song, default_profile(favorite_genre="jazz")) == "Chill"

    # --- Mixed: doesn't meet Hype or Chill criteria ---

    def test_mixed_mid_energy_no_keywords(self):
        song = make_song(genre="pop", energy=5)
        # Not favorite genre, not hype keyword, energy 5 is between 3 and 7
        assert classify_song(song, default_profile(favorite_genre="rock")) == "Mixed"

    def test_mixed_energy_just_above_chill_threshold(self):
        song = make_song(genre="electronic", energy=4)
        assert classify_song(song, default_profile(favorite_genre="rock")) == "Mixed"

    def test_mixed_energy_just_below_hype_threshold(self):
        song = make_song(genre="electronic", energy=6)
        assert classify_song(song, default_profile(favorite_genre="rock")) == "Mixed"

    # --- Hype takes precedence over Chill ---

    def test_hype_wins_when_favorite_genre_and_low_energy(self):
        # Favorite genre match triggers Hype even though energy is low
        song = make_song(genre="jazz", energy=2)
        assert classify_song(song, default_profile(favorite_genre="jazz")) == "Hype"


# ---------------------------------------------------------------------------
# 2. Search Functionality
# ---------------------------------------------------------------------------

class TestSearchSongs:

    def setup_method(self):
        self.songs = [
            make_song(title="Thunderstruck", artist="AC/DC", genre="rock"),
            make_song(title="Bohemian Rhapsody", artist="Queen", genre="rock"),
            make_song(title="Blinding Lights", artist="The Weeknd", genre="pop"),
            make_song(title="Take Five", artist="Dave Brubeck", genre="jazz"),
        ]

    def test_empty_query_returns_all_songs(self):
        result = search_songs(self.songs, "")
        assert len(result) == len(self.songs)

    def test_partial_match(self):
        # "DC" should find "AC/DC"
        result = search_songs(self.songs, "DC", field="artist")
        assert len(result) == 1
        assert result[0]["artist"] == "AC/DC"

    def test_case_insensitive_uppercase_query(self):
        # Searching "AC" in uppercase should still find "AC/DC"
        result = search_songs(self.songs, "AC", field="artist")
        assert len(result) == 1
        assert result[0]["artist"] == "AC/DC"

    def test_case_insensitive_lowercase_query(self):
        # Searching "ac/dc" in lowercase should find "AC/DC"
        result = search_songs(self.songs, "ac/dc", field="artist")
        assert len(result) == 1
        assert result[0]["artist"] == "AC/DC"

    def test_partial_match_returns_multiple(self):
        # "e" appears in "Queen", "The Weeknd", "Dave Brubeck"
        result = search_songs(self.songs, "e", field="artist")
        artists = {s["artist"] for s in result}
        assert "Queen" in artists

    def test_no_match_returns_empty(self):
        result = search_songs(self.songs, "Beyonce", field="artist")
        assert result == []

    def test_search_by_title_field(self):
        result = search_songs(self.songs, "thunder", field="title")
        assert len(result) == 1
        assert result[0]["title"] == "Thunderstruck"

    def test_exact_full_match(self):
        result = search_songs(self.songs, "queen", field="artist")
        assert len(result) == 1
        assert result[0]["artist"] == "Queen"


# ---------------------------------------------------------------------------
# 3. Playlist Statistics
# ---------------------------------------------------------------------------

class TestComputePlaylistStats:

    def test_total_songs_counts_all_categories(self):
        playlists = {
            "Hype": [make_song(energy=9), make_song(energy=8)],
            "Chill": [make_song(energy=1)],
            "Mixed": [make_song(energy=5)],
        }
        stats = compute_playlist_stats(playlists)
        assert stats["total_songs"] == 4

    def test_avg_energy_is_average_of_all_songs(self):
        playlists = {
            "Hype": [make_song(energy=10)],
            "Chill": [make_song(energy=2)],
            "Mixed": [],
        }
        stats = compute_playlist_stats(playlists)
        assert stats["avg_energy"] == pytest.approx(6.0)

    def test_hype_ratio_is_fraction_of_total(self):
        playlists = {
            "Hype": [make_song(), make_song()],
            "Chill": [make_song(), make_song(), make_song()],
            "Mixed": [],
        }
        stats = compute_playlist_stats(playlists)
        # 2 hype out of 5 total = 0.4
        assert stats["hype_ratio"] == pytest.approx(0.4)

    def test_hype_ratio_zero_when_no_hype_songs(self):
        playlists = {
            "Hype": [],
            "Chill": [make_song(), make_song()],
            "Mixed": [],
        }
        stats = compute_playlist_stats(playlists)
        assert stats["hype_ratio"] == pytest.approx(0.0)

    def test_hype_ratio_one_when_all_hype(self):
        playlists = {
            "Hype": [make_song(), make_song()],
            "Chill": [],
            "Mixed": [],
        }
        stats = compute_playlist_stats(playlists)
        assert stats["hype_ratio"] == pytest.approx(1.0)

    def test_empty_playlists_zero_avg_energy(self):
        playlists = {"Hype": [], "Chill": [], "Mixed": []}
        stats = compute_playlist_stats(playlists)
        assert stats["avg_energy"] == pytest.approx(0.0)

    def test_counts_per_category(self):
        playlists = {
            "Hype": [make_song(), make_song()],
            "Chill": [make_song()],
            "Mixed": [make_song(), make_song(), make_song()],
        }
        stats = compute_playlist_stats(playlists)
        assert stats["hype_count"] == 2
        assert stats["chill_count"] == 1
        assert stats["mixed_count"] == 3


# ---------------------------------------------------------------------------
# 4. Lucky Pick
# ---------------------------------------------------------------------------

class TestLuckyPick:

    def setup_method(self):
        hype_song = make_song(title="Hype Song", artist="Hype Artist", genre="rock", energy=9)
        hype_song["mood"] = "Hype"
        chill_song = make_song(title="Chill Song", artist="Chill Artist", genre="ambient", energy=1)
        chill_song["mood"] = "Chill"
        self.playlists = {
            "Hype": [hype_song],
            "Chill": [chill_song],
            "Mixed": [],
        }

    def test_hype_mode_only_picks_from_hype(self):
        for _ in range(20):
            pick = lucky_pick(self.playlists, mode="hype")
            assert pick is not None
            assert pick["mood"] == "Hype"

    def test_chill_mode_only_picks_from_chill(self):
        for _ in range(20):
            pick = lucky_pick(self.playlists, mode="chill")
            assert pick is not None
            assert pick["mood"] == "Chill"

    def test_any_mode_picks_from_hype_or_chill(self):
        # With many trials, both moods should appear
        moods_seen = set()
        for _ in range(50):
            pick = lucky_pick(self.playlists, mode="any")
            assert pick is not None
            moods_seen.add(pick["mood"])
        assert "Hype" in moods_seen
        assert "Chill" in moods_seen

    def test_returns_none_for_empty_hype_playlist(self):
        playlists = {"Hype": [], "Chill": [], "Mixed": []}
        assert lucky_pick(playlists, mode="hype") is None

    def test_returns_none_for_empty_chill_playlist(self):
        playlists = {"Hype": [], "Chill": [], "Mixed": []}
        assert lucky_pick(playlists, mode="chill") is None

    def test_returns_none_for_empty_any_mode(self):
        playlists = {"Hype": [], "Chill": [], "Mixed": []}
        assert lucky_pick(playlists, mode="any") is None

    def test_always_returns_song_when_songs_exist(self):
        pick = lucky_pick(self.playlists, mode="any")
        assert pick is not None
        assert "title" in pick


# ---------------------------------------------------------------------------
# 5. Data Normalization
# ---------------------------------------------------------------------------

class TestNormalizeSong:

    def test_strips_whitespace_from_title(self):
        song = make_song(title="  Thunderstruck  ")
        result = normalize_song(song)
        assert result["title"] == "Thunderstruck"

    def test_strips_whitespace_from_artist(self):
        song = make_song(artist="  AC/DC  ")
        result = normalize_song(song)
        assert result["artist"] == "AC/DC"

    def test_genre_normalized_to_lowercase(self):
        song = make_song(genre="ROCK")
        result = normalize_song(song)
        assert result["genre"] == "rock"

    def test_genre_strips_whitespace(self):
        song = make_song(genre="  Pop  ")
        result = normalize_song(song)
        assert result["genre"] == "pop"

    def test_invalid_string_energy_defaults_to_zero(self):
        song = make_song()
        song["energy"] = "loud"
        result = normalize_song(song)
        assert result["energy"] == 0

    def test_string_numeric_energy_is_converted(self):
        song = make_song()
        song["energy"] = "8"
        result = normalize_song(song)
        assert result["energy"] == 8

    def test_tags_string_converted_to_list(self):
        song = make_song()
        song["tags"] = "classic"
        result = normalize_song(song)
        assert isinstance(result["tags"], list)
        assert result["tags"] == ["classic"]

    def test_tags_list_preserved(self):
        song = make_song(tags=["rock", "classic"])
        result = normalize_song(song)
        assert result["tags"] == ["rock", "classic"]

    def test_missing_title_defaults_to_empty_string(self):
        song = {"artist": "Test", "genre": "pop", "energy": 5, "tags": []}
        result = normalize_song(song)
        assert result["title"] == ""

    def test_missing_energy_defaults_to_zero(self):
        song = {"title": "Test", "artist": "Test", "genre": "pop", "tags": []}
        result = normalize_song(song)
        assert result["energy"] == 0


# ---------------------------------------------------------------------------
# 6. Integration: build_playlists
# ---------------------------------------------------------------------------

class TestBuildPlaylists:

    def test_all_songs_are_placed_in_a_category(self):
        songs = [
            make_song(genre="rock", energy=9),    # Hype (genre=favorite + high energy)
            make_song(genre="pop", energy=2),     # Chill (low energy)
            make_song(genre="electronic", energy=5),  # Mixed
        ]
        profile = default_profile(favorite_genre="rock")
        playlists = build_playlists(songs, profile)
        total = len(playlists["Hype"]) + len(playlists["Chill"]) + len(playlists["Mixed"])
        assert total == len(songs)

    def test_songs_get_mood_field_assigned(self):
        songs = [make_song(genre="pop", energy=8)]
        playlists = build_playlists(songs, default_profile(favorite_genre="jazz"))
        assert playlists["Hype"][0]["mood"] == "Hype"

    def test_empty_songs_produces_empty_playlists(self):
        playlists = build_playlists([], DEFAULT_PROFILE)
        assert playlists == {"Hype": [], "Chill": [], "Mixed": []}
