import os
import json
import firebase_admin
from firebase_admin import credentials, storage
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
app = Flask(__name__, template_folder=template_dir)
app.secret_key = "niloy_ultra_secure_2026"

# --- Firebase Setup ---
firebase_config = os.getenv("FIREBASE_CONFIG")
if firebase_config and not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(firebase_config))
    firebase_admin.initialize_app(cred, {'storageBucket': 'tryst-d3288.appspot.com'})

bucket = storage.bucket()

# --- AI Setup (Gemini 2.5 Flash) ---
genai.configure(api_key=os.getenv("API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

# Strict instruction to avoid extra talk
SYSTEM_PROMPT = (
    "Your name is Niloy. Respond ONLY with the information found in the PDFs. "
    "Do not include conversational filler, introductory phrases, or extra text. "
    "Use a concise mix of Bengali and Banglish. If not found, say 'Sir, memory-te nei'."
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sync-memory', methods=['POST'])
def sync_memory():
    try:
        blobs = bucket.list_blobs(prefix="permanent_memory/")
        files = [blob.name.split('/')[-1] for blob in blobs if blob.name.endswith('.pdf')]
        return jsonify({'status': 'Linked', 'files': files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    user_msg = request.json.get('msg')
    try:
        blobs = bucket.list_blobs(prefix="permanent_memory/")
        pdf_contents = [{"mime_type": "application/pdf", "data": b.download_as_bytes()} for b in list(blobs)[:3]]
        
        if not pdf_contents:
            return jsonify({'reply': "Sir, memory empty."})

        response = model.generate_content([SYSTEM_PROMPT] + pdf_contents + [user_msg])
        return jsonify({'reply': response.text.strip()})
    except Exception as e:
        return jsonify({'reply': f"Error: {str(e)}"})

app = app
