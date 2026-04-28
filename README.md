# AI-Based Voice-Driven Patient Record Management System

A complete Flask-based healthcare web application with AI speech recognition, NLP extraction, billing verification, and consecutive visit tracking.

---

## 🚀 Quick Start

### Step 1: Install Python Dependencies

```bash
cd ai-patient-record-system
pip install -r requirements.txt
```

### Step 2: Download spaCy English Model (Optional)
If you want spaCy NLP (the app uses rule-based extraction by default):
```bash
python -m spacy download en_core_web_sm
```

### Step 3: Run the Application

```bash
python app.py
```

Open your browser at: **http://localhost:5000**

---

## 📁 Project Structure

```
ai-patient-record-system/
├── app.py                    # Main Flask application (all routes)
├── database.py               # SQLite models: Patients, Visits, Payments
├── speech_to_text.py         # Speech recognition (Google Web Speech API)
├── nlp_extraction.py         # Rule-based NLP extraction
├── security.py               # SHA-256 hashing & integrity verification
├── pdf_export.py             # PDF report generation (ReportLab)
├── requirements.txt          # Python dependencies
├── static/
│   ├── css/style.css         # Dark-mode UI stylesheet
│   └── js/script.js          # Audio recording & UI interactions
├── templates/
│   ├── base.html             # Shared layout with navbar
│   ├── index.html            # Nurse intake (recording + manual input)
│   ├── billing.html          # Billing module (payment verification)
│   ├── payment_pending.html  # Payment pending alert page
│   ├── doctor_dashboard.html # Doctor dashboard with visit history
│   ├── visit_detail.html     # Single visit detail + integrity check
│   └── patients.html         # All patients list
└── uploads/                  # Temporary audio file storage (auto-created)
```

---

## 🔄 System Workflow

```
1. Nurse records conversation  →  2. AI transcribes speech
3. NLP extracts medical data   →  4. Draft stored in session
5. Billing module checks fee   →  6. If Paid: Doctor Dashboard
                                   If Not Paid: Access Blocked
7. Doctor views visit history  →  8. SHA-256 integrity verified
9. PDF export available
```

---

## 🗄️ Database Schema

| Table    | Columns |
|----------|---------|
| patients | patient_id, name, phone, dob, age, created_at |
| visits   | visit_id, patient_id, date, symptoms, duration, medical_history, transcript, notes, visit_hash |
| payments | payment_id, patient_id, visit_id, status, amount, date |

---

## 🌐 Application Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Nurse intake page |
| `/record` | POST | Process audio/text, extract data |
| `/billing` | GET/POST | Payment verification |
| `/payment-pending/<id>` | GET | Payment pending alert |
| `/update-payment/<id>` | POST | Mark payment as paid |
| `/doctor/dashboard/<id>` | GET | Doctor dashboard |
| `/doctor/visit/<id>` | GET | Visit detail |
| `/doctor/update-notes/<id>` | POST | Update doctor notes |
| `/patients` | GET | All patients list |
| `/export/pdf/<id>` | GET | Download PDF report |
| `/api/transcribe` | POST | API: transcribe audio |
| `/api/patients` | GET | API: list patients |

---

## 🔒 Security Features

- **SHA-256 hashing**: Every visit record is hashed on creation
- **Integrity verification**: Hash is recomputed and compared on every dashboard load
- **Payment gating**: Doctor access is blocked unless registration fee is paid
- **Tamper detection**: Dashboard shows ⚠️ warning if hash mismatch is detected

---

## 📋 Sample Transcript for Testing

Paste this in the "Conversation Transcript" box to test NLP extraction:

```
Patient name is John Doe, 45 years old. Phone number is 9876543210.
He reports fever for 3 days and severe headache. 
Patient has a history of diabetes and hypertension.
```

Expected extraction:
- **Name**: John Doe
- **Age**: 45
- **Phone**: 9876543210
- **Symptoms**: fever, headache
- **Duration**: 3 days
- **Medical History**: diabetes, hypertension

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| Flask | Web framework |
| Flask-SQLAlchemy | ORM for SQLite |
| SpeechRecognition | Audio transcription |
| reportlab | PDF generation |
| pyaudio | Microphone access (optional) |
| Werkzeug | File upload handling |

> **Note**: `pyaudio` requires PortAudio. On Windows, install via:
> `pip install pipwin && pipwin install pyaudio`
> 
> If pyaudio installation fails, the app still works fully — just use the browser's built-in recording or manual text input.
