import os
import json
import uuid
import firebase_admin
from firebase_admin import credentials, storage
from flask import Flask, render_template, request, session, jsonify
import google.generativeai as genai

app = Flask(__name__, template_folder='../templates')
app.secret_key = "niloy_ultra_secure_2026"

# --- Firebase Config ---
firebase_config = os.getenv("FIREBASE_CONFIG")
if firebase_config and not firebase_admin._apps:
    cred_dict = json.loads(firebase_config)
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'moneymng.firebasestorage.app'
    })

bucket = storage.bucket()

# --- Niloy AI Setup ---
genai.configure(api_key="AIzaSyAWHka0BBoaplW4_f4_Orq-zku8nGHIUYE")
model = genai.GenerativeModel("gemini-1.5-flash")

IDENTITY = "Your name is Niloy. You are a personal thought partner for Niloy sir. Never mention Google or Gemini. If asked, you are Niloy AI."

@app.route('/')
def index():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    sid = session.get('session_id')
    files = request.files.getlist('pdf')
    if not files:
        return jsonify({'error': 'No files'}), 400
    
    # Ekshathe shorboccho 3-ti file allow kora hobe
    for file in files[:3]:
        blob = bucket.blob(f"memories/{sid}/{file.filename}")
        blob.upload_from_string(file.read(), content_type='application/pdf')
    
    return jsonify({'status': 'All files synced'})

@app.route('/files', methods=['GET'])
def list_files():
    sid = session.get('session_id')
    blobs = bucket.list_blobs(prefix=f"memories/{sid}/")
    files = [blob.name.split('/')[-1] for blob in blobs]
    return jsonify({'files': files})

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    sid = session.get('session_id')
    blob = bucket.blob(f"memories/{sid}/{filename}")
    blob.delete()
    return jsonify({'status': 'Deleted'})

@app.route('/chat', methods=['POST'])
def chat():
    sid = session.get('session_id')
    user_msg = request.json.get('msg')
    
    blobs = bucket.list_blobs(prefix=f"memories/{sid}/")
    pdf_contents = []
    for blob in blobs:
        pdf_contents.append({"mime_type": "application/pdf", "data": blob.download_as_bytes()})

    prompt = [IDENTITY] + pdf_contents + [user_msg]
    response = model.generate_content(prompt)
    return jsonify({'reply': response.text})

app = app
