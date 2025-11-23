# 🌲 Pinecone RAG Tool for OpenWebUI

![Pinecone](https://img.shields.io/badge/Pinecone-Vector_Database-green?style=for-the-badge&logo=pinecone)
![OpenAI](https://img.shields.io/badge/OpenAI-Embeddings-blue?style=for-the-badge&logo=openai)
![Python](https://img.shields.io/badge/Python-3.10+-yellow?style=for-the-badge&logo=python)

> **Supercharge your LLM with long-term memory!** 🧠✨

This tool seamlessly integrates **Pinecone** vector databases into **OpenWebUI**, allowing your agents to perform **RAG (Retrieval-Augmented Generation)** with ease. It automatically handles embedding generation (via OpenAI) and semantic search to retrieve the most relevant context for every query.

---

## 🚀 Features

- **🔍 Smart Retrieval**: Automatically converts user queries into vectors and finds the most relevant documents.
- **🤖 OpenAI Integration**: Uses OpenAI for high-quality, cost-effective embeddings.
- **🌐 Auto-Discovery**: Automatically detects your Pinecone index host—no need to hunt for URLs!
- **⚡ Real-time Feedback**: Provides visual status updates in the OpenWebUI chat (Connecting, Embedding, Searching...).
- **🛠️ Easy Configuration**: Just plug in your API keys and Index Name directly in the UI.

---

## ⚙️ Configuration (Valves)

Once installed, you can configure the tool directly in the OpenWebUI interface under **Valves**:

| Valve | Description | Example |
| :--- | :--- | :--- |
| **PINECONE_API_KEY** | Your secret API key from Pinecone console. | `pcsk_...` |
| **PINECONE_INDEX_NAME** | The name of the index you want to query. | `my-knowledge-base` |
| **OPENAI_API_KEY** | Your OpenAI API key for generating embeddings. | `sk-...` |
| **TOP_K** | Number of relevant chunks to retrieve. | `5` |

---

## 📦 Installation

1. Open **OpenWebUI**.
2. Go to **Workspace** > **Tools**.
3. Click **+ Create Tool**.
4. Copy the content of `pinecone_tool.py` and paste it into the editor.
5. Save and enable the tool in your agent!

---

## 💡 How it Works

1. **User asks a question.**
2. The tool **connects** to OpenAI to generate a vector embedding for the question.
3. It **searches** your Pinecone index for the nearest vectors (semantic match).
4. It **retrieves** the metadata text from the matched vectors.
5. It **returns** the context to the LLM to generate a grounded answer.

---

## 📝 License

MIT License. Feel free to use and modify!

---

*Created with ❤️ by [matheusbuniotto](https://github.com/matheusbuniotto)*
