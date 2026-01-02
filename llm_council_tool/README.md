# LLM Council Tool for OpenWebUI

![OpenWebUI](https://img.shields.io/badge/OpenWebUI-Tool-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-yellow?style=for-the-badge&logo=python)

> **Get consensus from multiple LLMs!**

This tool orchestrates a "council" of multiple LLMs to answer questions through a 3-stage deliberation process: individual responses, peer ranking, and chairperson synthesis.

> *Heavily inspired by [Andrej Karpathy's llm-council](https://github.com/karpathy/llm-council).*

---

## Features

- **Multi-Model Deliberation**: Query multiple models in parallel for diverse perspectives.
- **Peer Evaluation**: Models anonymously rank each other's responses.
- **Chairperson Synthesis**: A designated model synthesizes the final answer.
- **Auto-Configuration**: Automatically detects API key from session and base URL.

---

## Configuration (Valves)

Configure the tool in **OpenWebUI > Workspace > Tools > Valves**:

| Valve | Description | Default |
| :--- | :--- | :--- |
| **openwebui_base_url** | Base URL for OpenWebUI API. Leave empty to auto-detect. | `""` (auto) |
| **openwebui_api_key** | API Key. Leave empty to use session token or env var. | `""` (auto) |
| **fallback_api_key** | Fallback API key for OpenAI/OpenRouter when OpenWebUI unavailable. | `""` (uses `OPENAI_API_KEY` env) |
| **fallback_base_url** | Fallback API URL. Change to OpenRouter if needed. | `https://api.openai.com/v1` |
| **council_models** | Comma-separated model IDs or `all` for all available models. | `openai/gpt-4.1,openai/gpt-4o-mini,google/gemini-2.5-flash` |
| **chairperson_model** | Model ID for the chairperson. Empty uses first council model. | `""` |
| **max_models** | Maximum models when using `all`. Prevents runaway costs. | `5` |
| **timeout** | Timeout in seconds for model requests. | `60` |

---

## Installation

1. Open **OpenWebUI**.
2. Go to **Workspace** > **Tools**.
3. Click **+ Create Tool**.
4. Copy the content of `llm_council.py` and paste it into the editor.
5. Save and enable the tool in your agent!

---

## Usage

In your chat, the tool exposes the `consult_council` function:

```
Ask the council: What is the best programming language for beginners?
```

The tool will:
1. **Stage 1**: Query all council models with your question
2. **Stage 2**: Have each model rank the anonymized responses
3. **Stage 3**: Chairperson synthesizes a final answer

---

## Customizing Behavior

To modify prompts or council behavior, edit these sections in `llm_council.py`:

- **Ranking Prompt** (~line 348): Edit `ranking_prompt` to change how models evaluate each other.
- **Chairman Prompt** (~line 385): Edit `chairman_prompt` to change how the final synthesis is generated.
- **Report Format** (~line 404): Modify `report_parts` to customize the output structure.

---

## Authentication

The tool resolves API credentials in this order:
1. **Session token** from `__user__` (automatic inside OpenWebUI)
2. **Environment variable** `OPENWEBUI_API_KEY`
3. **Valve configuration** `openwebui_api_key`
4. **Fallback to OpenAI/OpenRouter** using `OPENAI_API_KEY` or `OPENROUTER_API_KEY` env vars

For most users inside OpenWebUI, **no configuration is needed**.

### Using with OpenRouter

Set `fallback_base_url` to `https://openrouter.ai/api/v1` and configure `fallback_api_key` or set `OPENROUTER_API_KEY` env var.

---

## License

MIT License.

---

*Maintained by [matheusbuniotto](https://github.com/matheusbuniotto)*
