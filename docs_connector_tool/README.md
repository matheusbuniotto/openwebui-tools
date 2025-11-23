# Google Docs Templater

A powerful tool for OpenWebUI that allows you to generate Google Docs from templates using Google Apps Script.

## 🚀 Features

- **Template-based Generation**: Use any Google Doc as a template.
- **Dynamic Replacements**: Replace placeholders (e.g., `{client_name}`, `{date}`) with dynamic content from LLMs.
- **Instant Access**: Returns a direct link to the newly created document.

## 🛠️ Setup

### Part 1: Google Docs (The Template)

1.  **Create a Template**:
    *   Go to Google Docs and create a new document (or open an existing one).
    *   Add placeholders in your text using curly braces, e.g., `{company_name}`, `{invoice_amount}`, `{date}`.

2.  **Add the Script**:
    *   In your Google Doc, go to **Extensions** > **Apps Script**.
    *   Delete any code in the `Code.gs` file.
    *   Copy the content of `app_script.js` from this repository and paste it into the editor.
    *   (Optional) Rename the project to something like "OpenWebUI Connector".

3.  **Deploy as Web App**:
    *   Click the **Deploy** button (blue button top right) > **New deployment**.
    *   Click the **Select type** (gear icon) > **Web app**.
    *   **Description**: OpenWebUI Connector (or anything you like).
    *   **Execute as**: `Me` (your email).
    *   **Who has access**: `Anyone` (This is important so OpenWebUI can reach it without complex auth).
    *   Click **Deploy**.
    *   **Authorize Access**: You will need to authorize the script to access your Drive and Docs. Since it's your own script, you may see a "Google hasn't verified this app" warning. Click "Advanced" > "Go to ... (unsafe)" to proceed.
    *   **Copy the Web App URL**: You will get a URL ending in `/exec`. Copy this URL.

### Part 2: OpenWebUI (The Tool)

1.  **Install the Tool**:
    *   Copy the content of `docs_maker.py`.
    *   Go to your OpenWebUI instance > **Workspace** > **Tools**.
    *   Click **+** to add a new tool.
    *   Paste the code and save.

2.  **Configure the Valve**:
    *   In the Tool settings (or when you activate it for a model), look for the **Valves** section.
    *   Paste the **Web App URL** you copied from Google Apps Script into the `DOCS_WEBHOOK_URL` field.

## 💡 Usage

1.  Enable the tool for your model in OpenWebUI.
2.  Ask the model to create a document.
    *   *Example*: "Create a proposal document for Acme Corp based on the template. Set the client to 'Acme Corp' and the date to 'October 24th'."
3.  The model will detect the placeholders in your template (you might need to tell it what they are if it doesn't guess correctly, or just provide the JSON context) and generate the document.
4.  The tool will return a link to the new document.

## ⚠️ Notes

-   **Privacy**: The Google Apps Script deployment setting "Who has access: Anyone" means anyone with the URL can trigger the script. However, the script only creates files in *your* Drive.
-   **Sharing**: By default, the script creates private documents (accessible only to the owner). If you want to make them shareable via link automatically, uncomment the `setSharing` line in `app_script.js`.
