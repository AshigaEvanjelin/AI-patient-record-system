"""
nlp_extraction.py - Rule-based NLP extraction for medical data
Extracts: Patient Name, Age, Symptoms, Duration, Medical History
from nurse-patient conversation transcripts.
"""

import re
import os
import json
import re
import os
import json
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# ─── Keyword Banks ────────────────────────────────────────────────────────────

SYMPTOM_KEYWORDS = [
    'fever', 'cough', 'cold', 'headache', 'nausea', 'vomiting', 'diarrhea',
    'fatigue', 'weakness', 'chest pain', 'shortness of breath', 'dizziness',
    'rash', 'swelling', 'pain', 'ache', 'sore throat', 'runny nose',
    'abdominal pain', 'back pain', 'joint pain', 'muscle pain', 'insomnia',
    'anxiety', 'depression', 'palpitations', 'breathlessness', 'wheezing',
    'constipation', 'bloating', 'indigestion', 'loss of appetite',
    'weight loss', 'weight gain', 'frequent urination', 'burning urination',
    'blurred vision', 'ear pain', 'toothache', 'skin irritation'
]

HISTORY_KEYWORDS = [
    'diabetes', 'hypertension', 'asthma', 'heart disease', 'cancer',
    'tuberculosis', 'tb', 'hiv', 'hepatitis', 'kidney disease', 'liver disease',
    'thyroid', 'arthritis', 'epilepsy', 'stroke', 'surgery', 'allergies',
    'allergy', 'allergic', 'high blood pressure', 'low blood pressure',
    'cholesterol', 'anemia', 'migraine', 'ulcer', 'gastritis', 'copd',
    'previous surgery', 'hospitalized', 'chronic', 'history of'
]

DURATION_PATTERNS = [
    r'\b(\d+)\s*(day|days|week|weeks|month|months|year|years|hour|hours)\b',
    r'\b(since\s+\w+)',
    r'\b(for\s+\d+\s+\w+)',
    r'\b(last\s+\d+\s+\w+)',
    r'\b(past\s+\d+\s+\w+)',
]


# ─── Extraction Functions ──────────────────────────────────────────────────────

def extract_name(text: str) -> Optional[str]:
    """Extract patient name from transcript."""
    patterns = [
        r"(?:patient(?:'s)?\s+name\s+is|my name is|i am|i'm|name[:\s]+)\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})",
        r"(?:patient|name)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})",
        r"^([A-Z][a-z]+\s+[A-Z][a-z]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) > 2:
                return name.title()
    return None


def extract_age(text: str) -> Optional[int]:
    """Extract patient age from transcript."""
    patterns = [
        r'\b(?:age[d]?\s+(?:is\s+)?|i(?:\'m|\s+am)\s+|(\d+)\s*years?\s+old)\b(\d{1,3})',
        r'\b(\d{1,3})\s*(?:years?\s+old|yr\s+old|y\.?o\.?)\b',
        r'\bage\s*[:\-]?\s*(\d{1,3})\b',
        r'\b(\d{1,3})\s*years?\s+of\s+age\b',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = [g for g in match.groups() if g and g.isdigit()]
            if groups:
                age = int(groups[-1])
                if 0 < age < 130:
                    return age
    return None


def extract_symptoms(text: str) -> list:
    """Extract symptoms mentioned in transcript."""
    found = []
    text_lower = text.lower()
    for symptom in SYMPTOM_KEYWORDS:
        if symptom in text_lower:
            found.append(symptom)
    return list(set(found))


def extract_duration(text: str) -> Optional[str]:
    """Extract duration of symptoms from transcript."""
    for pattern in DURATION_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return None


def extract_medical_history(text: str) -> list:
    """Extract medical history keywords from transcript."""
    found = []
    text_lower = text.lower()
    for keyword in HISTORY_KEYWORDS:
        if keyword in text_lower:
            found.append(keyword)
    return list(set(found))


def extract_phone(text: str) -> Optional[str]:
    """Extract phone number from transcript."""
    pattern = r'\b(\+?\d[\d\s\-]{8,14}\d)\b'
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip()
    return None


def extract_medical_data(transcript: str) -> dict:
    """
    Main extraction function using rule-based NLP.
    """
    if not transcript:
        return {
            'name': None, 'age': None, 'phone': None,
            'symptoms': [], 'duration': None, 'medical_history': []
        }

    return {
        'name': extract_name(transcript),
        'age': extract_age(transcript),
        'phone': extract_phone(transcript),
        'symptoms': extract_symptoms(transcript),
        'duration': extract_duration(transcript),
        'medical_history': extract_medical_history(transcript)
    }
