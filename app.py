"""
app.py - Main Flask application
AI-Based Voice-Driven Patient Record Management System
"""

import os
import json
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify, send_file
)
from flask_login import (
    LoginManager, login_user, logout_user, 
    login_required, current_user
)
from werkzeug.utils import secure_filename
from functools import wraps
import io

from database import db, Patient, Visit, Payment, User, init_db
from speech_to_text import transcribe_audio_file
from nlp_extraction import extract_medical_data
from pdf_export import generate_visit_pdf
from security import generate_visit_hash, verify_visit_hash
from ml.predict import predict_hospital

# ─── App Configuration ─────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = 'ai-healthcare-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///healthcare.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB max upload

# Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Role-based access decorator
def roles_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            if current_user.role not in roles:
                flash(f"🚫 Access Denied: {current_user.role} role does not have permission.", "danger")
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg', 'webm', 'flac', 'm4a'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize DB
init_db(app)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ─── Authentication ─────────────────────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash(f"👋 Welcome back, {user.username} ({user.role})!", "success")
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash("❌ Invalid username or password.", "danger")
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'Nurse')
        
        if User.query.filter_by(username=username).first():
            flash("⚠️ Username already exists.", "warning")
        else:
            new_user = User(username=username, role=role)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash("✅ Account created! Please log in.", "success")
            return redirect(url_for('login'))
            
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("🔒 Logged out successfully.", "info")
    return redirect(url_for('login'))

# ─── Home / Nurse Intake ───────────────────────────────────────────────────────

@app.route('/')
@login_required
def index():
    """Nurse intake page - record conversation."""
    return render_template('index.html')


@app.route('/api/extract', methods=['POST'])
@login_required
def api_extract():
    """API endpoint: extract medical data from provided text."""
    data = request.json
    text = data.get('text', '')
    if not text:
        return jsonify({'success': False, 'error': 'No text provided'}), 400
    
    extracted = extract_medical_data(text)
    return jsonify({
        'success': True,
        'extracted': extracted
    })


@app.route('/record', methods=['POST'])
@login_required
@roles_required('Nurse')
def record():
    """
    Handle audio upload OR manual text input.
    If text is provided, we skip backend transcription to avoid format errors.
    """
    transcript = request.form.get('manual_transcript', '').strip()
    extracted = {}

    # If no transcript was provided via hidden field/form, try to transcribe the file
    if not transcript and 'audio_file' in request.files:
        audio = request.files['audio_file']
        if audio and audio.filename and allowed_file(audio.filename):
            filename = secure_filename(audio.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            audio.save(filepath)
            
            # This is where the PCM error used to happen. 
            # With browser transcription, we usually already have the text.
            result = transcribe_audio_file(filepath)
            if result['success']:
                transcript = result['transcript']
            else:
                # Fallback: if transcription failed but was expected
                flash(f"⚠️ Speech extraction failed: {result['error']}", 'warning')

    # Extract medical data from transcript (if any)
    if transcript:
        extracted = extract_medical_data(transcript)
    else:
        extracted = {
            'name': None, 'age': None, 'phone': None,
            'symptoms': [], 'duration': None, 'medical_history': []
        }

    # Override with manual form fields if provided
    name_override = request.form.get('patient_name', '').strip()
    age_override = request.form.get('patient_age', '').strip()
    phone_override = request.form.get('patient_phone', '').strip()

    if name_override: extracted['name'] = name_override
    if age_override:
        try: extracted['age'] = int(age_override)
        except ValueError: pass
    if phone_override: extracted['phone'] = phone_override

    # Store draft in session
    session['draft'] = {
        'transcript': transcript,
        'name': extracted.get('name') or 'Unknown Patient',
        'age': extracted.get('age'),
        'phone': extracted.get('phone'),
        'symptoms': ', '.join(extracted.get('symptoms', [])) if isinstance(extracted.get('symptoms'), list) else extracted.get('symptoms', ''),
        'duration': extracted.get('duration') or '',
        'medical_history': ', '.join(extracted.get('medical_history', [])) if isinstance(extracted.get('medical_history'), list) else extracted.get('medical_history', ''),
    }

    flash('✅ Patient data extracted successfully. Please proceed to billing.', 'success')
    return redirect(url_for('billing'))


# ─── Billing Module ────────────────────────────────────────────────────────────

@app.route('/billing', methods=['GET', 'POST'])
@login_required
@roles_required('Nurse')
def billing():
    """
    Billing module:
    - Shows draft patient info
    - Allows nurse to confirm payment status
    - Saves Patient + Visit + Payment records
    - Redirects to doctor dashboard if Paid, else blocks
    """
    draft = session.get('draft', {})
    if not draft:
        flash('⚠️ No patient draft found. Please start a new recording.', 'warning')
        return redirect(url_for('index'))

    # ── Pre-lookup for existing history ─────────────────────────────
    existing_patient = None
    previous_visits = []
    patient_name = draft.get('name', 'Unknown Patient')
    patient_phone = draft.get('phone')

    if patient_phone:
        existing_patient = Patient.query.filter_by(name=patient_name, phone=patient_phone).first()
    if not existing_patient:
        existing_patient = Patient.query.filter_by(name=patient_name).first()

    if existing_patient:
        previous_visits = Visit.query.filter_by(patient_id=existing_patient.patient_id).order_by(Visit.date.desc()).all()

    if request.method == 'POST':
        payment_status = request.form.get('payment_status', 'Not Paid')
        amount = request.form.get('amount', '500')
        notes = request.form.get('notes', '').strip()

        try:
            amount = float(amount)
        except ValueError:
            amount = 500.0

        # ── Find or create Patient ─────────────────────────────────────────
        # Note: We already looked up existing_patient above, so we can reuse it
        if existing_patient:
            patient = existing_patient
            # Update age if we have new info
            if draft.get('age') and not patient.age:
                patient.age = draft.get('age')
            db.session.commit()
        else:
            patient = Patient(
                name=patient_name,
                phone=patient_phone or None,
                age=draft.get('age'),
                dob=None
            )
            db.session.add(patient)
            db.session.flush()  # Get patient_id

        # ── Create Visit ───────────────────────────────────────────────────
        visit_date = datetime.utcnow()
        visit_data_for_hash = {
            'patient_id': patient.patient_id,
            'date': visit_date,
            'symptoms': draft.get('symptoms', ''),
            'duration': draft.get('duration', ''),
            'medical_history': draft.get('medical_history', ''),
            'transcript': draft.get('transcript', ''),
            'notes': notes,
        }
        visit_hash = generate_visit_hash(visit_data_for_hash)

        visit = Visit(
            patient_id=patient.patient_id,
            date=visit_date,
            symptoms=draft.get('symptoms', ''),
            duration=draft.get('duration', ''),
            medical_history=draft.get('medical_history', ''),
            transcript=draft.get('transcript', ''),
            notes=notes,
            visit_hash=visit_hash
        )
        db.session.add(visit)
        db.session.flush()  # Get visit_id

        # ── Create Payment ─────────────────────────────────────────────────
        payment = Payment(
            patient_id=patient.patient_id,
            visit_id=visit.visit_id,
            status=payment_status,
            amount=amount,
            date=datetime.utcnow()
        )
        db.session.add(payment)
        db.session.commit()

        # Clear draft
        session.pop('draft', None)

        if payment_status == 'Paid':
            flash(f'✅ Payment confirmed for {patient.name}. Visit record secured.', 'success')
            
            # If the user is a Doctor, they can go straight to the dashboard
            if current_user.role == 'Doctor':
                return redirect(url_for('doctor_dashboard', patient_id=patient.patient_id))
            
            # If the user is a Nurse, they should stay in the intake/billing zone
            # Redirect to intake so they can handle the next patient
            flash('👨‍⚕️ Patient is ready for the Doctor. Hand over the records.', 'info')
            return redirect(url_for('index'))
        else:
            flash('🚫 Registration fee pending. Doctor access is blocked.', 'danger')
            return redirect(url_for('payment_pending', patient_id=patient.patient_id))

    return render_template('billing.html', draft=draft, previous_visits=previous_visits, existing_patient=existing_patient)


@app.route('/payment-pending/<int:patient_id>')
def payment_pending(patient_id):
    """Show payment pending alert page."""
    patient = Patient.query.get_or_404(patient_id)
    latest_visit = Visit.query.filter_by(patient_id=patient_id).order_by(Visit.date.desc()).first()
    payment = None
    if latest_visit:
        payment = Payment.query.filter_by(visit_id=latest_visit.visit_id).first()
    return render_template('payment_pending.html', patient=patient, payment=payment, visit=latest_visit)


@app.route('/update-payment/<int:payment_id>', methods=['POST'])
def update_payment(payment_id):
    """Update payment status to Paid."""
    payment = Payment.query.get_or_404(payment_id)
    payment.status = 'Paid'
    payment.date = datetime.utcnow()
    db.session.commit()
    flash('✅ Payment updated successfully!', 'success')
    return redirect(url_for('doctor_dashboard', patient_id=payment.patient_id))


# ─── Doctor Dashboard ──────────────────────────────────────────────────────────

@app.route('/doctor/dashboard/<int:patient_id>')
@login_required
@roles_required('Doctor')
def doctor_dashboard(patient_id):
    """
    Doctor dashboard for a specific patient.
    Shows current visit + all previous visits with hash integrity check.
    Only accessible if latest payment is Paid.
    """
    patient = Patient.query.get_or_404(patient_id)

    # Get latest visit
    latest_visit = Visit.query.filter_by(patient_id=patient_id).order_by(Visit.date.desc()).first()
    if not latest_visit:
        flash('⚠️ No visit records found for this patient.', 'warning')
        return redirect(url_for('all_patients'))

    # Check payment status
    payment = Payment.query.filter_by(visit_id=latest_visit.visit_id).first()
    if not payment or payment.status != 'Paid':
        flash('🚫 Registration fee pending. Doctor access is blocked.', 'danger')
        return redirect(url_for('payment_pending', patient_id=patient_id))

    # Get all visits (consecutive visit tracking)
    all_visits = Visit.query.filter_by(patient_id=patient_id).order_by(Visit.date.desc()).all()

    # Hash integrity check for all visits
    visits_with_integrity = []
    for v in all_visits:
        is_intact = verify_visit_hash(v, v.visit_hash) if v.visit_hash else None
        v_payment = Payment.query.filter_by(visit_id=v.visit_id).first()
        visits_with_integrity.append({
            'visit': v,
            'is_intact': is_intact,
            'payment': v_payment
        })

    return render_template(
        'doctor_dashboard.html',
        patient=patient,
        latest_visit=latest_visit,
        payment=payment,
        visits_with_integrity=visits_with_integrity,
        visit_count=len(all_visits)
    )


@app.route('/doctor/visit/<int:visit_id>')
def visit_detail(visit_id):
    """Detailed view of a single visit."""
    visit = Visit.query.get_or_404(visit_id)
    patient = Patient.query.get_or_404(visit.patient_id)
    payment = Payment.query.filter_by(visit_id=visit_id).first()

    # Hash integrity
    is_intact = verify_visit_hash(visit, visit.visit_hash) if visit.visit_hash else None

    # Previous visits
    previous_visits = Visit.query.filter(
        Visit.patient_id == visit.patient_id,
        Visit.visit_id != visit_id
    ).order_by(Visit.date.desc()).all()

    return render_template(
        'visit_detail.html',
        visit=visit,
        patient=patient,
        payment=payment,
        is_intact=is_intact,
        previous_visits=previous_visits
    )


@app.route('/doctor/recommend-hospital/<int:visit_id>')
@login_required
@roles_required('Doctor')
def recommend_hospital(visit_id):
    """
    Generate an ML-based hospital recommendation for a visit.
    Uses severity, age, and a computed specialization index.
    """
    visit = Visit.query.get_or_404(visit_id)
    patient = Patient.query.get_or_404(visit.patient_id)
    
    # 1. Prepare Features
    # Since we don't have a 'severity' field yet, we'll estimate it 
    # based on symptoms count or clinical summary length as a proxy.
    severity = min(len((visit.symptoms or "").split(",")) * 2, 10)
    age = patient.age or 35 # Default to 35 if unknown
    
    # Estimate specialization (0: General, 1: Cardio, 2: Neuro, 3: Ortho)
    spec_index = 0
    symp_lower = (visit.symptoms or "").lower()
    if any(k in symp_lower for k in ['heart', 'chest', 'palpitations']): spec_index = 1
    elif any(k in symp_lower for k in ['brain', 'nerve', 'seizure']): spec_index = 2
    elif any(k in symp_lower for k in ['bone', 'joint', 'fracture']): spec_index = 3
    
    features = [severity, age, spec_index]
    
    # 2. Get Prediction
    result = predict_hospital(features)
    
    if result['success']:
        return jsonify(result)
    else:
        # Resolve user request: Return proper JSON error message instead of crashing
        return jsonify({
            'success': False, 
            'error': result['error'],
            'message': "Wait! The recommendation engine is warming up or model is missing."
        }), 500


@app.route('/doctor/update-notes/<int:visit_id>', methods=['POST'])
def update_notes(visit_id):
    """Update doctor notes for a visit."""
    visit = Visit.query.get_or_404(visit_id)
    notes = request.form.get('notes', '').strip()
    visit.notes = notes
    db.session.commit()
    flash('✅ Notes updated successfully.', 'success')
    return redirect(url_for('visit_detail', visit_id=visit_id))


# ─── All Patients List ─────────────────────────────────────────────────────────

@app.route('/patients')
def all_patients():
    """List all patients with their visit counts."""
    patients = Patient.query.order_by(Patient.created_at.desc()).all()
    patient_data = []
    for p in patients:
        visit_count = Visit.query.filter_by(patient_id=p.patient_id).count()
        latest_visit = Visit.query.filter_by(patient_id=p.patient_id).order_by(Visit.date.desc()).first()
        latest_payment = None
        if latest_visit:
            latest_payment = Payment.query.filter_by(visit_id=latest_visit.visit_id).first()
        patient_data.append({
            'patient': p,
            'visit_count': visit_count,
            'latest_visit': latest_visit,
            'latest_payment': latest_payment
        })
    return render_template('patients.html', patient_data=patient_data)


# ─── PDF Export ────────────────────────────────────────────────────────────────

@app.route('/export/pdf/<int:visit_id>')
@login_required
def export_pdf(visit_id):
    """Export visit summary as PDF."""
    visit = Visit.query.get_or_404(visit_id)
    patient = Patient.query.get_or_404(visit.patient_id)
    payment = Payment.query.filter_by(visit_id=visit_id).first()

    # Previous visits
    previous_visits = Visit.query.filter(
        Visit.patient_id == visit.patient_id,
        Visit.visit_id != visit_id
    ).order_by(Visit.date.desc()).all()

    pdf_bytes = generate_visit_pdf(
        patient=patient.to_dict(),
        visit=visit.to_dict(),
        payment=payment.to_dict() if payment else {},
        previous_visits=[v.to_dict() for v in previous_visits]
    )

    filename = f"visit_{visit_id}_patient_{patient.patient_id}.pdf"
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )


# ─── API Endpoints ─────────────────────────────────────────────────────────────

@app.route('/api/transcribe', methods=['POST'])
def api_transcribe():
    """API endpoint: transcribe uploaded audio and return extracted data."""
    if 'audio' not in request.files:
        return jsonify({'success': False, 'error': 'No audio file provided'}), 400

    audio = request.files['audio']
    if not audio or not allowed_file(audio.filename):
        return jsonify({'success': False, 'error': 'Invalid file format'}), 400

    filename = secure_filename(audio.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    audio.save(filepath)

    result = transcribe_audio_file(filepath)
    if result['success']:
        extracted = extract_medical_data(result['transcript'])
        return jsonify({
            'success': True,
            'transcript': result['transcript'],
            'extracted': extracted
        })
    else:
        return jsonify({'success': False, 'error': result['error']}), 422


@app.route('/api/patients')
def api_patients():
    """API: list all patients."""
    patients = Patient.query.all()
    return jsonify([p.to_dict() for p in patients])


# ─── Run ───────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
