# OpenWebUI Tools Lab

[![CI](https://github.com/matheusbuniotto/openwebui-tools/actions/workflows/ci.yml/badge.svg)](https://github.com/matheusbuniotto/openwebui-tools/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Python tools for [OpenWebUI](https://github.com/open-webui/open-webui). Each folder is a standalone tool you can paste into **Workspace → Tools → Create Tool**, with optional Valves for API keys and endpoints.

## Tools

| Tool | Description |
|------|-------------|
| [LLM Council](./llm_council_tool) | Runs a question through multiple models, ranks peer answers, and synthesizes a final reply. |
| [Spotify Vibe Controller](./spotify_tool) | Suggests Spotify playlists from mood and context in the chat. |
| [N8N Workflow Executor](./n8n_tool) | Calls an n8n webhook and returns the workflow result in chat. |
| [Pinecone RAG](./pinecone_rag_tool) | Embeds the query with OpenAI and searches a Pinecone index for context. |
| [Google Docs Templater](./docs_connector_tool) | Fills a Google Docs template via a Google Apps Script webhook. |

## Install a tool

1. Open the tool folder (for example, `llm_council_tool/`).
2. Copy the main `.py` file into OpenWebUI (**Workspace → Tools → + Create Tool**).
3. Set Valves in the UI (API keys, URLs, and so on).

## Contributing

Issues and pull requests are welcome.

Maintained by [matheusbuniotto](https://github.com/matheusbuniotto).