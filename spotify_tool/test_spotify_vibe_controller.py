"""
Unit tests for Spotify Vibe Controller.
Following TDD methodology with RED and GREEN tests.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from spotify_vibe_controller import (
    SpotifyAuthClient,
    SemanticAnalyzer,
    SpotifyAPIClient,
    SpotifyAPIClient,
    PlaylistFinder,
    Tools,
    SpotifyAuthError,
    SpotifyAPIError,
)

try:
    import pytest_asyncio
    pytestmark = pytest.mark.asyncio
except ImportError:
    # If pytest-asyncio is not available, skip async tests
    pytestmark = pytest.mark.skip(reason="pytest-asyncio not installed")


class TestSpotifyAuthClient:
    """Tests for SpotifyAuthClient."""

    def test_init(self):
        """Test client initialization."""
        client = SpotifyAuthClient("test_id", "test_secret")
        assert client.client_id == "test_id"
        assert client.client_secret == "test_secret"
        assert client.access_token is None

    @patch("spotify_vibe_controller.requests.post")
    def test_get_access_token_success(self, mock_post):
        """Test successful token retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_token",
            "expires_in": 3600,
        }
        mock_post.return_value = mock_response

        client = SpotifyAuthClient("test_id", "test_secret")
        token = client.get_access_token()

        assert token == "test_token"
        assert client.access_token == "test_token"
        assert client.token_expires_at > time.time()

    @patch("spotify_vibe_controller.requests.post")
    def test_get_access_token_failure(self, mock_post):
        """Test token retrieval failure."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response

        client = SpotifyAuthClient("test_id", "test_secret")

        with pytest.raises(SpotifyAuthError):
            client.get_access_token()

    @patch("spotify_vibe_controller.requests.post")
    def test_token_caching(self, mock_post):
        """Test that valid tokens are cached."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_token",
            "expires_in": 3600,
        }
        mock_post.return_value = mock_response

        client = SpotifyAuthClient("test_id", "test_secret")
        token1 = client.get_access_token()
        token2 = client.get_access_token()

        assert token1 == token2
        assert mock_post.call_count == 1


class TestSemanticAnalyzer:
    """Tests for SemanticAnalyzer."""

    def test_init(self):
        """Test analyzer initialization."""
        analyzer = SemanticAnalyzer("test_key")
        assert analyzer.openai_api_key == "test_key"

    def test_default_analysis_nostalgic(self):
        """Test default analysis for nostalgic text."""
        analyzer = SemanticAnalyzer("")
        result = analyzer.analyze_context("I'm feeling nostalgic about RPG games")

        assert result["mood"] == "nostalgic"
        assert "rpg soundtracks" in result["genres"]
        assert "nostalgic" in result["search_terms"]

    def test_default_analysis_energetic(self):
        """Test default analysis for energetic text."""
        analyzer = SemanticAnalyzer("")
        result = analyzer.analyze_context("I need energetic music to pump me up")

        assert result["mood"] == "energetic"
        assert "energetic" in result["search_terms"]

    def test_default_analysis_melancholic(self):
        """Test default analysis for melancholic text."""
        analyzer = SemanticAnalyzer("")
        result = analyzer.analyze_context("I'm feeling sad and melancholic")

        assert result["mood"] == "melancholic"
        assert "melancholic" in result["search_terms"]

    def test_default_analysis_reading(self):
        """Test default analysis for reading context with specific subject."""
        analyzer = SemanticAnalyzer("")
        result = analyzer.analyze_context("Im currently reading tolkien and i need a playlist")

        # This is what we WANT to happen
        assert result["activity"] == "reading"
        assert "reading music" in result["search_terms"]
        assert "tolkien" in result["search_terms"] or "Tolkien" in result["search_terms"]

    @patch("spotify_vibe_controller.requests.post")
    def test_openai_analysis_success(self, mock_post):
        """Test OpenAI analysis when available."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": '{"mood": "nostalgic", "genres": ["rpg"], "era": "2000s", "search_terms": ["RPG", "2000s"]}'
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        analyzer = SemanticAnalyzer("test_key")
        result = analyzer.analyze_context("nostalgic RPG games")

        assert result["mood"] == "nostalgic"
        assert "rpg" in result["genres"]

    @patch("spotify_vibe_controller.requests.post")
    def test_openai_analysis_fallback(self, mock_post):
        """Test fallback to default analysis on OpenAI failure."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        analyzer = SemanticAnalyzer("test_key")
        result = analyzer.analyze_context("nostalgic RPG games")

        assert result["mood"] == "nostalgic"
        assert isinstance(result["search_terms"], list)


class TestSpotifyAPIClient:
    """Tests for SpotifyAPIClient."""

    def test_init(self):
        """Test API client initialization."""
        auth_client = Mock(spec=SpotifyAuthClient)
        api_client = SpotifyAPIClient(auth_client)
        assert api_client.auth_client == auth_client

    @patch("spotify_vibe_controller.requests.get")
    def test_search_tracks_success(self, mock_get):
        """Test successful track search."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tracks": {
                "items": [
                    {"id": "track1", "name": "Track 1", "uri": "spotify:track:1"},
                    {"id": "track2", "name": "Track 2", "uri": "spotify:track:2"},
                ]
            }
        }
        mock_get.return_value = mock_response

        auth_client = Mock(spec=SpotifyAuthClient)
        auth_client.get_access_token.return_value = "test_token"
        api_client = SpotifyAPIClient(auth_client)

        tracks = api_client.search_tracks("test query")

        assert len(tracks) == 2
        assert tracks[0]["id"] == "track1"

    @patch("spotify_vibe_controller.requests.get")
    def test_search_tracks_failure(self, mock_get):
        """Test track search failure."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_get.return_value = mock_response

        auth_client = Mock(spec=SpotifyAuthClient)
        auth_client.get_access_token.return_value = "test_token"
        api_client = SpotifyAPIClient(auth_client)

        with pytest.raises(SpotifyAPIError):
            api_client.search_tracks("test query")

    @patch("spotify_vibe_controller.requests.get")
    def test_search_playlists_success(self, mock_get):
        """Test successful playlist search."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "playlists": {
                "items": [
                    {"id": "playlist1", "name": "Playlist 1", "uri": "spotify:playlist:1"},
                    {"id": "playlist2", "name": "Playlist 2", "uri": "spotify:playlist:2"},
                ]
            }
        }
        mock_get.return_value = mock_response

        auth_client = Mock(spec=SpotifyAuthClient)
        auth_client.get_access_token.return_value = "test_token"
        api_client = SpotifyAPIClient(auth_client)

        playlists = api_client.search_playlists("test query")

        assert len(playlists) == 2
        assert playlists[0]["id"] == "playlist1"


class TestPlaylistFinder:
    """Tests for PlaylistFinder."""

    def test_find_mood_playlist(self):
        """Test mood playlist finding."""
        api_client = Mock(spec=SpotifyAPIClient)
        api_client.search_playlists.return_value = [
            {
                "id": "playlist123",
                "name": "Nostalgic Vibes",
                "external_urls": {"spotify": "https://spotify.com/playlist/123"},
                "description": "A nostalgic playlist",
                "owner": {"display_name": "Spotify"},
                "tracks": {"total": 50},
            }
        ]

        finder = PlaylistFinder(api_client)

        context = {
            "mood": "nostalgic",
            "genres": ["rpg"],
            "era": "2000s",
            "search_terms": ["RPG", "2000s"],
        }

        result = finder.find_mood_playlist(context)

        assert result["found"] is True
        assert result["playlist_name"] == "Nostalgic Vibes"
        assert result["total_tracks"] == 50


class TestTools:
    """Tests for main Tools class."""

    def test_init(self):
        """Test Tools initialization."""
        tools = Tools()
        assert tools.valves is not None
        assert tools._auth_client is None

    async def test_create_vibe_playlist_missing_credentials(self):
        """Test playlist creation with missing credentials."""
        tools = Tools()
        tools.valves.SPOTIFY_CLIENT_ID = ""
        tools.valves.SPOTIFY_CLIENT_SECRET = ""

        result = await tools.find_vibe_playlist("test context")

        assert "Configuration Error" in result
        assert "missing" in result.lower()

    @patch("spotify_vibe_controller.SpotifyAuthClient.get_access_token")
    @patch("spotify_vibe_controller.SpotifyAPIClient.search_playlists")
    async def test_find_vibe_playlist_success(
        self, mock_search, mock_token
    ):
        """Test successful vibe playlist finding."""
        mock_token.return_value = "test_token"
        mock_search.return_value = [
            {
                "id": "playlist123",
                "name": "Vibe: Nostalgic",
                "external_urls": {"spotify": "https://spotify.com/playlist/123"},
                "description": "A nostalgic playlist",
                "owner": {"display_name": "Spotify"},
                "tracks": {"total": 50},
            }
        ]

        tools = Tools()
        tools.valves.SPOTIFY_CLIENT_ID = "test_id"
        tools.valves.SPOTIFY_CLIENT_SECRET = "test_secret"

        result = await tools.find_vibe_playlist("I'm feeling nostalgic")

        assert "Found 1 playlist(s)" in result
        assert "Link: https" in result
        assert "Nostalgic" in result

    async def test_emit_status(self):
        """Test status emission."""
        tools = Tools()
        mock_emitter = AsyncMock()

        await tools._emit_status(mock_emitter, "test", "Test message", True)

        mock_emitter.assert_called_once()
        call_args = mock_emitter.call_args[0][0]
        assert call_args["type"] == "status"
        assert call_args["data"]["description"] == "Test message"
        assert call_args["data"]["done"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

