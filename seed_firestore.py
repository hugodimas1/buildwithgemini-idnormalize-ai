"""Seed script for IDNormalize AI datatape & identity records in Firestore."""

from google.cloud import firestore

# Hardcoded project ID as string to prevent project number resolution issues
FIRESTORE_PROJECT = "qwiklabs-gcp-04-ee12fa990f7c"

def seed_data():
    db = firestore.Client(project=FIRESTORE_PROJECT)
    collection_name = "identity_records"
    
    sample_records = [
        {
            "record_id": "REC-1001",
            "full_name": "Alexander James Wright",
            "country_code": "US",
            "id_type": "SSN",
            "tape_id_number": "123-45-6789",
            "doc_id_number": "123-45-6789",
            "dob": "1985-04-12",
            "status": "VERIFIED",
            "fraud_risk_score": 0.05,
            "discrepancy_notes": "Identity document matches tape parameters and provider database.",
            "provider": "Equifax Identity Verification"
        },
        {
            "record_id": "REC-1002",
            "full_name": "Maria Elena Gomez",
            "country_code": "MX",
            "id_type": "CURP",
            "tape_id_number": "GOME880315MDFRRN01",
            "doc_id_number": "GOME880315MDFRRN09",
            "dob": "1988-03-15",
            "status": "FLAGGED_DISCREPANCY",
            "fraud_risk_score": 0.82,
            "discrepancy_notes": "Checksum character mismatch in CURP: tape ends in 01, provider doc ends in 09.",
            "provider": "RENAPO Verification API"
        },
        {
            "record_id": "REC-1003",
            "full_name": "David Kwesi Mensah",
            "country_code": "GH",
            "id_type": "GHANA_CARD",
            "tape_id_number": "GHA-712345678-9",
            "doc_id_number": "GHA-712345678-9",
            "dob": "1992-11-20",
            "status": "VERIFIED",
            "fraud_risk_score": 0.12,
            "discrepancy_notes": "Valid biometric token match and normalized national card syntax.",
            "provider": "NIA Verification System"
        },
        {
            "record_id": "REC-1004",
            "full_name": "Sophie Anne Tremblay",
            "country_code": "CA",
            "id_type": "SIN",
            "tape_id_number": "046-454-286",
            "doc_id_number": "046-454-287",
            "dob": "1990-07-08",
            "status": "HIGH_FRAUD_RISK",
            "fraud_risk_score": 0.94,
            "discrepancy_notes": "Failed Luhn checksum validation on tape SIN; provider document displays different serial number.",
            "provider": "TransUnion ID Vision"
        }
    ]

    print(f"Seeding {len(sample_records)} identity records into Firestore collection '{collection_name}' (Project: {FIRESTORE_PROJECT})...")
    for record in sample_records:
        doc_ref = db.collection(collection_name).document(record["record_id"])
        doc_ref.set(record)
        print(f"  ✓ Seeded {record['record_id']} - {record['full_name']} ({record['status']})")

    print("\nSeeding complete!")

if __name__ == "__main__":
    seed_data()
