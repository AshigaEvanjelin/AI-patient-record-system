"""
security.py - SHA-256 hashing for visit record integrity
"""

import hashlib
import json
from datetime import datetime


def generate_visit_hash(visit_data: dict) -> str:
    """
    Generate a SHA-256 hash for a visit record.
    Uses ISO formatted dates and normalized strings for consistency.
    """
    # Normalize date to string (ISO format is most consistent)
    raw_date = visit_data.get('date')
    if isinstance(raw_date, datetime):
        date_str = raw_date.strftime('%Y-%m-%d %H:%M:%S')
    else:
        date_str = str(raw_date or '')

    # Normalize fields to ensure consistency
    hash_payload = {
        'patient_id': int(visit_data.get('patient_id', 0)),
        'date': date_str,
        'symptoms': str(visit_data.get('symptoms') or '').strip(),
        'duration': str(visit_data.get('duration') or '').strip(),
        'medical_history': str(visit_data.get('medical_history') or '').strip(),
        'transcript': str(visit_data.get('transcript') or '').strip(),
        'notes': str(visit_data.get('notes') or '').strip(),
    }

    payload_str = json.dumps(hash_payload, sort_keys=True)
    return hashlib.sha256(payload_str.encode('utf-8')).hexdigest()


def verify_visit_hash(visit_obj, stored_hash: str) -> bool:
    """
    Verify a visit record's integrity by recomputing its hash.
    """
    if not stored_hash:
        return False
        
    current_data = {
        'patient_id': visit_obj.patient_id,
        'date': visit_obj.date,
        'symptoms': visit_obj.symptoms,
        'duration': visit_obj.duration,
        'medical_history': visit_obj.medical_history,
        'transcript': visit_obj.transcript,
        'notes': visit_obj.notes,
    }
    recomputed = generate_visit_hash(current_data)
    return recomputed == stored_hash
