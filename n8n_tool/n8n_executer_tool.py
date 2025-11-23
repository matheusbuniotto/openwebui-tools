"""
title: N8N Tool
author: matheusbuniotto
funding_url: https://github.com/matheusbuniotto/openwebui-tools
version: 0.0.1
license: MIT
"""

from typing import Optional, Callable, Awaitable
from pydantic import BaseModel, Field
import requests
import time
import json


class Tools:
    """
    This module defines a Tools class that utilizes N8N for an Agent.
    Based on the original work by Cole Medin.
    """
    class Valves(BaseModel):
        n8n_url: str = Field(default="http://n8n-ui:5678/webhook/invoke-n8n-agent")
        n8n_bearer_token: str = Field(default="")
        input_field: str = Field(default="chatInput")
        response_field: str = Field(default="output")
        emit_interval: float = Field(
            default=2.0, description="Interval in seconds between status emissions"
        )
        enable_status_indicator: bool = Field(
            default=True, description="Enable or disable status indicator emissions"
        )

    def __init__(self):
        self.valves = self.Valves()
        self.citation = False  # Disable citation to remove citations from output
        self.last_emit_time = 0

    async def emit_status(
        self,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]],
        level: str,
        message: str,
        done: bool,
    ):
        """
        Emits status updates if an event emitter is provided and status indicators are enabled.
        """
        current_time = time.time()
        if (
            __event_emitter__
            and self.valves.enable_status_indicator
            and (
                current_time - self.last_emit_time >= self.valves.emit_interval or done
            )
        ):
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "status": "complete" if done else "in_progress",
                        "level": level,
                        "description": message,
                        "done": done,
                    },
                }
            )
            self.last_emit_time = current_time

    async def invoke_n8n_workflow(
        self,
        input_text: str,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
    ) -> dict:
        """
        Invokes the N8N workflow with the provided input text and returns a structured response.
        :param input_text: The input text to send to the N8N workflow.
        :param __user__: Optional user context (for compatibility with pipe).
        :param __event_emitter__: Optional event emitter for status updates.
        :return: A dictionary mimicking the pipe's output structure.
        """
        # Initialize response body similar to pipe
        body = {"messages": [{"role": "user", "content": input_text}]}

        # Emit initial status
        await self.emit_status(__event_emitter__, "info", "Executing N8N Workflow...", False)

        # Verify input is available
        if not input_text:
            await self.emit_status(
                __event_emitter__,
                "error",
                "No input text provided",
                True,
            )
            body["messages"].append(
                {"role": "assistant", "content": "No input text provided"}
            )
            return {"error": "No input text provided", "messages": body["messages"]}

        try:
            # Prepare request to N8N
            headers = {
                "Authorization": f"Bearer {self.valves.n8n_bearer_token}",
                "Content-Type": "application/json",
            }
            payload = {self.valves.input_field: input_text}

            # Add sessionId if available (mimicking pipe's chat_id)
            if __event_emitter__:
                chat_id, _ = self.extract_event_info(__event_emitter__)
                if chat_id:
                    payload["sessionId"] = chat_id

            # Invoke N8N workflow
            response = requests.post(self.valves.n8n_url, json=payload, headers=headers)

            if response.status_code == 200:
                n8n_response = response.json()[self.valves.response_field]
                # Append assistant response to messages, like the pipe
                body["messages"].append({"role": "assistant", "content": n8n_response})
            else:
                raise Exception(f"Error: {response.status_code} - {response.text}")

        except Exception as e:
            await self.emit_status(
                __event_emitter__,
                "error",
                f"Error during N8N workflow execution: {str(e)}",
                True,
            )
            body["messages"].append(
                {"role": "assistant", "content": f"Error: {str(e)}"}
            )
            return {"error": str(e), "messages": body["messages"]}

        # Emit completion status
        await self.emit_status(__event_emitter__, "info", "Workflow completed", True)

        # Return structured output like the pipe
        return {"response": n8n_response, "messages": body["messages"]}

    def extract_event_info(self, event_emitter) -> tuple[Optional[str], Optional[str]]:
        """
        Extracts chat_id and message_id from the event emitter, if available.
        """
        if not event_emitter or not event_emitter.__closure__:
            return None, None
        for cell in event_emitter.__closure__:
            if isinstance(request_info := cell.cell_contents, dict):
                chat_id = request_info.get("chat_id")
                message_id = request_info.get("message_id")
                return chat_id, message_id
        return None, None
