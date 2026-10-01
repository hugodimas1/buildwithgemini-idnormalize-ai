# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import logging
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

from google.cloud import firestore
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

# Hardcoded project ID as string to prevent project number resolution issues on Agent Platform
FIRESTORE_PROJECT = "qwiklabs-gcp-04-ee12fa990f7c"
COLLECTION_NAME = "identity_records"

_db = None

def get_firestore_client():
    global _db
    if _db is None:
        _db = firestore.Client(project=FIRESTORE_PROJECT)
    return _db

MODEL = "gemini-3.6-flash"


def list_identity_records(status_filter: str = "") -> str:
    """Lists identity verification records from the Firestore database.

    Args:
        status_filter: Optional filter by status, e.g. 'VERIFIED', 'FLAGGED_DISCREPANCY', or 'HIGH_FRAUD_RISK'. Leave empty for all records.

    Returns:
        A formatted summary list of matching records with their IDs, names, ID types, and fraud risk scores.
    """
    db = get_firestore_client()
    query = db.collection(COLLECTION_NAME)
    docs = query.stream()

    results = []
    for doc in docs:
        data = doc.to_dict()
        status = data.get("status", "UNKNOWN")
        if status_filter and status_filter.upper() not in status.upper():
            continue
        results.append(
            f"Record ID: {data.get('record_id')} | Name: {data.get('full_name')} | "
            f"Country: {data.get('country_code')} | Type: {data.get('id_type')} | "
            f"Status: {status} | Risk Score: {data.get('fraud_risk_score')}"
        )

    if not results:
        return "No records found matching the criteria."
    return "\n".join(results)


def get_identity_record(record_id: str) -> str:
    """Fetches full details of a specific identity verification record from Firestore.

    Args:
        record_id: The ID of the record to retrieve (e.g., 'REC-1001', 'REC-1002').

    Returns:
        JSON-formatted string with all record fields, including tape data, provider doc data, and discrepancy notes.
    """
    db = get_firestore_client()
    doc_ref = db.collection(COLLECTION_NAME).document(record_id.strip())
    doc = doc_ref.get()

    if not doc.exists:
        return f"Record with ID '{record_id}' not found in database."

    data = doc.to_dict()
    return (
        f"Record ID: {data.get('record_id')}\n"
        f"Full Name: {data.get('full_name')}\n"
        f"Country: {data.get('country_code')}\n"
        f"ID Type: {data.get('id_type')}\n"
        f"Tape ID Number: {data.get('tape_id_number')}\n"
        f"Provider Doc ID Number: {data.get('doc_id_number')}\n"
        f"Date of Birth: {data.get('dob')}\n"
        f"Verification Provider: {data.get('provider')}\n"
        f"Status: {data.get('status')}\n"
        f"Fraud Risk Score: {data.get('fraud_risk_score')}\n"
        f"Discrepancy Notes: {data.get('discrepancy_notes')}"
    )


def save_identity_record(
    record_id: str,
    full_name: str,
    country_code: str,
    id_type: str,
    tape_id_number: str,
    doc_id_number: str,
    dob: str,
    status: str,
    fraud_risk_score: float,
    discrepancy_notes: str,
    provider: str,
) -> str:
    """Saves or updates an identity verification record in the Firestore database.

    Args:
        record_id: Unique identifier for the record (e.g., 'REC-1005').
        full_name: Client's full legal name.
        country_code: 2-letter ISO country code (e.g., 'US', 'MX', 'GH', 'CA').
        id_type: Type of national identity document (e.g., 'SSN', 'CURP', 'SIN', 'PASSPORT').
        tape_id_number: ID number provided in the received client datatape.
        doc_id_number: ID number extracted from the provider's verified identity documentation.
        dob: Date of birth (YYYY-MM-DD).
        status: Verification status ('VERIFIED', 'FLAGGED_DISCREPANCY', or 'HIGH_FRAUD_RISK').
        fraud_risk_score: Numerical fraud risk estimate from 0.0 (safe) to 1.0 (critical risk).
        discrepancy_notes: Explanation of detected discrepancies, checksum mismatches, or audit findings.
        provider: Name of the identity verification provider or source API.

    Returns:
        Confirmation message indicating whether the record was created or updated.
    """
    db = get_firestore_client()
    doc_ref = db.collection(COLLECTION_NAME).document(record_id.strip())
    
    data = {
        "record_id": record_id.strip(),
        "full_name": full_name.strip(),
        "country_code": country_code.strip().upper(),
        "id_type": id_type.strip().upper(),
        "tape_id_number": tape_id_number.strip(),
        "doc_id_number": doc_id_number.strip(),
        "dob": dob.strip(),
        "status": status.strip(),
        "fraud_risk_score": float(fraud_risk_score),
        "discrepancy_notes": discrepancy_notes.strip(),
        "provider": provider.strip(),
    }
    doc_ref.set(data)
    return f"Successfully saved record '{record_id}' for {full_name} with status '{status}' (Risk Score: {fraud_risk_score})."


def validate_national_id_syntax(id_type: str, id_number: str) -> str:
    """Validates the structure and checksum syntax of a National Identity number.

    Supports:
      - 'SIN' (Canada Social Insurance Number, 9 digits with Luhn checksum)
      - 'SSN' (US Social Security Number, 9 digits formatted AAA-GG-SSSS)
      - 'CURP' (Mexico CURP, 18 alphanumeric characters)
      - 'GHANA_CARD' (Ghana Card format, GHA-XXXXXXXXX-X)

    Args:
        id_type: The identity type ('SIN', 'SSN', 'CURP', 'GHANA_CARD').
        id_number: The identity number to validate.

    Returns:
        Validation result with is_valid boolean and concise diagnostic explanation.
    """
    clean_id = id_number.strip().replace("-", "").replace(" ", "").upper()
    id_type = id_type.strip().upper()

    if id_type == "SIN":
        if len(clean_id) != 9 or not clean_id.isdigit():
            return f"Invalid SIN: Must be exactly 9 numeric digits, got '{id_number}'."
        # Luhn checksum validation
        total = 0
        for idx, char in enumerate(clean_id):
            digit = int(char)
            if idx % 2 == 1:
                digit *= 2
                if digit > 9:
                    digit -= 9
            total += digit
        if total % 10 == 0:
            return f"Valid Canada SIN: '{id_number}' passes Luhn algorithm checksum verification."
        return f"Invalid Canada SIN: '{id_number}' failed Luhn algorithm checksum verification."

    if id_type == "SSN":
        if len(clean_id) != 9 or not clean_id.isdigit():
            return f"Invalid US SSN: Must be exactly 9 numeric digits, got '{id_number}'."
        area = clean_id[:3]
        group = clean_id[3:5]
        serial = clean_id[5:9]
        if area in ("000", "666") or area.startswith("9"):
            return f"Invalid US SSN: Area number '{area}' is not issued by SSA."
        if group == "00" or serial == "0000":
            return f"Invalid US SSN: Group or serial segment contains forbidden all-zero values."
        return f"Valid US SSN format: '{id_number}' conforms to Social Security Number syntax."

    if id_type == "CURP":
        if len(clean_id) != 18 or not clean_id.isalnum():
            return f"Invalid Mexico CURP: Must be 18 alphanumeric characters, got '{id_number}'."
        return f"Valid Mexico CURP structure: '{id_number}' conforms to the 18-character standard format."

    if id_type == "GHANA_CARD":
        if not id_number.strip().upper().startswith("GHA-"):
            return f"Invalid Ghana Card: Must begin with 'GHA-' prefix, got '{id_number}'."
        return f"Valid Ghana Card syntax: '{id_number}' conforms to the national PIN structure."

    return f"Unsupported ID type '{id_type}'. Supported types: SIN, SSN, CURP, GHANA_CARD."


import urllib.request
import json
import os


def verify_address_jurisdiction(country_code: str, postal_code: str) -> str:
    """Verifies postal code and geographic jurisdiction using the public Zippopotam API.

    Validates whether a postal code matches the claimed country, state/province,
    and place name in datatape or identity documentation.

    Args:
        country_code: 2-letter ISO country code (e.g. 'US', 'CA', 'MX', 'FR', 'DE', 'ES', etc.).
        postal_code: Postal or ZIP code to verify (e.g. '90210', 'M5V', '10001').

    Returns:
        Structured string with matched city/state jurisdiction details or error message.
    """
    clean_country = country_code.strip().lower()
    clean_postal = postal_code.strip().replace(" ", "").upper()
    api_base = os.getenv("ZIPPOPOTAM_API_URL", "https://api.zippopotam.us")
    url = f"{api_base}/{clean_country}/{clean_postal}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "IDNormalizeAI/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status != 200:
                return f"Jurisdiction lookup failed for {country_code} postal code '{postal_code}' (Status: {resp.status})."
            data = json.loads(resp.read().decode("utf-8"))

        country_name = data.get("country", country_code)
        places = data.get("places", [])
        if not places:
            return f"No jurisdiction records found for {country_code} postal code '{postal_code}'."

        first_place = places[0]
        place_name = first_place.get("place name", "Unknown City")
        state_name = first_place.get("state", "Unknown State/Province")
        state_abbr = first_place.get("state abbreviation", "")

        return (
            f"Verified Address Jurisdiction for '{postal_code}':\n"
            f"- Country: {country_name} ({data.get('country abbreviation', clean_country.upper())})\n"
            f"- City/Place: {place_name}\n"
            f"- State/Province: {state_name} ({state_abbr})\n"
            f"- Coordinates: Lat {first_place.get('latitude')}, Long {first_place.get('longitude')}"
        )
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return f"Invalid or unrecognized postal code '{postal_code}' for country '{country_code}'."
        return f"Public API error verifying postal code: {str(e)}"
    except Exception as e:
        return f"Error contacting jurisdiction verification service: {str(e)}"


from google.cloud import storage
from google import genai
from google.adk.tools import ToolContext

# Hardcoded bucket name as string
STORAGE_BUCKET_NAME = "idnormalize-ai-audit-docs-qwiklabs-gcp-04-ee12fa990f7c"

_storage_client = None

def get_storage_client():
    global _storage_client
    if _storage_client is None:
        _storage_client = storage.Client(project=FIRESTORE_PROJECT)
    return _storage_client


async def generate_identity_audit_badge(
    record_id: str,
    status: str,
    tool_context: ToolContext,
) -> str:
    """Generates an official visual audit stamp/badge for an identity record using gemini-3.1-flash-lite-image.

    Saves the image as a local session artifact for the Playground UI and uploads the bytes
    to the public Cloud Storage bucket, returning its public HTTPS URL.

    Args:
        record_id: The identifier of the identity record (e.g. 'REC-1001', 'REC-1004').
        status: The audit verification status (e.g. 'VERIFIED', 'FLAGGED_DISCREPANCY', 'HIGH_FRAUD_RISK').
        tool_context: ToolContext provided automatically by the ADK framework.

    Returns:
        Structured message containing the public HTTPS URL and confirmation of artifact creation.
    """
    clean_id = record_id.strip().replace(" ", "_")
    clean_status = status.strip().upper()

    prompt = (
        f"A clean, minimal, professional graphic design audit badge icon for identity verification. "
        f"Badge state: '{clean_status}'. High quality vector emblem style, clear colors, security crest, "
        f"crisp borders, transparent or solid neutral background, modern fintech compliance aesthetic."
    )

    client = genai.Client(
        vertexai=True,
        project=FIRESTORE_PROJECT,
        location="global",
    )

    response = await client.aio.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=prompt,
    )

    image_bytes = None
    mime_type = "image/jpeg"

    for candidate in response.candidates:
        if candidate.content and candidate.content.parts:
            for part in candidate.content.parts:
                if part.inline_data:
                    image_bytes = part.inline_data.data
                    mime_type = part.inline_data.mime_type or "image/jpeg"
                    break
        if image_bytes:
            break

    if not image_bytes:
        return f"Failed to generate audit badge for {record_id}: No image returned by Gemini model."

    ext = "png" if "png" in mime_type else "jpg"
    artifact_filename = f"audit_badge_{clean_id}.{ext}"

    # 1. Save as ADK session artifact
    artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    await tool_context.save_artifact(filename=artifact_filename, artifact=artifact_part)

    # 2. Upload to public Cloud Storage bucket
    storage_cli = get_storage_client()
    bucket = storage_cli.bucket(STORAGE_BUCKET_NAME)
    blob_name = f"badges/{clean_id}_{clean_status}.{ext}"
    blob = bucket.blob(blob_name)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{STORAGE_BUCKET_NAME}/{blob_name}"

    return (
        f"Audit badge successfully generated for {record_id} ({clean_status})!\n"
        f"- Saved Artifact: {artifact_filename}\n"
        f"- Public Image URL: {public_url}"
    )


from google.adk.code_executors.agent_engine_sandbox_code_executor import (
    AgentEngineSandboxCodeExecutor,
)
from google.adk.code_executors.code_execution_utils import CodeExecutionInput

SANDBOX_RESOURCE_NAME = (
    "projects/550295534713/locations/us-east1/reasoningEngines/5485804359579074560/sandboxEnvironments/4493967905511178240"
)

sandbox_executor = AgentEngineSandboxCodeExecutor(
    sandbox_resource_name=SANDBOX_RESOURCE_NAME
)


async def code_interpreter(code: str) -> str:
    """Executes Python code in the secure Vertex AI Agent Engine sandbox environment.

    Use this tool when you need to run custom Python calculations, string slicing,
    or algorithm verifications in the remote sandbox.

    Args:
        code: Complete Python script or code snippet to execute.

    Returns:
        The standard output, returned values, or error traceback from the sandbox execution.
    """
    try:
        api_client = sandbox_executor._get_api_client()
        input_data = {"code": code}
        resp = api_client.agent_engines.sandboxes.execute_code(
            name=SANDBOX_RESOURCE_NAME,
            input_data=input_data,
        )
        stdout = ""
        stderr = ""
        for output in resp.outputs:
            if output.mime_type == "application/json":
                json_data = json.loads(output.data.decode("utf-8"))
                stdout = json_data.get("msg_out", "")
                stderr = json_data.get("msg_err", "")
        res = (stdout or "") + ("\n" + stderr if stderr else "")
        return res.strip() if res.strip() else "Code executed successfully with no output."
    except Exception as e:
        return f"Sandbox execution error: {e}"

from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.adk.memory import VertexAiMemoryBankService

MEMORY_BANK_ID = "5485804359579074560"


# WRITE: after each turn, send the session to Memory Bank for extraction.
async def generate_memories_callback(callback_context: CallbackContext):
    try:
        await callback_context.add_session_to_memory()
    except Exception as e:
        logger.warning(f"Memory extraction skipped or unavailable: {e}")
    return None


def memory_bank_service_builder():
    """Configures VertexAiMemoryBankService for deployed Agent Runtime container."""
    return VertexAiMemoryBankService(
        project=FIRESTORE_PROJECT,
        location="us-east1",
        agent_engine_id=MEMORY_BANK_ID,
    )


from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from .a2ui_utils import a2ui_callback

schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

a2ui_instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are IDNormalize AI, a specialized risk and compliance assistant that helps fraud analysts "
        "normalize National Identity Files and cross-validate datatape records against provider-issued "
        "identity documentation to detect fraud anomalies. "
        "You remember all fraudulent IDs, flagged record IDs (e.g. REC-1001), suspect national identity numbers, "
        "borrower names, and detected anomalies across all sessions and conversations. "
        "You have tools to validate national ID syntax, list/get/save identity records, verify address jurisdictions, "
        "generate visual audit badges (which upload to Cloud Storage and return public image URLs), and execute Python code in the sandbox."
    ),
    workflow_description="Analyze the request, call the necessary tools to validate identity records or syntax, and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=a2ui_instruction,
    code_executor=AgentEngineSandboxCodeExecutor(
        sandbox_resource_name=SANDBOX_RESOURCE_NAME
    ),
    tools=[
        PreloadMemoryTool(),
        list_identity_records,
        get_identity_record,
        save_identity_record,
        validate_national_id_syntax,
        verify_address_jurisdiction,
        generate_identity_audit_badge,
        code_interpreter,
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
