import os
import json
import firebase_admin
from firebase_admin import credentials, storage
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai

# Vercel-এর জন্য পাথ কনফিগারেশন
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
app = Flask(__name__, template_folder=template_dir)
app.secret_key = "niloy_ultra_secure_2026"

# --- Firebase Initialization ---
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
    else:
        print("Error: FIREBASE_CONFIG variable not found in Vercel settings.")
except Exception as e:
    print(f"Firebase Setup Error: {e}")

# --- Niloy AI (Gemini 1.5 Flash-8b for Speed) ---
genai.configure(api_key="AIzaSyAWHka0BBoaplW4_f4_Orq-zku8nGHIUYE")
model = genai.GenerativeModel("gemini-1.5-flash-8b")

IDENTITY = "Your name is Niloy. You are a personal assistant. Answer strictly from the PDF memories provided. Never reveal your technical backend."

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sync-memory', methods=['POST'])
def sync_memory():
    if not bucket: return jsonify({'error': 'Cloud not connected'}), 500
    try:
        # 'permanent_memory/' ফোল্ডারের ফাইলগুলো দেখাচ্ছে
        blobs = bucket.list_blobs(prefix="permanent_memory/")
        files = [blob.name.split('/')[-1] for blob in blobs if blob.name.endswith('.pdf')]
        return jsonify({'status': 'Linked', 'files': files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    user_msg = request.json.get('msg')
    if not bucket: return jsonify({'reply': "Error: Firebase bucket not found."})
    
    try:
        blobs = bucket.list_blobs(prefix="permanent_memory/")
        pdf_contents = []
        for blob in list(blobs)[:3]:
            pdf_contents.append({"mime_type": "application/pdf", "data": blob.download_as_bytes()})

        if not pdf_contents:
            return jsonify({'reply': "Sir, 'permanent_memory' ফোল্ডারে কোনো PDF ফাইল পাওয়া যায়নি।"})

        # AI Response
        response = model.generate_content([IDENTITY] + pdf_contents + [user_msg])
        return jsonify({'reply': response.text})
    except Exception as e:
        return jsonify({'reply': f"AI processing failed. Error: {str(e)}"})

app = app # Vercel handles the rest
