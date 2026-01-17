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

# --- AI Setup (Gemini 1.5 Flash - Best for PDFs) ---
genai.configure(api_key=os.getenv("API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# Strict instruction: No extra talk, only Bengali/Banglish mix
SYSTEM_PROMPT = (
    "Your name is Niloy. Respond ONLY with the requested answer from the PDFs. "
    "Do not use introductory phrases like 'According to the document' or 'Hello'. "
    "Keep it strictly to the point in a natural mix of Bengali and Banglish."
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
        pdf_contents = []
        for blob in list(blobs)[:3]:
            data = blob.download_as_bytes()
            # 400 error bondho korte check kora hocche jate file size 0 na hoy
            if data and len(data) > 100: 
                pdf_contents.append({"mime_type": "application/pdf", "data": data})
        
        if not pdf_contents:
            return jsonify({'reply': "Sir, storage-e kono valid PDF paini."})

        # AI Response Generation
        response = model.generate_content([SYSTEM_PROMPT] + pdf_contents + [user_msg])
        return jsonify({'reply': response.text.strip()})
    except Exception as e:
        return jsonify({'reply': f"Error: {str(e)}"})

app = app
