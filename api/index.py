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
bucket = None
try:
    firebase_config_str = os.getenv("FIREBASE_CONFIG")
    if firebase_config_str:
        if not firebase_admin._apps:
            cred_dict = json.loads(firebase_config_str)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred, {
                'storageBucket': 'tryst-d3288.appspot.com'
            })
        bucket = storage.bucket()
except Exception as e:
    print(f"Firebase Error: {e}")

# --- Niloy AI (Gemini 2.5 Flash) ---
genai.configure(api_key="AIzaSyBdlzv2ux22RGQFIe2u1_TidQv7VhOZwcY")
model = genai.GenerativeModel("gemini-2.5-flash") #

# Persona setup for Bengali/Banglish mix
SYSTEM_PROMPT = (
    "Your name is Niloy. You are a personal assistant. "
    "Respond in a natural mix of Bengali and Banglish (e.g., 'Ji sir, ami check korchi'). "
    "Always use the provided PDF memories to answer. Be helpful and concise."
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sync-memory', methods=['POST'])
def sync_memory():
    if not bucket: return jsonify({'error': 'Cloud not connected'}), 500
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
            pdf_contents.append({"mime_type": "application/pdf", "data": blob.download_as_bytes()})

        if not pdf_contents:
            return jsonify({'reply': "Sir, 'permanent_memory' folder-e kono PDF paini. Please check korun."})

        response = model.generate_content([SYSTEM_PROMPT] + pdf_contents + [user_msg]) #
        return jsonify({'reply': response.text})
    except Exception as e:
        return jsonify({'reply': f"Opps! Ektu error hoyeche: {str(e)}"})

app = app
