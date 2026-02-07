# 🧪 OpenWebUI Tools Lab

A curated collection of high-utility, experimental tools for [OpenWebUI](https://github.com/open-webui/open-webui). These tools are built to bridge the gap between LLM reasoning and real-world execution, focusing on automation, knowledge retrieval, and creative workflows.

## 🛠️ Available Tools

### 🧠 [LLM Council](./llm_council_tool)
**Consensus-driven reasoning.** Orchestrates a deliberation process among multiple models (e.g., GPT-4, Gemini, Claude). It features a 3-stage pipeline: individual responses, anonymous peer-ranking, and chairperson synthesis to provide high-confidence answers.
- **Key Feature**: Peer evaluation eliminates single-model bias.

### 🎵 [Spotify Vibe Controller](./spotify_tool)
**Semantic music curation.** Translates the mood and context of your chat into a curated Spotify playlist. Tell it how you feel or what you're working on, and it will build a matching soundtrack using semantic analysis.
- **Key Feature**: Automatic playlist generation based on conversational context.

### ⚡ [N8N Workflow Executor](./n8n_tool)
**The universal connector.** Bridges OpenWebUI to the N8N automation ecosystem. Trigger complex workflows, interact with thousands of apps, and receive results directly in your chat interface.
- **Key Feature**: Session-aware executions that maintain context between your chat and N8N.

### 🌲 [Pinecone RAG](./pinecone_rag_tool)
**Long-term semantic memory.** Provides agents with access to persistent knowledge bases. It handles embedding generation and semantic search to ground responses in your own data.
- **Key Feature**: Seamless integration with Pinecone for production-grade retrieval.

### 📄 [Google Docs Templater](./docs_connector_tool)
**Last-mile productivity.** Automates document creation by filling Google Doc templates via Google Apps Script. Perfect for generating invoices, proposals, or reports directly from a chat.
- **Key Feature**: Dynamic placeholder replacement with LLM-generated content.

---

## 🔬 The Experimental DNA

My background is in Data Science and A/B testing, which drives a **test-everything, ship-fast** mentality. Each tool here is a specific exploration into "LLM Agency"—the ability for models to move beyond text and into action.

### The Builder Philosophy
1.  **Curiosity First**: Solve a personal friction point or explore an API limit.
2.  **Action & Shipping**: Move from "what if" to "it works" quickly.
3.  **Modular Design**: Tools are self-contained and easy to port into any OpenWebUI instance.

---

## 🚀 Getting Started

Each tool is designed for easy installation:

1.  **Pick a Tool**: Navigate to the specific tool's directory (e.g., `/llm_council_tool`).
2.  **Copy the Code**: Open the main Python file (usually `tool_name.py`) and copy the content.
3.  **Install in OpenWebUI**: 
    - Go to **Workspace** > **Tools** > **+ Create Tool**.
    - Paste the code and save.
4.  **Configure Valves**: Enter any required API keys (OpenAI, Spotify, etc.) in the tool's **Valves** configuration in the UI.

---

## 🤝 Contributing

These tools are built through chronic experimentation. If you find a bug or have an idea for a new "vibe", feel free to open an issue or a PR.

Built with ❤️ by [matheusbuniotto](https://github.com/matheusbuniotto)