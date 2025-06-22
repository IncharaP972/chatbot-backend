from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------------------------
# 1. Intent detection (kept mostly for /test-intents; chat forces "brief")
# ---------------------------------------------------------------------------
def analyze_user_intent(user_message: str) -> str:
    """Classify intent; not used in /chat because we force 'brief'."""
    message = user_message.lower().strip()

    greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']
    if message in greetings or len(message) <= 3:
        return "brief"

    # Indicators (for completeness)
    detail_indicators = [
        'how to', 'explain', 'why', 'process', 'steps',
        'guide', 'tutorial', 'detailed', 'comprehensive', 'complete',
        'tell me about', 'walk me through', 'show me', 'teach me',
        'benefits', 'what should i do'
    ]
    brief_indicators = [
        'yes or no', 'quickly', 'briefly', 'short answer', 'simple',
        'can i', 'is it', 'does it', 'will it', 'should i', 'what is'
    ]

    if any(i in message for i in detail_indicators):
        return "detailed"
    if any(i in message for i in brief_indicators):
        return "brief"
    return "moderate"

# ---------------------------------------------------------------------------
# 2. Prompt builder – generic, short-answer assistant
# ---------------------------------------------------------------------------
def create_smart_prompt(user_message: str, lang: str = "en") -> str:
    """Return a single short system prompt + the user message."""
    greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']
    if user_message.lower().strip() in greetings:
        return (
            "You are a friendly AI assistant. "
            "Greet the user briefly (1 sentence) and mention you answer questions in concise form. "
            f"User said: {user_message}"
        )

    # Language-specific brief instruction
    base_prompts = {
        "en": "You are a knowledgeable AI assistant. Answer the user's question in no more than two clear, direct sentences.",
        "hi": "आप एक ज्ञानपूर्ण AI सहायक हैं। उपयोगकर्ता के प्रश्न का उत्तर अधिकतम दो संक्षिप्त वाक्यों में दें।",
        "es": "Eres un asistente de IA bien informado. Responde la pregunta del usuario en no más de dos frases claras."
    }
    system_prompt = base_prompts.get(lang, base_prompts["en"])

    return f"{system_prompt}\nUser question: {user_message}"

# ---------------------------------------------------------------------------
# 3. /chat endpoint – always BRIEF for speed
# ---------------------------------------------------------------------------
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json or {}
    user_message = data.get("message", "")
    lang = data.get("lang", "en")

    if not user_message.strip():
        return jsonify({"response": "Please enter a question."}), 400

    print(f"Received: {user_message}")

    # Always brief
    smart_prompt = create_smart_prompt(user_message, lang)
    print("Prompt generated.")

    ollama_payload = {
        "model": "phi3:mini",          # adjust if you prefer another local model
        "prompt": smart_prompt,
        "stream": False,
        "options": {
            "temperature": 0.5,
            "top_p": 0.8,
            "max_tokens": 30           # keeps answers very short
        }
    }

    try:
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json=ollama_payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
    except requests.exceptions.ConnectionError:
        return jsonify({"response": "Cannot reach Ollama – is it running?"}), 500
    except requests.exceptions.Timeout:
        return jsonify({"response": "AI service timed out, please retry."}), 500

    if resp.status_code != 200:
        print("Ollama error:", resp.status_code, resp.text)
        return jsonify({"response": "AI service error."}), 500

    ai_text = resp.json().get("response", "").strip()

    # safety cut – keep ≤ 2 sentences
    pieces = ai_text.split('. ')
    if len(pieces) > 2:
        ai_text = '. '.join(pieces[:2]).rstrip('.') + '.'

    print("Reply:", ai_text)
    return jsonify({"response": ai_text, "response_type": "brief"})

# ---------------------------------------------------------------------------
# 4. Health-check endpoint
# ---------------------------------------------------------------------------
@app.route('/health', methods=['GET'])
def health():
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        if r.status_code == 200:
            models = [m['name'] for m in r.json().get('models', [])]
            return jsonify({"status": "healthy", "available_models": models})
        return jsonify({"status": "unhealthy"}), 500
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

# ---------------------------------------------------------------------------
# 5. Intent-testing endpoint (optional utility)
# ---------------------------------------------------------------------------
@app.route('/test-intents', methods=['POST'])
def test_intents():
    msgs = (request.json or {}).get("messages", [])
    return jsonify({
        "results": [
            {"message": m, "detected_intent": analyze_user_intent(m)}
            for m in msgs
        ]
    })

# ---------------------------------------------------------------------------
if __name__ == '__main__':
    print("General-purpose Chatbot backend starting on http://localhost:5001 …")
    app.run(port=5001, debug=True)
