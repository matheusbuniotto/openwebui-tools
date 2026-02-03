"""
title: LLM Council Tool
author: matheusbuniotto
funding_url: https://github.com/matheusbuniotto/openwebui-tools
version: 0.3.0
license: MIT
"""

import os
import asyncio
import re
from typing import List, Dict, Any, Tuple, Optional, Union
from pydantic import BaseModel, Field
import requests


DEFAULT_COUNCIL_MODELS = "openai/gpt-4.1,openai/gpt-4o-mini,google/gemini-2.5-flash"


class Tools:
    class Valves(BaseModel):
        openwebui_base_url: str = Field(
            default="",
            description="Base URL for OpenWebUI API. Leave empty to auto-detect (tries localhost:3000, then host.docker.internal:3000).",
        )
        openwebui_api_key: str = Field(
            default="",
            description="API Key for OpenWebUI. Leave empty to auto-detect from session or OPENWEBUI_API_KEY env var.",
        )
        fallback_api_key: str = Field(
            default="",
            description="Fallback API key for OpenAI/OpenRouter when OpenWebUI is unavailable. Uses OPENAI_API_KEY env var if empty.",
        )
        fallback_base_url: str = Field(
            default="https://api.openai.com/v1",
            description="Fallback API base URL. Use 'https://openrouter.ai/api/v1' for OpenRouter.",
        )
        council_models: str = Field(
            default=DEFAULT_COUNCIL_MODELS,
            description="Comma-separated model IDs (e.g., 'llama3:latest,gpt-4o') or 'all' to use all available models (limited by max_models).",
        )
        chairperson_model: str = Field(
            default="",
            description="Model ID for the Chairperson who synthesizes the final answer. If empty, uses the first council model.",
        )
        max_models: int = Field(
            default=5,
            description="Maximum number of models when using 'all'. Prevents runaway costs.",
        )
        timeout: int = Field(
            default=60, description="Timeout in seconds for model requests."
        )

    def __init__(self):
        self.valves = self.Valves()
        self._resolved_api_key: Optional[str] = None
        self._resolved_base_url: Optional[str] = None
        self._using_fallback: bool = False

    def _resolve_api_key(self, __user__: Optional[dict] = None) -> Optional[str]:
        """
        Resolves API key in order of priority:
        1. __user__ dict token (passed by OpenWebUI)
        2. OPENWEBUI_API_KEY environment variable
        3. Valve configuration
        """
        if __user__:
            token = __user__.get("token") or __user__.get("api_key")
            if token:
                return token

        env_key = os.environ.get("OPENWEBUI_API_KEY")
        if env_key:
            return env_key

        if self.valves.openwebui_api_key:
            return self.valves.openwebui_api_key

        return None

    def _resolve_fallback_api_key(self) -> Optional[str]:
        """
        Resolves fallback API key for OpenAI/OpenRouter.
        """
        if self.valves.fallback_api_key:
            return self.valves.fallback_api_key

        # Try common environment variables
        for env_var in ["OPENAI_API_KEY", "OPENROUTER_API_KEY"]:
            key = os.environ.get(env_var)
            if key:
                return key

        return None

    def _resolve_base_url(self) -> str:
        """
        Resolves base URL in order of priority:
        1. Valve configuration (if set)
        2. OPENWEBUI_BASE_URL environment variable
        3. Auto-detect (localhost first, then Docker internal)
        """
        if self.valves.openwebui_base_url:
            return self.valves.openwebui_base_url

        env_url = os.environ.get("OPENWEBUI_BASE_URL")
        if env_url:
            return env_url

        localhost_url = "http://localhost:3000/api"
        docker_url = "http://host.docker.internal:3000/api"

        try:
            response = requests.get(f"{localhost_url}/models", timeout=2)
            if response.status_code in [200, 401, 403]:
                return localhost_url
        except Exception:
            pass

        return docker_url

    def _try_fallback(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Attempts to use fallback API (OpenAI/OpenRouter).
        Returns (api_key, base_url) or (None, None) if unavailable.
        """
        fallback_key = self._resolve_fallback_api_key()
        if fallback_key:
            return fallback_key, self.valves.fallback_base_url
        return None, None

    async def _emit_status(
        self,
        event_emitter: Any,
        level: str,
        message: str,
        done: bool,
    ):
        """
        Emits status updates to the OpenWebUI interface.
        """
        if event_emitter:
            await event_emitter(
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

    def _query_model_sync(
        self, model: str, messages: List[Dict[str, Any]], api_key: str, base_url: str
    ) -> Optional[Dict[str, Any]]:
        """
        Synchronous helper to query a single model via OpenWebUI API.
        """
        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
        }

        try:
            response = requests.post(
                url, headers=headers, json=payload, timeout=self.valves.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]
        except Exception as e:
            print(f"Error querying model {model}: {e}")
            return {"error": str(e)}

    async def _query_model_async(
        self, model: str, messages: List[Dict[str, Any]], api_key: str, base_url: str
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Async wrapper for querying a model.
        """
        loop = asyncio.get_running_loop()
        # Run synchronous request in a separate thread to avoid blocking the event loop
        result = await loop.run_in_executor(
            None, self._query_model_sync, model, messages, api_key, base_url
        )
        return model, result

    def _normalize_topic_to_content(
        self, topic: Union[str, List[Dict[str, Any]]]
    ) -> Union[str, List[Dict[str, Any]]]:
        """
        Normalize topic (string or OpenWebUI multimodal content) for API message content.
        Returns content as-is for API: str or list of parts (text + image_url).
        """
        if isinstance(topic, str):
            return topic
        if isinstance(topic, list):
            return topic if topic else ""
        # Fallback: coerce to string (e.g. unexpected type)
        return str(topic) if topic is not None else ""

    def _topic_to_text(self, topic: Union[str, List[Dict[str, Any]]]) -> str:
        """
        Extract a plain-text representation of topic for use in prompts (ranking, chairman).
        Handles string input and multimodal content (text + image parts).
        """
        if topic is None:
            return ""
        if isinstance(topic, str):
            return topic
        if not isinstance(topic, list):
            return str(topic)
        parts = []
        for item in topic:
            if not isinstance(item, dict):
                continue
            kind = item.get("type")
            if kind == "text":
                parts.append(item.get("text", ""))
            elif kind == "image_url":
                parts.append("[Image attached]")
        return " ".join(parts).strip() or "[No text content]"

    def _parse_ranking_from_text(self, ranking_text: str) -> List[str]:
        """
        Extracts the ranking list from the model's text response.
        Looks for 'FINAL RANKING:' followed by '1. Response X'.
        """
        if "FINAL RANKING:" in ranking_text:
            parts = ranking_text.split("FINAL RANKING:")
            if len(parts) >= 2:
                ranking_section = parts[1]
                # Match "1. Response A" or "1. Response A"
                numbered_matches = re.findall(
                    r"\d+\.\s*Response [A-Z]", ranking_section
                )
                if numbered_matches:
                    return [
                        re.search(r"Response [A-Z]", m).group()
                        for m in numbered_matches
                    ]

                # Fallback: just find Response X in order
                matches = re.findall(r"Response [A-Z]", ranking_section)
                return matches

        # Global fallback
        matches = re.findall(r"Response [A-Z]", ranking_text)
        return matches

    def _get_available_models(self, api_key: str, base_url: str) -> List[str]:
        """
        Fetches the list of available model IDs from the OpenWebUI API.
        """
        url = f"{base_url}/models"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.get(url, headers=headers, timeout=self.valves.timeout)
            response.raise_for_status()
            data = response.json()
            # OpenWebUI /api/models format: {"data": [{"id": "model_id", ...}, ...]}
            return [model["id"] for model in data.get("data", [])]
        except Exception as e:
            print(f"Error fetching available models: {e}")
            return []

    async def consult_council(
        self,
        topic: Union[str, List[Dict[str, Any]]],
        __user__: Optional[dict] = None,
        __event_emitter__: Any = None,
    ) -> str:
        """
        Orchestrates a 3-stage council meeting:
        1. Council provides individual responses.
        2. Council ranks peer responses.
        3. Chairperson synthesizes the final answer.

        topic: User input as plain text (str) or OpenWebUI multimodal content (list of
               parts with "type": "text" and/or "type": "image_url"). Supports images.
        """
        # Normalize topic for API (preserve images) and for text-only prompts
        user_content = self._normalize_topic_to_content(topic)
        topic_text = self._topic_to_text(topic)

        # Resolve API key and base URL (try OpenWebUI first, then fallback)
        api_key = self._resolve_api_key(__user__)
        base_url = self._resolve_base_url()
        self._using_fallback = False

        if not api_key:
            # Try fallback to OpenAI/OpenRouter
            fallback_key, fallback_url = self._try_fallback()
            if fallback_key:
                api_key = fallback_key
                base_url = fallback_url
                self._using_fallback = True
                await self._emit_status(
                    __event_emitter__,
                    "info",
                    f"Using fallback API: {fallback_url}",
                    False,
                )
            else:
                await self._emit_status(
                    __event_emitter__,
                    "error",
                    "No API Key found. Set OPENWEBUI_API_KEY or OPENAI_API_KEY env var.",
                    True,
                )
                return "Error: No API Key found. Please set OPENWEBUI_API_KEY, OPENAI_API_KEY, or configure in Valves."

        # 1. Fetch available models
        available_models = await asyncio.get_running_loop().run_in_executor(
            None, self._get_available_models, api_key, base_url
        )

        # 2. Determine target models
        configured_models_raw = self.valves.council_models.lower().strip()

        target_models = []
        if configured_models_raw == "all":
            if available_models:
                target_models = available_models[: self.valves.max_models]
                if len(available_models) > self.valves.max_models:
                    await self._emit_status(
                        __event_emitter__,
                        "info",
                        f"Limiting council to {self.valves.max_models} models (of {len(available_models)} available).",
                        False,
                    )
            else:
                return "Error: 'council_models' set to 'all', but could not fetch available models from API."
        else:
            requested_models = [
                m.strip() for m in self.valves.council_models.split(",") if m.strip()
            ]

            if available_models:
                # Validation logic
                missing_models = []
                for m in requested_models:
                    if m in available_models:
                        target_models.append(m)
                    else:
                        missing_models.append(m)

                if missing_models:
                    warning_msg = f"Warning: The following models were not found and will be skipped: {', '.join(missing_models)}"
                    await self._emit_status(
                        __event_emitter__, "info", warning_msg, False
                    )

                if not target_models:
                    return f"Error: None of the requested models ({', '.join(requested_models)}) are available."
            else:
                # Could not fetch available models (API error?), so we trust the user's list
                await self._emit_status(
                    __event_emitter__,
                    "info",
                    "Could not verify models with API, proceeding with configured list.",
                    False,
                )
                target_models = requested_models

        council_models_list = target_models

        if not council_models_list:
            return "Error: No council models configured or found."

        # check for chairperson
        chairperson = self.valves.chairperson_model
        if not chairperson:
            chairperson = council_models_list[0]

        # Validate chairperson if we have list
        if available_models and chairperson not in available_models:
            await self._emit_status(
                __event_emitter__,
                "info",
                f"Warning: Chairperson model '{chairperson}' not found in available models. Trying anyway...",
                False,
            )

        # --- Stage 1: Collect Responses ---
        await self._emit_status(
            __event_emitter__,
            "info",
            f"Stage 1: Consulting {len(council_models_list)} council members: {', '.join(council_models_list)}",
            False,
        )

        stage1_messages = [{"role": "user", "content": user_content}]
        tasks = [
            self._query_model_async(model, stage1_messages, api_key, base_url)
            for model in council_models_list
        ]

        # Run all requests in parallel
        stage1_results_raw = await asyncio.gather(*tasks)

        valid_responses = []
        errors = []
        for model, response in stage1_results_raw:
            if response and "error" not in response:
                content = response.get("content", "")
                if content:
                    valid_responses.append({"model": model, "response": content})
            elif response and "error" in response:
                errors.append(f"{model}: {response['error']}")

        if not valid_responses:
            error_details = "; ".join(errors) if errors else "Unknown error"
            error_msg = f"All council models failed. Errors: {error_details}"
            await self._emit_status(
                __event_emitter__, "error", f"Failed: {error_details[:100]}...", True
            )
            return f"Error: Please check your OpenWebUI Base URL and API Key. Details: {error_msg}"

        # --- Stage 2: Peer Ranking ---
        await self._emit_status(
            __event_emitter__,
            "info",
            "Stage 2: Council is reviewing peer responses...",
            False,
        )

        # Anonymize responses with labels A, B, C...
        labels = [chr(65 + i) for i in range(len(valid_responses))]

        # Prepare ranking prompt
        responses_text = "\n\n".join(
            [
                f"Response {label}:\n{r['response']}"
                for label, r in zip(labels, valid_responses)
            ]
        )

        ranking_prompt = f"""You are evaluating different responses to the following question:

Question: {topic_text}

Here are the responses from different models (anonymized):

{responses_text}

Your task:
1. Evaluate each response individually (strengths/weaknesses).
2. Provide a final ranking.

IMPORTANT: Your final ranking MUST be formatted EXACTLY as follows:
- Start with the line "FINAL RANKING:" (all caps, with colon)
- Then list the responses from best to worst as a numbered list
- Each line should be: number, period, space, then ONLY the response label (e.g., "1. Response A")

FINAL RANKING:
1. Response [Label]
2. Response [Label]
...
"""
        ranking_messages = [{"role": "user", "content": ranking_prompt}]

        # Ask council members to rank
        ranking_tasks = [
            self._query_model_async(model, ranking_messages, api_key, base_url)
            for model in council_models_list
        ]
        stage2_results_raw = await asyncio.gather(*ranking_tasks)

        rankings = []
        for model, response in stage2_results_raw:
            if response:
                content = response.get("content", "")
                parsed = self._parse_ranking_from_text(content)
                rankings.append(
                    {"model": model, "full_text": content, "parsed": parsed}
                )

        # --- Stage 3: Synthesis ---
        await self._emit_status(
            __event_emitter__,
            "info",
            "Stage 3: Chairperson is synthesizing the result...",
            False,
        )

        # Build context for Chairman
        stage1_summary = "\n\n".join(
            [f"Model: {r['model']}\nResponse: {r['response']}" for r in valid_responses]
        )

        stage2_summary = "\n\n".join(
            [
                f"Model: {r['model']}\nRanking: {r.get('parsed', 'No valid ranking found')}"
                for r in rankings
            ]
        )

        chairman_prompt = f"""You are the Chairperson of an LLM Council.
        
Original Question: {topic_text}

STAGE 1 - Individual Responses:
{stage1_summary}

STAGE 2 - Peer Rankings:
{stage2_summary}

Your task as Chairman is to synthesize a single, comprehensive answer.
Consider the insights from Stage 1 and the consensus (or disagreement) from Stage 2.
"""
        chairman_messages = [{"role": "user", "content": chairman_prompt}]

        _, final_response = await self._query_model_async(
            chairperson, chairman_messages, api_key, base_url
        )

        await self._emit_status(
            __event_emitter__, "info", "Council meeting adjourned.", True
        )

        # --- Construct Detailed Report ---

        report_parts = ["# 🏛️ LLM Council Report\n"]

        # Stage 1 Output
        report_parts.append("## Stage 1: Individual Perspectives")
        for r in valid_responses:
            report_parts.append(f"### {r['model']}\n{r['response']}\n")

        # Stage 2 Output
        report_parts.append("\n## Stage 2: Peer Evaluation & Ranking")
        for r in rankings:
            report_parts.append(f"### {r['model']}'s Ranking\n{r['full_text']}\n")

        # Stage 3 Output
        if final_response:
            # Use the final_response content obtained from the Chairperson
            final_synthesis = final_response.get("content", "Error: No content.")
            report_parts.append(
                f"\n## Stage 3: Chairperson Synthesis ({chairperson})\n{final_synthesis}"
            )
        else:
            final_synthesis = (
                "Error: Chairperson failed to synthesize the final response."
            )
            report_parts.append(
                f"\n## Stage 3: Chairperson Synthesis\n{final_synthesis}"
            )

        full_report = "\n".join(report_parts)

        # Emit the report directly to the chat to ensure raw visibility
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "message",
                    "data": {"content": full_report},
                }
            )

        # Return the report as well (for history/context) but the emitter ensures direct display.
        return full_report
