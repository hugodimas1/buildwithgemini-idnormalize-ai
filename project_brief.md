# My agent: IDNormalize AI (National ID & Fraud Verification Concierge)

One-liner: A conversational risk and compliance agent that helps fraud analysts normalize National Identity Files and cross-validate datatape records against provider-issued identity documentation to detect fraud anomalies.

Tool coverage:
- Memory: Remembers analyst history, audit sessions, jurisdiction-specific compliance preferences (e.g., country ID formats/schemes), and provider credential configurations.
- Tools:
  - `query_datatape_record(record_id: str)`: Looks up client records and submitted tape fields from database/storage.
  - `verify_identity_doc(record_id: str, id_type: str)`: Cross-references normalized doc parameters (e.g., name syntax, national ID checksum/hash, DOB) against identity provider APIs/databases.
  - `flag_fraud_discrepancy(record_id: str, issue_type: str, severity: str)`: Logs flagged mismatches and audit notes.
- Catalog/UI: Catalog of processed identity audit batches, record discrepancy comparison tables, and risk score cards (rendered via A2UI).
- Image gen: Generates visual audit summary charts or risk indicator badges/infographics for analyst review.
- Sandbox: Code sandbox for running national ID checksum validation algorithms, fuzzy string distance scoring (Levenshtein), and discrepancy statistics.

Recommended for every project: memory, storage, tools, image generation, A2UI
Agent-specific / stretch (pick what fits): Code sandbox for checksum/fuzzy-match algorithms, BigQuery/Firestore integration for datatape batches, Cloud Trace for auditability.
