# ⚡ N8N Workflow Tool for OpenWebUI

![N8N](https://img.shields.io/badge/N8N-Workflow_Automation-FF6B6B?style=for-the-badge&logo=n8n)
![Python](https://img.shields.io/badge/Python-3.10+-yellow?style=for-the-badge&logo=python)

> **Connect your Agents to the world!** 🌍🔗

This tool allows your **OpenWebUI** users to trigger **N8N** workflows directly. It sends the user's input to a Webhook, waits for the execution, and returns the result back to the chat. Perfect for automations, integrations, and complex logic handling.

> *Based on the original work by [Cole Medin](https://github.com/ColeMedin).*

---

## 🚀 Features

- **🔄 Seamless Integration**: Calls N8N webhooks as if they were native functions.
- **📡 Real-time Status**: Shows "Executing N8N Workflow..." status in the chat UI.
- **🆔 Session Awareness**: Passes the `sessionId` (Chat ID) to N8N, allowing for persistent memory or context in your workflows.
- **🛠️ Flexible Configuration**: Customize the URL, tokens, and JSON field names to match your N8N setup.

---

## ⚙️ Configuration (Valves)

Configure the tool in **OpenWebUI > Workspace > Tools > Valves**:

| Valve | Description | Default |
| :--- | :--- | :--- |
| **n8n_url** | The URL of your N8N Webhook (POST). | `http://n8n-ui:5678/webhook/...` |
| **n8n_bearer_token** | Optional Bearer Token for authentication. | `""` |
| **input_field** | The JSON key to send the user input in. | `chatInput` |
| **response_field** | The JSON key to read the response from. | `output` |
| **emit_interval** | How often to update the status indicator (seconds). | `2.0` |

---

## 📦 Installation

1. Open **OpenWebUI**.
2. Go to **Workspace** > **Tools**.
3. Click **+ Create Tool**.
4. Copy the content of `n8n_executer_tool.py` and paste it into the editor.
5. Save and enable the tool in your agent!

---

## 💡 Usage in N8N

1. Create a **Webhook** node in N8N:
   - Method: `POST`
   - Path: `invoke-n8n-agent` (or whatever matches your URL)
   - Authentication: `Header Auth` (if using token) or `None`.
2. Connect your logic (AI Agent, HTTP Request, etc.).
3. End with a **Respond to Webhook** node:
   - Respond With: `JSON`
   - Response Body: `{ "output": "Your response here" }` (matches `response_field`).

---

## 📝 License

MIT License.

---

*Maintained by [matheusbuniotto](https://github.com/matheusbuniotto)*
