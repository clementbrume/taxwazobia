from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import openai
import faiss
import json
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Database configuration
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///metrics.db")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# OpenAI key
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    print("Warning: OPENAI_API_KEY is not set!")

# ---------------------------
# Database Model
# ---------------------------
class UsageMetric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.String(100), unique=True)
    first_seen = db.Column(db.DateTime, default=datetime.utcnow)
    error_count = db.Column(db.Integer, default=0)

with app.app_context():
    db.create_all()

# ---------------------------
# Load FAISS Knowledge Base
# ---------------------------
index = None
sources = None

faiss_index_path = "knowledge_base/index.faiss"
sources_path = "knowledge_base/sources.json"

if os.path.exists(faiss_index_path) and os.path.exists(sources_path):
    try:
        index = faiss.read_index(faiss_index_path)
        with open(sources_path, "r", encoding="utf-8") as f:
            sources = json.load(f)
    except Exception as e:
        print("Error loading FAISS index or sources:", e)
else:
    print(f"FAISS index or sources not found: {faiss_index_path}, {sources_path}")

# ---------------------------
# Helper Functions
# ---------------------------
def embed_text(text):
    if not openai.api_key:
        raise ValueError("OpenAI API key not set.")
    from openai import OpenAI
    client = OpenAI(api_key=openai.api_key)
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return np.array(response.data[0].embedding).astype("float32")

def retrieve_context(query, k=3):
    if index is None or sources is None:
        return "Knowledge base not available."
    try:
        query_embedding = embed_text(query)
        distances, indices = index.search(np.array([query_embedding]), k)
        context = "\n\n".join([sources[str(i)] for i in indices[0] if str(i) in sources])
        return context
    except Exception as e:
        print("Error retrieving context:", e)
        return "Knowledge base unavailable."

def generate_response(user_message):
    try:
        context = retrieve_context(user_message)
        prompt = f"""
You are TaxWazobia, an expert Nigerian tax advisor. Use Nigerian tax laws and relevant sections.
User question: {user_message}

Relevant context:
{context}

Provide an accurate, law-based explanation in clear professional language.
"""
        from openai import OpenAI
        client = OpenAI(api_key=openai.api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a Nigerian tax law expert."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("Error generating response:", e)
        return "Sorry, I encountered an error while processing your question."

# ---------------------------
# Routes
# ---------------------------
@app.route('/')
def home():
    return render_template("index.html")

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get("message", "")
    if not user_message:
        return jsonify({"reply": "Please enter a valid message."})
    bot_reply = generate_response(user_message)
    return jsonify({"reply": bot_reply})

# ---------------------------
# Run (for local debugging)
# ---------------------------
if __name__ == '__main__':
    # Only debug locally; Render ignores this block
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
