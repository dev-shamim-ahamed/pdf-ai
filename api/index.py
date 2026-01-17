import os
import json
import firebase_admin
from firebase_admin import credentials, storage
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai

# পাথ এবং কনফিগারেশন
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
    print(f"Firebase Init Error: {e}")

# --- Niloy AI (Updated to Gemini 3 Pro Preview) ---
# আপনার নতুন তৈরি করা API Key এখানে দিন
genai.configure(api_key="AIzaSyBdlzv2ux22RGQFIe2u1_TidQv7VhOZwcY")
# আপনার স্ক্রিনশট অনুযায়ী মডেল কোডটি ব্যবহার করা হয়েছে
model = genai.GenerativeModel("gemini-1.5-flash") 

IDENTITY = "Your name is Niloy. You are a professional assistant. Answer strictly from the PDF documents provided."

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sync-memory', methods=['POST'])
def sync_memory():
    if not bucket: return jsonify({'error': 'Cloud connection failed'}), 500
    try:
        blobs = bucket.list_blobs(prefix="permanent_memory/")
        files = [blob.name.split('/')[-1] for blob in blobs if blob.name.endswith('.pdf')]
        return jsonify({'status': 'Linked', 'files': files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    user_msg = request.json.get('msg')
    if not bucket: return jsonify({'reply': "Error: Cloud connection failed."})
    
    try:
        blobs = bucket.list_blobs(prefix="permanent_memory/")
        pdf_contents = []
        # Gemini 3 Pro অনেক বড় কনটেক্সট হ্যান্ডেল করতে পারে
        for blob in list(blobs)[:3]:
            pdf_contents.append({"mime_type": "application/pdf", "data": blob.download_as_bytes()})

        if not pdf_contents:
            return jsonify({'reply': "Sir, 'permanent_memory' ফোল্ডারে কোনো PDF নেই।"})

        # AI Response Generation
        response = model.generate_content([IDENTITY] + pdf_contents + [user_msg])
        return jsonify({'reply': response.text})
    except Exception as e:
        # এটি ৫০০ এরর হওয়া আটকাবে এবং চ্যাট বক্সেই এরর দেখাবে
        return jsonify({'reply': f"AI processing failed. Please check if the API key and model are active. Error: {str(e)}"})

app = app
