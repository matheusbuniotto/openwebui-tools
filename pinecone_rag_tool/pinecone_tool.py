"""
title: Pinecone RAG Tool
author: matheusbuniotto
funding_url: https://github.com/matheusbuniotto/openwebui-tools
version: 0.0.1
license: MIT
"""

import requests
from pydantic import BaseModel, Field
from typing import Callable, Any


class Tools:
    """
    This tool allows you to perform RAG (Retrieval-Augmented Generation) using Pinecone as a vector database.
    It converts the user's query into a vector using OpenAI's embedding model and searches for relevant documents in the specified Pinecone index.
    """

    class Valves(BaseModel):
        # Manual Configurations (Valves) - Copy and paste your keys here via the panel
        PINECONE_API_KEY: str = Field(default="", description="Your Pinecone API Key.")
        PINECONE_INDEX_NAME: str = Field(
            default="", description="The name of your Pinecone Index."
        )
        OPENAI_API_KEY: str = Field(
            default="",
            description="Your OpenAI Key (sk-...) to generate embeddings.",
        )
        TOP_K: int = Field(
            default=5, description="Number of documents to return in the search."
        )

    def __init__(self):
        self.valves = self.Valves()
        self.cached_host = None

    async def query_pinecone(
        self, query: str, __event_emitter__: Callable[[dict], Any] = None
    ) -> str:
        """
        RAG Tool for Pinecone.
        Converts the question into a vector (OpenAI) and searches in the specified Pinecone index.
        """

        # 1. UX: Notify start
        await self._emit_status(
            __event_emitter__, "start", "Connecting to APIs...", False
        )

        try:
            # Key Validation
            if not self.valves.PINECONE_API_KEY or not self.valves.PINECONE_INDEX_NAME:
                return "Error: Pinecone settings are missing. Check the tool Valves."

            if not self.valves.OPENAI_API_KEY:
                return "Error: OpenAI key is missing. Check the tool Valves."

            # 2. Host Discovery
            # Fetches the real database address if we don't have it cached yet
            if not self.cached_host:
                await self._emit_status(
                    __event_emitter__,
                    "discovery",
                    f"Locating database '{self.valves.PINECONE_INDEX_NAME}'...",
                    False,
                )
                self.cached_host = self._fetch_index_host(
                    self.valves.PINECONE_API_KEY, self.valves.PINECONE_INDEX_NAME
                )

            # 3. Generate Embedding (Text -> Vector)
            await self._emit_status(
                __event_emitter__, "embedding", "Generating search vectors...", False
            )

            embedding_headers = {
                "Authorization": f"Bearer {self.valves.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            }
            # The model must be compatible with the one used in database creation
            embedding_payload = {"input": query, "model": "text-embedding-3-small"}

            emb_response = requests.post(
                "https://api.openai.com/v1/embeddings",
                headers=embedding_headers,
                json=embedding_payload,
            )

            if emb_response.status_code != 200:
                raise Exception(
                    f"OpenAI Error ({emb_response.status_code}): {emb_response.text}"
                )

            vector = emb_response.json()["data"][0]["embedding"]

            # 4. Search in Pinecone (Vector -> Context)
            await self._emit_status(
                __event_emitter__, "searching", "Querying Pinecone...", False
            )

            pinecone_url = f"https://{self.cached_host}/query"
            pinecone_headers = {
                "Api-Key": self.valves.PINECONE_API_KEY,
                "Content-Type": "application/json",
            }
            pinecone_payload = {
                "vector": vector,
                "topK": self.valves.TOP_K,
                "includeMetadata": True,
                "includeValues": False,
            }

            response = requests.post(
                pinecone_url, headers=pinecone_headers, json=pinecone_payload
            )

            if response.status_code != 200:
                # If it fails, clear the host cache to try rediscovery next time
                self.cached_host = None
                raise Exception(f"Pinecone Error: {response.text}")

            matches = response.json().get("matches", [])

            # 5. Format Response
            if not matches:
                await self._emit_status(
                    __event_emitter__,
                    "empty",
                    "No relevant documents found.",
                    True,
                )
                return "No relevant information was found in the database to answer this question."

            contexts = []
            for match in matches:
                metadata = match.get("metadata", {})
                # Tries to extract text from several common fields
                text = (
                    metadata.get("text")
                    or metadata.get("content")
                    or metadata.get("context")
                    or str(metadata)
                )
                contexts.append(
                    f"--- Document (Relevance: {match['score']:.2f}) ---\n{text}"
                )

            final_context = "\n\n".join(contexts)

            await self._emit_status(
                __event_emitter__,
                "complete",
                f"Success: {len(matches)} documents retrieved.",
                True,
            )
            return f"Context retrieved from Pinecone:\n{final_context}"

        except Exception as e:
            await self._emit_status(
                __event_emitter__, "error", f"Technical Error: {str(e)}", True
            )
            return f"An error occurred while searching the knowledge base: {str(e)}"

    def _fetch_index_host(self, api_key, index_name):
        """Discovers the host URL based on the index name."""
        url = "https://api.pinecone.io/indexes"
        headers = {"Api-Key": api_key}

        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            raise Exception(f"Failed to list indexes: {resp.text}")

        data = resp.json()
        for idx in data.get("indexes", []):
            if idx.get("name") == index_name:
                return idx.get("host")

        raise Exception(
            f"Index '{index_name}' not found in the provided Pinecone account."
        )

    async def _emit_status(self, handler, status_id, description, done):
        """Sends visual updates to the Chat UI."""
        if handler:
            await handler(
                {"type": "status", "data": {"description": description, "done": done}}
            )
