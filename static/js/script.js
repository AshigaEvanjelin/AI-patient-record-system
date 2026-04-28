/**
 * script.js - HealSync AI Medical Engine
 * Optimized for Browser-side Web Speech API + Premium glassmorphism UI.
 */

// ── State ────────────────────────────────────────────────────────────────────
let mediaRecorder = null;
let audioChunks = [];
let recordingTimer = null;
let recordingSeconds = 0;
let isRecording = false;

// Web Speech API
let recognition = null;
let finalTranscript = "";

// ── DOM Helpers ───────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);

// ── Initialize Speech Recognition ─────────────────────────────────────────────
function initRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        console.warn("Web Speech API not supported in this browser.");
        return null;
    }

    const rec = new SpeechRecognition();
    rec.continuous = true;
    rec.interimResults = true;
    rec.lang = 'en-US';

    rec.onresult = (event) => {
        let interimTranscript = "";
        for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
                finalTranscript += event.results[i][0].transcript + " ";
            } else {
                interimTranscript += event.results[i][0].transcript;
            }
        }

        const ta = $('transcriptArea');
        if (ta) {
            ta.value = finalTranscript + interimTranscript;
            ta.scrollTop = ta.scrollHeight;
        }
    };

    rec.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
        if (event.error === 'network') {
            showStatus('error', '❌ Network error during transcription. Check your internet connection.');
        }
    };

    return rec;
}

// ── Toggle Recording ──────────────────────────────────────────────────────────
async function toggleRecording() {
    if (isRecording) {
        stopRecording();
    } else {
        await startRecording();
    }
}

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

        // Reset state
        audioChunks = [];
        finalTranscript = "";
        const ta = $('transcriptArea');
        if (ta) ta.value = '';

        // 1. Start Audio Recorder (raw backup)
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.ondataavailable = e => {
            if (e.data && e.data.size > 0) audioChunks.push(e.data);
        };
        mediaRecorder.start();

        // 2. Start Browser Speech Recognition
        recognition = initRecognition();
        if (recognition) {
            recognition.start();
            showStatus('transcribing', '<i class="fas fa-satellite-dish"></i> HEALSYNC AI is listening...');
        } else {
            showStatus('warning', '⚠️ Transcription not supported in this browser.');
        }

        isRecording = true;
        setRecordingUI(true);

        // Timer
        recordingSeconds = 0;
        recordingTimer = setInterval(() => {
            recordingSeconds++;
            const mins = String(Math.floor(recordingSeconds / 60)).padStart(2, '0');
            const secs = String(recordingSeconds % 60).padStart(2, '0');
            $('recordNote').innerHTML = `<span class="tm-active">Session Time: ${mins}:${secs}</span>`;
        }, 1000);

    } catch (err) {
        handleMicError(err);
    }
}

async function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
    }

    if (recognition) {
        recognition.stop();
    }

    clearInterval(recordingTimer);
    isRecording = false;
    setRecordingUI(false);
    $('recordNote').textContent = 'Processing session...';

    setTimeout(async () => {
        const transcript = $('transcriptArea').value.trim();
        if (transcript) {
            $('manualTranscriptHidden').value = transcript;
            await extractFromText(transcript);
        } else {
            showStatus('error', '❌ No speech detected. Please speak clearly.');
            $('recordNote').textContent = 'Click to try again';
        }
    }, 500);
}

// ── Extraction Flow ───────────────────────────────────────────────────────────
async function extractFromText(text) {
    showStatus('transcribing', '<i class="fas fa-brain"></i> Analyzing clinical conversation...');

    try {
        const resp = await fetch('/api/extract', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        });

        const data = await resp.json();

        if (data.success) {
            fillExtractedFields(data.extracted);
            showStatus('success', '<i class="fas fa-check-circle"></i> Clinical details extracted successfully!');
            showExtractedPreview(data.extracted, text);
            $('recordNote').textContent = 'Intake complete. Verify details ->';
        } else {
            showStatus('error', '❌ AI Analysis failed.');
        }
    } catch (err) {
        showStatus('error', '❌ Connection lost during analysis.');
    }
}

function fillExtractedFields(extracted) {
    if (extracted.name) $('patientNameField').value = extracted.name;
    if (extracted.age) $('patientAgeField').value = extracted.age;
    if (extracted.phone) $('patientPhoneField').value = extracted.phone;
}

function showExtractedPreview(extracted, transcript) {
    const preview = $('aiPreview');
    const content = $('aiPreviewContent');
    if (!preview || !content) return;

    const symptoms = Array.isArray(extracted.symptoms) ? extracted.symptoms.join(', ') : extracted.symptoms;
    const history = Array.isArray(extracted.medical_history) ? extracted.medical_history.join(', ') : extracted.medical_history;

    content.innerHTML = `
        <div class="ex-grid">
            <div class="ex-cell"><span class="ex-lbl">IDENTIFIED NAME</span><span class="ex-val">${extracted.name || '—'}</span></div>
            <div class="ex-cell"><span class="ex-lbl">IDENTIFIED AGE</span><span class="ex-val">${extracted.age || '—'}</span></div>
            <div class="ex-cell"><span class="ex-lbl">CLINICAL SYMPTOMS</span><span class="ex-val">${symptoms || '—'}</span></div>
            <div class="ex-cell"><span class="ex-lbl">DURATION</span><span class="ex-val">${extracted.duration || '—'}</span></div>
        </div>
        <div class="ex-footer">
            <span class="ex-lbl">MEDICAL HISTORY MATCH:</span>
            <p class="ex-val-long">${history || 'None significant.'}</p>
        </div>
    `;
    preview.classList.remove('hidden');
    preview.style.display = 'block';
}

// ── UI Helpers ────────────────────────────────────────────────────────────────
function setRecordingUI(recording) {
    const btn = $('recordBtn');
    if (!btn) return;

    if (recording) {
        btn.classList.add('recording');
        btn.innerHTML = '<i class="fas fa-stop"></i>';
    } else {
        btn.classList.remove('recording');
        btn.innerHTML = '<i class="fas fa-microphone"></i>';
    }
}

function showStatus(type, html) {
    const el = $('transcriptionStatus');
    if (!el) return;
    el.className = `status-banner-${type}`;
    el.innerHTML = html;
    el.style.display = 'block';
}

function handleMicError(err) {
    let msg = 'Microphone access denied or error: ' + err.message;
    showStatus('error', '<i class="fas fa-exclamation-triangle"></i> ' + msg);
}

// ── Initialization ────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    // Record Button Setup
    const recBtn = $('recordBtn');
    if (recBtn) {
        recBtn.addEventListener('click', toggleRecording);
    }

    // Auto-dismiss alerts
    document.querySelectorAll('.alert').forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'all 0.5s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateX(20px)';
            setTimeout(() => alert.remove(), 500);
        }, 8000);
    });
});
