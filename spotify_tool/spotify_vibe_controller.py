"""
title: Spotify Vibe Controller
author: matheusbuniotto
funding_url: https://github.com/matheusbuniotto/openwebui-tools
version: 0.0.1
license: MIT
"""

import json
import time
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field
import requests


class SpotifyAuthError(Exception):
    """Raised when Spotify authentication fails."""

    pass


class SpotifyAPIError(Exception):
    """Raised when Spotify API call fails."""

    pass


class SpotifyAuthClient:
    """Handles Spotify OAuth2 authentication."""

    TOKEN_URL = "https://accounts.spotify.com/api/token"

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token: Optional[str] = None
        self.token_expires_at: float = 0

    def _is_token_valid(self) -> bool:
        """Checks if current token is still valid."""
        return self.access_token is not None and time.time() < self.token_expires_at

    def get_access_token(self) -> str:
        """Gets valid access token, refreshing if necessary."""
        if self._is_token_valid():
            return self.access_token

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        # Send credentials in body (matches curl command format)
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        try:
            response = requests.post(self.TOKEN_URL, headers=headers, data=data)

            if response.status_code != 200:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get("error_description", error_detail)
                except Exception:
                    pass
                raise SpotifyAuthError(
                    f"Authentication failed ({response.status_code}): {error_detail}"
                )

            token_data = response.json()
            self.access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            self.token_expires_at = time.time() + expires_in - 60

            return self.access_token
        except requests.exceptions.RequestException as e:
            raise SpotifyAuthError(f"Network error during authentication: {str(e)}")


class SemanticAnalyzer:
    """Analyzes text to extract mood, genre, and context for music curation."""

    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        self.api_url = "https://api.openai.com/v1/chat/completions"

    def analyze_context(self, text: str) -> Dict[str, Any]:
        """
        Analyzes text to extract musical context.
        Returns mood, genres, era, and search terms.
        """
        if not self.openai_api_key:
            return self._default_analysis(text)

        prompt = f"""Analyze this text and extract comprehensive musical context. Return JSON with:
- mood: emotional state (e.g., "cozy", "relaxed", "energetic", "nostalgic", "peaceful", "warm")
- activity: what the person is doing (e.g., "cooking", "reading", "working", "exercising", null)
- time_context: time of day or occasion (e.g., "morning", "evening", "sunday", "weekend", null)
- weather: weather conditions if mentioned (e.g., "rainy", "sunny", "cozy", null)
- genres: list of relevant music genres (e.g., ["jazz", "acoustic", "instrumental", "lofi"])
- era: time period if mentioned (e.g., "2000s", "90s", null)
- search_terms: list of 5-8 keywords for music search, combining mood, activity, and context (e.g., ["cooking music", "sunday morning", "rainy day", "cozy", "family"])

Extract all contextual clues: activities, time, weather, mood, setting. Be creative with search terms.

Text: "{text}"

Return ONLY valid JSON, no markdown."""

        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are a music curation assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.8,
            "max_tokens": 300,
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                return json.loads(content.strip())
        except Exception:
            pass

        return self._default_analysis(text)

    def _default_analysis(self, text: str) -> Dict[str, Any]:
        """Fallback analysis when OpenAI is unavailable."""
        text_lower = text.lower()
        mood = "neutral"
        activity = None
        time_context = None
        weather = None
        genres = []
        era = None
        search_terms = []

        # Mood detection
        if any(word in text_lower for word in ["nostalgic", "nostalgia", "remember"]):
            mood = "nostalgic"
            search_terms.append("nostalgic")
        elif any(word in text_lower for word in ["energetic", "energy", "pump"]):
            mood = "energetic"
            search_terms.append("energetic")
        elif any(word in text_lower for word in ["sad", "melancholic", "melancholy"]):
            mood = "melancholic"
            search_terms.append("melancholic")
        elif any(word in text_lower for word in ["cozy", "warm", "comfortable", "relaxed"]):
            mood = "cozy"
            search_terms.append("cozy")
        elif any(word in text_lower for word in ["peaceful", "calm", "serene"]):
            mood = "peaceful"
            search_terms.append("peaceful")

        # Activity detection
        if any(word in text_lower for word in ["cooking", "cook", "kitchen", "baking"]):
            activity = "cooking"
            search_terms.extend(["cooking music", "kitchen vibes"])
        elif any(word in text_lower for word in ["reading", "read", "book", "study"]):
            activity = "reading"
            search_terms.extend(["reading music", "study", "instrumental"])
        elif any(word in text_lower for word in ["working", "work", "focus"]):
            activity = "working"
            search_terms.extend(["focus", "work music", "productivity"])

        # Time context
        if any(word in text_lower for word in ["morning", "am", "dawn", "breakfast"]):
            time_context = "morning"
            search_terms.extend(["morning", "breakfast"])
        elif any(word in text_lower for word in ["evening", "pm", "dusk", "dinner"]):
            time_context = "evening"
            search_terms.extend(["evening", "dinner"])
        if any(word in text_lower for word in ["sunday", "weekend", "saturday"]):
            time_context = (time_context or "") + " weekend"
            search_terms.extend(["sunday", "weekend"])

        # Weather detection
        if any(word in text_lower for word in ["rain", "raining", "rainy", "drizzle"]):
            weather = "rainy"
            search_terms.extend(["rainy day", "rain", "cozy"])
        elif any(word in text_lower for word in ["sunny", "sun", "bright"]):
            weather = "sunny"
            search_terms.append("sunny")

        # Genre detection
        if "rpg" in text_lower:
            genres.append("rpg soundtracks")
            search_terms.append("RPG")
        if "2000" in text_lower or "2000s" in text_lower:
            era = "2000s"
            search_terms.append("2000s")
        if any(word in text_lower for word in ["jazz", "jazz music"]):
            genres.append("jazz")
            search_terms.append("jazz")
        if any(word in text_lower for word in ["acoustic", "acoustic guitar"]):
            genres.append("acoustic")
            search_terms.append("acoustic")

        # Extract meaningful words
        words = text.split()
        stop_words = {
            "i", "im", "i'm", "and", "a", "for", "of", "the", "to", "in", "is", "my", "me",
            "need", "currently", "playlist", "on", "at", "with", "family", "day"
        }
        for word in words:
            clean_word = word.strip(".,!?\"'")
            lower_word = clean_word.lower()
            if (lower_word not in stop_words and lower_word not in search_terms 
                and len(lower_word) > 2 and lower_word not in ["the", "and", "for"]):
                if lower_word not in ["nostalgic", "energetic", "sad", "reading", "cooking"]:
                    search_terms.append(clean_word)

        return {
            "mood": mood,
            "activity": activity,
            "time_context": time_context,
            "weather": weather,
            "genres": genres,
            "era": era,
            "search_terms": search_terms[:8] if search_terms else ["ambient", "relaxing"],
        }


class SpotifyAPIClient:
    """Handles Spotify Web API calls."""

    BASE_URL = "https://api.spotify.com/v1"

    def __init__(self, auth_client: SpotifyAuthClient):
        self.auth_client = auth_client

    def _get_headers(self) -> Dict[str, str]:
        """Gets headers with valid access token."""
        token = self.auth_client.get_access_token()
        return {"Authorization": f"Bearer {token}"}

    def search_tracks(
        self, query: str, limit: int = 20, market: str = "US"
    ) -> List[Dict[str, Any]]:
        """Searches for tracks matching the query."""
        headers = self._get_headers()
        params = {"q": query, "type": "track", "limit": limit, "market": market}

        response = requests.get(
            f"{self.BASE_URL}/search", headers=headers, params=params
        )

        if response.status_code != 200:
            raise SpotifyAPIError(
                f"Search failed: {response.status_code} - {response.text}"
            )

        return response.json().get("tracks", {}).get("items", [])

    def search_playlists(
        self, query: str, limit: int = 10, market: str = "US"
    ) -> List[Dict[str, Any]]:
        """Searches for playlists matching the query."""
        headers = self._get_headers()
        params = {"q": query, "type": "playlist", "limit": limit, "market": market}

        response = requests.get(
            f"{self.BASE_URL}/search", headers=headers, params=params
        )

        if response.status_code != 200:
            raise SpotifyAPIError(
                f"Search failed: {response.status_code} - {response.text}"
            )

        return response.json().get("playlists", {}).get("items", [])

    # def create_playlist(
    #     self, user_id: str, name: str, description: str = "", public: bool = False
    # ) -> Dict[str, Any]:
    #     """Creates a new playlist."""
    #     headers = self._get_headers()
    #     headers["Content-Type"] = "application/json"
    #     payload = {"name": name, "description": description, "public": public}
    #
    #     response = requests.post(
    #         f"{self.BASE_URL}/users/{user_id}/playlists",
    #         headers=headers,
    #         json=payload,
    #     )
    #
    #     if response.status_code not in [200, 201]:
    #         raise SpotifyAPIError(
    #             f"Playlist creation failed: {response.status_code} - {response.text}"
    #         )
    #
    #     return response.json()

    # def add_tracks_to_playlist(
    #     self, playlist_id: str, track_uris: List[str]
    # ) -> Dict[str, Any]:
    #     """Adds tracks to a playlist."""
    #     headers = self._get_headers()
    #     headers["Content-Type"] = "application/json"
    #     payload = {"uris": track_uris}
    #
    #     response = requests.post(
    #         f"{self.BASE_URL}/playlists/{playlist_id}/tracks",
    #         headers=headers,
    #         json=payload,
    #     )
    #
    #     if response.status_code not in [200, 201]:
    #         raise SpotifyAPIError(
    #             f"Add tracks failed: {response.status_code} - {response.text}"
    #         )
    #
    #     return response.json()

    def get_current_user(self) -> Dict[str, Any]:
        """Gets current user info (requires user auth, returns mock for now)."""
        return {"id": "default_user", "display_name": "OpenWebUI User"}


class PlaylistFinder:
    """Finds existing playlists based on mood and context."""

    def __init__(self, api_client: SpotifyAPIClient):
        self.api_client = api_client

    def find_mood_playlist(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Finds playlists based on mood and context."""
        mood = context.get("mood", "neutral")
        activity = context.get("activity")
        time_context = context.get("time_context")
        weather = context.get("weather")
        genres = context.get("genres", [])
        era = context.get("era")
        search_terms = context.get("search_terms", [])

        # Construct intelligent search queries combining all context
        queries = []
        
        # 1. Full context combination (most specific)
        full_context_parts = []
        if activity:
            full_context_parts.append(activity)
        if time_context:
            full_context_parts.append(time_context)
        if weather:
            full_context_parts.append(weather)
        if mood and mood != "neutral":
            full_context_parts.append(mood)
        
        if len(full_context_parts) >= 2:
            queries.append(" ".join(full_context_parts))
        
        # 2. Activity + Time + Mood
        if activity and time_context and mood != "neutral":
            queries.append(f"{activity} {time_context} {mood}")
        
        # 3. Activity + Weather
        if activity and weather:
            queries.append(f"{activity} {weather}")
        
        # 4. Time + Weather + Mood
        if time_context and weather and mood != "neutral":
            queries.append(f"{time_context} {weather} {mood}")
        
        # 5. Activity + Mood
        if activity and mood != "neutral":
            queries.append(f"{activity} {mood}")
        
        # 6. Weather + Mood
        if weather and mood != "neutral":
            queries.append(f"{weather} {mood}")
        
        # 7. Era + Genre combinations
        if era and genres:
            queries.append(f"{mood} {era} {genres[0]}")
        elif genres:
            queries.append(f"{mood} {genres[0]}")
        elif era:
            queries.append(f"{mood} {era}")
        
        # 8. Direct search terms (prioritize longer, more specific ones)
        prioritized_terms = sorted(search_terms, key=len, reverse=True)
        queries.extend(prioritized_terms[:5])
        
        # 9. Fallback: mood vibe
        if mood != "neutral":
            queries.append(f"{mood} vibe")
            queries.append(f"{mood} music")

        found_playlists = []
        seen_ids = set()

        # Search with multiple queries
        for query in queries[:10]:  # Limit to 10 queries
            try:
                playlists = self.api_client.search_playlists(query, limit=5)
                for playlist in playlists:
                    if not playlist:
                        continue
                    p_id = playlist.get("id")
                    if p_id and p_id not in seen_ids:
                        found_playlists.append(playlist)
                        seen_ids.add(p_id)
            except Exception:
                continue
            
            # If we found enough playlists, stop searching
            if len(found_playlists) >= 8:
                break

        # Also search for tracks as fallback/complement
        track_suggestions = []
        if len(found_playlists) < 3:
            # If we don't have many playlists, also search for tracks
            for query in queries[:3]:
                try:
                    tracks = self.api_client.search_tracks(query, limit=10)
                    track_suggestions.extend(tracks[:5])
                except Exception:
                    continue

        if not found_playlists and not track_suggestions:
            return {
                "found": False,
                "error": "No playlists or tracks found matching the vibe."
            }

        result = {
            "found": len(found_playlists) > 0,
            "playlists": found_playlists[:5],  # Top 5 playlists
            "track_suggestions": track_suggestions[:10] if track_suggestions else [],
        }
        
        if found_playlists:
            best_match = found_playlists[0]
            result.update({
                "playlist_name": best_match.get("name"),
                "playlist_url": best_match.get("external_urls", {}).get("spotify"),
                "description": best_match.get("description"),
                "image_url": best_match.get("images", [{}])[0].get("url") if best_match.get("images") else None,
                "owner": best_match.get("owner", {}).get("display_name"),
                "total_tracks": best_match.get("tracks", {}).get("total"),
                "alternatives": found_playlists[1:5]  # Top 4 alternatives
            })
        
        return result


class Tools:
    """
    Spotify Vibe Controller for OpenWebUI.
    Creates and plays music playlists based on semantic context from chat.
    """

    class Valves(BaseModel):
        SPOTIFY_CLIENT_ID: str = Field(
            default="", description="Your Spotify Client ID."
        )
        SPOTIFY_CLIENT_SECRET: str = Field(
            default="", description="Your Spotify Client Secret."
        )
        OPENAI_API_KEY: str = Field(
            default="",
            description="OpenAI API key for semantic analysis (optional).",
        )
        SPOTIFY_USER_ID: str = Field(
            default="",
            description="Spotify User ID (optional, for playlist creation).",
        )

    def __init__(self):
        self.valves = self.Valves()
        self._auth_client: Optional[SpotifyAuthClient] = None
        self._api_client: Optional[SpotifyAPIClient] = None
        self._semantic_analyzer: Optional[SemanticAnalyzer] = None
        self._playlist_finder: Optional[PlaylistFinder] = None

    def _initialize_clients(self):
        """Lazy initialization of clients."""
        if not self._auth_client:
            if not self.valves.SPOTIFY_CLIENT_ID or not self.valves.SPOTIFY_CLIENT_SECRET:
                raise ValueError(
                    "Spotify credentials are missing. Check the tool Valves."
                )
            self._auth_client = SpotifyAuthClient(
                self.valves.SPOTIFY_CLIENT_ID, self.valves.SPOTIFY_CLIENT_SECRET
            )
            self._api_client = SpotifyAPIClient(self._auth_client)
            self._semantic_analyzer = SemanticAnalyzer(self.valves.OPENAI_API_KEY)
            self._playlist_finder = PlaylistFinder(self._api_client)

    async def find_vibe_playlist(
        self,
        context_text: str,
        __event_emitter__: Optional[Any] = None,
    ) -> str:
        """
        Finds a Spotify playlist based on the semantic context of the conversation.
        Example: "I'm feeling nostalgic about 2000s RPG games" finds a relevant playlist.
        
        :param context_text: The text describing the mood, context, or desired music vibe.
        :param __event_emitter__: Optional event emitter for status updates in the UI.
        :return: A formatted string with playlist details and results.
        """
        await self._emit_status(
            __event_emitter__, "start", "Analyzing context...", False
        )

        try:
            self._initialize_clients()

            await self._emit_status(
                __event_emitter__, "analyzing", "Extracting mood and context...", False
            )
            context = self._semantic_analyzer.analyze_context(context_text)

            await self._emit_status(
                __event_emitter__, "searching", "Searching for matching playlists...", False
            )
            result = self._playlist_finder.find_mood_playlist(context)

            playlists = result.get("playlists", [])
            track_suggestions = result.get("track_suggestions", [])
            
            if playlists:
                # Found playlists
                await self._emit_status(
                    __event_emitter__,
                    "complete",
                    f"Found {len(playlists)} matching playlist(s)!",
                    True,
                )
                
                # Build response with all playlists
                response_parts = [f"🎵 **Found {len(playlists)} playlist(s) for your vibe:**\n"]
                
                for i, playlist in enumerate(playlists[:5], 1):
                    name = playlist.get("name", "Unknown")
                    # Get URL from multiple possible locations
                    url = (
                        playlist.get("external_urls", {}).get("spotify") or
                        playlist.get("href", "").replace("/v1/playlists/", "https://open.spotify.com/playlist/") or
                        f"https://open.spotify.com/playlist/{playlist.get('id', '')}"
                    )
                    owner = playlist.get("owner", {}).get("display_name", "Unknown")
                    total = playlist.get("tracks", {}).get("total", 0)
                    description = playlist.get("description", "")
                    
                    # Always show the link prominently and avoid Markdown links on titles to prevent stripping
                    if url:
                        response_parts.append(
                            f"\n**{i}. {name}**\n"
                            f"Link: {url}\n"
                            f"👤 By: {owner} | 🎵 {total} tracks"
                        )
                    else:
                        # Fallback if URL is somehow missing
                        playlist_id = playlist.get("id", "")
                        fallback_url = f"https://open.spotify.com/playlist/{playlist_id}" if playlist_id else ""
                        response_parts.append(
                            f"\n**{i}. {name}**\n"
                            f"Link: {fallback_url}\n"
                            f"👤 By: {owner} | 🎵 {total} tracks"
                        )
                    if description:
                        response_parts.append(f"📝 {description[:100]}...")
                
                # Add track suggestions if available
                if track_suggestions:
                    response_parts.append(f"\n\n🎶 **Track Suggestions:**\n")
                    for i, track in enumerate(track_suggestions[:10], 1):
                        artists = ", ".join([a["name"] for a in track.get("artists", [])])
                        # Get track URL from multiple possible locations
                        track_url = (
                            track.get("external_urls", {}).get("spotify") or
                            track.get("href", "").replace("/v1/tracks/", "https://open.spotify.com/track/") or
                            f"https://open.spotify.com/track/{track.get('id', '')}"
                        )
                        if track_url:
                            response_parts.append(
                                f"{i}. **{track['name']}** by {artists}\n"
                                f"   🔗 {track_url}"
                            )
                        else:
                            response_parts.append(
                                f"{i}. **{track['name']}** by {artists}"
                            )
                
                # Add context summary
                context_summary = []
                if context.get("activity"):
                    context_summary.append(f"activity: {context['activity']}")
                if context.get("time_context"):
                    context_summary.append(f"time: {context['time_context']}")
                if context.get("weather"):
                    context_summary.append(f"weather: {context['weather']}")
                if context.get("mood") and context.get("mood") != "neutral":
                    context_summary.append(f"mood: {context['mood']}")
                
                if context_summary:
                    response_parts.append(f"\n\n*Context: {', '.join(context_summary)}*")
                
                return "\n".join(response_parts)
                
            elif track_suggestions:
                # Only track suggestions available
                await self._emit_status(
                    __event_emitter__,
                    "complete",
                    f"Found {len(track_suggestions)} matching tracks!",
                    True,
                )
                
                response_parts = [
                    f"🎶 **Found {len(track_suggestions)} track(s) matching your vibe:**\n"
                ]
                
                for i, track in enumerate(track_suggestions[:15], 1):
                    artists = ", ".join([a["name"] for a in track.get("artists", [])])
                    # Get track URL from multiple possible locations
                    track_url = (
                        track.get("external_urls", {}).get("spotify") or
                        track.get("href", "").replace("/v1/tracks/", "https://open.spotify.com/track/") or
                        f"https://open.spotify.com/track/{track.get('id', '')}"
                    )
                    if track_url:
                        response_parts.append(
                            f"{i}. **{track['name']}** by {artists}\n"
                            f"   🔗 {track_url}"
                        )
                    else:
                        response_parts.append(
                            f"{i}. **{track['name']}** by {artists}"
                        )
                
                # Add context summary
                context_summary = []
                if context.get("activity"):
                    context_summary.append(f"activity: {context['activity']}")
                if context.get("time_context"):
                    context_summary.append(f"time: {context['time_context']}")
                if context.get("weather"):
                    context_summary.append(f"weather: {context['weather']}")
                if context.get("mood") and context.get("mood") != "neutral":
                    context_summary.append(f"mood: {context['mood']}")
                
                if context_summary:
                    response_parts.append(f"\n*Context: {', '.join(context_summary)}*")
                
                return "\n".join(response_parts)
            else:
                # Nothing found
                await self._emit_status(
                    __event_emitter__,
                    "complete",
                    "No matching playlists or tracks found.",
                    True,
                )

                return (
                    f"❌ No playlists or tracks found matching your vibe.\n\n"
                    f"💡 **Try:**\n"
                    f"- Being more specific (e.g., 'jazz for cooking')\n"
                    f"- Using different keywords\n"
                    f"- Describing the mood or activity more clearly\n\n"
                    f"*Analyzed: {context.get('mood', 'neutral')} mood, "
                    f"{', '.join(context.get('genres', [])) or 'various genres'}*"
                )

        except ValueError as e:
            await self._emit_status(
                __event_emitter__, "error", str(e), True
            )
            return f"❌ Configuration Error: {str(e)}"
        except SpotifyAuthError as e:
            await self._emit_status(
                __event_emitter__, "error", "Authentication failed", True
            )
            return f"❌ Spotify Authentication Error: {str(e)}"
        except SpotifyAPIError as e:
            await self._emit_status(
                __event_emitter__, "error", "API request failed", True
            )
            return f"❌ Spotify API Error: {str(e)}"
        except Exception as e:
            await self._emit_status(
                __event_emitter__, "error", f"Unexpected error: {str(e)}", True
            )
            return f"❌ Error: {str(e)}"

    async def _emit_status(
        self,
        handler: Optional[Any],
        status_id: str,
        description: str,
        done: bool,
    ):
        """Sends visual updates to the Chat UI."""
        if handler:
            await handler(
                {
                    "type": "status",
                    "data": {"description": description, "done": done},
                }
            )

