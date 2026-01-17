import os
import json
import firebase_admin
from firebase_admin import credentials, storage
from flask import Flask, render_template, request, session, jsonify
import google.generativeai as genai

app = Flask(__name__, template_folder='../templates')
app.secret_key = "niloy_ultra_secure_2026"

# --- Firebase Initialization ---
firebase_config = os.getenv("FIREBASE_CONFIG")
if firebase_config and not firebase_admin._apps:
    cred_dict = json.loads(firebase_config)
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred, {
        'storage_bucket': 'tryst-d3288.appspot.com'
    })

bucket = storage.bucket()

# --- Niloy AI Setup ---
genai.configure(api_key="AIzaSyAWHka0BBoaplW4_f4_Orq-zku8nGHIUYE")
# আমরা flash-8b ব্যবহার করছি যাতে Vercel-এ রেসপন্স সুপার ফাস্ট হয়
model = genai.GenerativeModel("gemini-1.5-flash-8b")

IDENTITY = "Your name is Niloy. You are a personal assistant for Niloy sir. Never mention Google, Gemini, or technical details. You answer strictly from the provided PDF memories."

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sync-memory', methods=['POST'])
def sync_memory():
    """Firebase থেকে ফাইলগুলো মেমরিতে লোড করার জন্য"""
    try:
        # 'permanent_memory' ফোল্ডারের ফাইলগুলো লিস্ট করা
        blobs = bucket.list_blobs(prefix="permanent_memory/")
        files = [blob.name.split('/')[-1] for blob in blobs if blob.name.endswith('.pdf')]
        return jsonify({'status': 'Found', 'files': files})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/chat', methods=['POST'])
def chat():
    user_msg = request.json.get('msg')
    
    try:
        # সরাসরি Firebase থেকে ৩টি PDF কন্টেন্ট নেওয়া
        blobs = bucket.list_blobs(prefix="permanent_memory/")
        pdf_contents = []
        for blob in list(blobs)[:3]:
            data = blob.download_as_bytes()
            pdf_contents.append({"mime_type": "application/pdf", "data": data})

        if not pdf_contents:
            return jsonify({'reply': "Sir, please upload PDFs to 'permanent_memory' folder in Firebase Storage first."})

        # AI Response Generation
        prompt = [IDENTITY] + pdf_contents + [user_msg]
        response = model.generate_content(prompt)
        
        return jsonify({'reply': response.text})
    except Exception as e:
        return jsonify({'reply': f"Error: {str(e)}. Please check your Firebase/API configuration."})

app = app
