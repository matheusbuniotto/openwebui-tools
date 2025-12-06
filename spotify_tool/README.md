# 🎵 Spotify Vibe Controller for OpenWebUI

![Spotify](https://img.shields.io/badge/Spotify-1DB954?style=for-the-badge&logo=spotify&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-Embeddings-blue?style=for-the-badge&logo=openai)
![Python](https://img.shields.io/badge/Python-3.10+-yellow?style=for-the-badge&logo=python)

> **Curate music playlists based on semantic context from your chat!** 🎶✨

This tool integrates **Spotify** into **OpenWebUI**, allowing your agents to create and play music playlists based on the semantic context of conversations. Say "I'm feeling nostalgic about 2000s RPG games" and it automatically creates a playlist with relevant soundtracks from that era!

---

## 🚀 Features

- **🧠 Semantic Analysis**: Extracts mood, genre, and context from chat conversations
- **🎵 Smart Playlist Creation**: Automatically creates Spotify playlists based on context
- **🔍 Intelligent Search**: Finds tracks matching the extracted mood and keywords
- **🤖 OpenAI Integration**: Uses GPT for advanced semantic understanding (optional, with fallback)
- **⚡ Real-time Feedback**: Provides visual status updates in the OpenWebUI chat
- **🛠️ Easy Configuration**: Just plug in your API keys directly in the UI

---

## ⚙️ Configuration (Valves)

Once installed, configure the tool in **OpenWebUI > Workspace > Tools > Valves**:

| Valve | Description | Required |
| :--- | :--- | :--- |
| **SPOTIFY_CLIENT_ID** | Your Spotify App Client ID from [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) | ✅ Yes |
| **SPOTIFY_CLIENT_SECRET** | Your Spotify App Client Secret | ✅ Yes |
| **OPENAI_API_KEY** | OpenAI API key for semantic analysis (optional, has fallback) | ❌ No |
| **SPOTIFY_USER_ID** | Your Spotify User ID (optional, for playlist creation) | ❌ No |

### Getting Spotify Credentials

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app or select an existing one
3. Copy the **Client ID** and **Client Secret**
4. Note: This uses **Client Credentials** flow (no user authorization required for search)

### Getting Your Spotify User ID

The User ID is **optional** and only needed if you want to create playlists in your account. Here are ways to find it:

**Method 1: Spotify Web Player (Easiest)**
1. Go to [open.spotify.com](https://open.spotify.com) and log in
2. Click on your profile name/avatar
3. Look at the URL - it will be: `https://open.spotify.com/user/YOUR_USER_ID_HERE`
4. Copy the part after `/user/` - that's your User ID

**Method 2: Spotify Desktop App**
1. Open Spotify desktop app
2. Click on your profile name/avatar
3. Right-click → "Copy profile link"
4. The link contains your User ID: `https://open.spotify.com/user/YOUR_USER_ID_HERE`

**Method 3: Spotify API**
- If you have an access token, call: `GET https://api.spotify.com/v1/me`
- The response includes your `id` field

**Note:** Your User ID is a long string of letters and numbers (e.g., `31abc123def456ghi789jkl012mno345pq`). It's different from your username!

---

## 📦 Installation

1. Open **OpenWebUI**
2. Go to **Workspace** > **Tools**
3. Click **+ Create Tool**
4. Copy the content of `spotify_vibe_controller.py` and paste it into the editor
5. Save and enable the tool in your agent!

---

## 💡 Usage Examples

### Example 1: Mood-Based Playlist
```
User: "I'm feeling nostalgic, remembering RPG games from the 2000s"
Agent: Creates playlist "Vibe: Nostalgic (2000s)" with RPG soundtracks
```

### Example 2: Context Matching
```
User: "Play music that matches the melancholic tone of the text I just generated"
Agent: Analyzes the text, extracts mood, and creates matching playlist
```

### Example 3: Energetic Vibes
```
User: "I need energetic music to get pumped up!"
Agent: Creates "Vibe: Energetic" playlist with high-energy tracks
```

---

## 🔧 How it Works

1. **User provides context** (e.g., "feeling nostalgic about 2000s RPGs")
2. **Semantic Analysis**: Tool extracts:
   - Mood (nostalgic, energetic, melancholic, etc.)
   - Genres (RPG soundtracks, etc.)
   - Era (2000s, 90s, etc.)
   - Search terms (keywords for music search)
3. **Track Search**: Searches Spotify for tracks matching the context
4. **Playlist Creation**: Creates a new playlist and adds matching tracks
5. **Returns**: Playlist name, track count, and Spotify link

---

## 🏗️ Architecture

The tool follows clean code principles with modular, single-responsibility classes:

- **`SpotifyAuthClient`**: Handles OAuth2 authentication and token management
- **`SemanticAnalyzer`**: Analyzes text to extract musical context (with OpenAI or fallback)
- **`SpotifyAPIClient`**: Wraps Spotify Web API calls
- **`PlaylistManager`**: Manages playlist creation and curation logic
- **`Tools`**: Main OpenWebUI integration class

---

## 🧪 Testing

Install test dependencies:

```bash
pip install -r requirements.txt
```

Run the test suite:

```bash
cd spotify_tool
pytest test_spotify_vibe_controller.py -v
```

Tests follow TDD methodology with comprehensive coverage of all components.

---

## 📝 Limitations

- **Client Credentials Flow**: Currently uses app-only authentication (no user playlists)
- **Playlist Creation**: Requires user authentication for full playlist management (future enhancement)
- **Search Only**: Focuses on search and playlist creation; playback control requires additional setup

---

## 🔮 Future Enhancements

- User authentication flow for personal playlist management
- Direct playback control (play, pause, skip)
- Integration with Plex/Jellyfin for local media
- Advanced mood detection with multiple LLM providers
- Playlist persistence and history

---

## 📝 License

MIT License. Feel free to use and modify!

---

*Created with ❤️ by [matheusbuniotto](https://github.com/matheusbuniotto)*

