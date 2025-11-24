"""
title: Google Docs Script Connector
author: matheusbuniotto
funding_url:  https://github.com/matheusbuniotto/openwebui-tools
version: 0.0.1
license: MIT
"""

import requests
import json
from pydantic import BaseModel, Field
from typing import Callable, Any


class Tools:
    """
    This tool connects to a Google Apps Script Web App to create Google Docs based on a template.
    It replaces placeholders in the template with provided values. For this to work, you need to
    add a App script into you google docs file.
    """

    class Valves(BaseModel):
        # Here you should pastes the link copied from Google Apps Script
        DOCS_WEBHOOK_URL: str = Field(
            default="",
            description="Paste here the 'Web App' URL generated in Google Apps Script.",
        )

    def __init__(self):
        self.valves = self.Valves()

    async def create_google_doc(
        self,
        filename: str,
        replacements_json: str,
        __event_emitter__: Callable[[dict], Any] = None,
    ) -> str:
        """
        Creates a new Google Doc based on the configured template, replacing the requested text.

        :param filename: The name of the new file.
        :param replacements_json: JSON with the replacements. Ex: {"{client}": "Company X", "{value}": "$ 500"}
        """

        # Simple validation
        if not self.valves.DOCS_WEBHOOK_URL:
            return "Error: You need to configure the Webhook URL in the tool settings (Valves)."

        await self._emit_status(
            __event_emitter__, "start", "Sending data to Google...", False
        )

        try:
            # Prepare the data
            payload = {
                "filename": filename,
                "replacements": json.loads(replacements_json),
            }

            # Send to your Google Script
            response = requests.post(self.valves.DOCS_WEBHOOK_URL, json=payload)

            if response.status_code != 200:
                raise Exception(f"Connection error: {response.text}")

            result = response.json()

            if result.get("status") == "error":
                raise Exception(result.get("message"))

            doc_url = result.get("url")

            await self._emit_status(
                __event_emitter__, "complete", "Document created!", True
            )

            return f"Success! The document was created.\n\n**Name:** {filename}\n**Access here:** [Open Document]({doc_url})"

        except Exception as e:
            await self._emit_status(
                __event_emitter__, "error", f"Error: {str(e)}", True
            )
            return f"Failed to create document: {str(e)}"

    async def _emit_status(self, handler, status_id, description, done):
        if handler:
            await handler(
                {"type": "status", "data": {"description": description, "done": done}}
            )
