# IDNormalize AI (National ID & Fraud Verification Concierge)

IDNormalize AI is a conversational risk and compliance agent built with the Google Agent Development Kit (ADK) and Gemini. It helps fraud analysts normalize National Identity Files and cross-validate loan datatape records against provider-issued identity documentation to detect fraud anomalies, syntax errors, and identity mismatches.

---

## 🚀 Key Capabilities & Implemented Features

Every feature listed below is fully implemented and wired into the agent:

- **🧠 Cross-Session Memory Bank**: Powered by Vertex AI Agent Engine Memory Bank (`PreloadMemoryTool` + `after_agent_callback`). The agent remembers flagged fraudulent IDs, suspicious borrower records (e.g., `REC-1001`), mismatched date-of-birth anomalies, and jurisdiction discrepancies across distinct conversations and sessions.
- **🗄️ Structured Datatape Portfolio (Firestore)**: Reads and writes portfolio identity audit records stored in Google Cloud Firestore (`list_identity_records`, `get_identity_record`, `save_identity_record`).
- **🔧 National ID Syntax & Checksum Validation**:
  - **Canada SIN**: Validates format and calculates mathematical **Luhn algorithm** checksums.
  - **US SSN**: Enforces SSA issuance structure rules and detects invalid area/group numbers.
  - **Mexico CURP**: Validates 18-character alphanumeric structure.
  - **Ghana Card**: Validates national PIN syntax.
- **🌐 Address & Postal Jurisdiction Geo-Verification**: Calls the live public Zippopotam API (`verify_address_jurisdiction`) to verify postal codes, city names, and state/province consistency against client identity files.
- **🎨 Visual Audit Badge Generation (Cloud Storage & Artifacts)**: Uses `gemini-3.1-flash-lite-image` to generate visual identity audit badges (`generate_identity_audit_badge`), saves them to ADK session artifacts, uploads the image bytes directly to a public Google Cloud Storage bucket, and returns public HTTPS image URLs.
- **🧪 Remote Agent Engine Code Sandbox**: Securely executes Python calculations, substring slicing, and custom algorithmic analysis in an isolated Vertex AI Agent Engine sandbox environment (`code_interpreter`).
- **🪟 Agent-First A2UI (v0.8)**: Generates structured A2UI cards (Card, Column, Row, Text, Image) via `A2uiSchemaManager` (version 0.8) and Basic Catalog, rendered directly in ADK Web with custom `a2ui_callback`.

---

## 🛠️ Architecture & Google Cloud Services

| Layer | Implementation / Service | Description |
|---|---|---|
| **Agent Core** | Google ADK + Gemini 3.6 Flash | Autonomous ReAct reasoning loop with tool calling |
| **Long-Term Memory** | Vertex AI Memory Bank (Agent Engine) | Persistent recall of fraud records and risk patterns across sessions |
| **Document Store** | Google Cloud Firestore | Datatape portfolio records and compliance audit logs |
| **Object Storage** | Google Cloud Storage | Public bucket hosting generated audit badge images |
| **Image Generation** | `gemini-3.1-flash-lite-image` | On-demand generation of compliance status visual badges |
| **Code Execution** | Vertex AI Agent Engine Sandbox | Remote sandboxed Python environment for algorithmic parsing |
| **Agent UI** | A2UI (v0.8) + `a2ui_utils.py` | Rich card-based rendering in ADK Web dev UI |

---

## 📋 Prerequisites

- Python 3.11 or later
- [uv](https://docs.astral.sh/uv/) package manager
- Google Cloud SDK (`gcloud`) authenticated with a project with Vertex AI and Firestore enabled

---

## 🏃 Local Setup & Running Instructions

1. **Navigate into the project directory**:
   ```bash
   cd idnormalize-ai
   ```

2. **Install project dependencies**:
   ```bash
   uv sync
   ```

3. **Configure environment variables**:
   Create a `.env` file based on `.env.example`:
   ```bash
   GOOGLE_CLOUD_PROJECT="<your-gcp-project-id>"
   GOOGLE_CLOUD_LOCATION="global"
   GOOGLE_GENAI_USE_VERTEXAI="true"
   ```

4. **Seed sample Firestore records (optional)**:
   ```bash
   uv run python seed_firestore.py
   ```

5. **Start the Agent Playground with Memory Service**:
   ```bash
   uv run adk web . --port 8080 --reload_agents --memory_service_uri=agentengine://<YOUR_AGENT_ENGINE_ID>
   ```

6. **Using the Dev UI**:
   - Open the web interface in your browser.
   - For optimal A2UI card rendering, turn **Token Streaming OFF** in the dev UI settings (gear icon) and start a new session.
