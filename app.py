from flask import Flask, request, jsonify, render_template
import os
import speech_recognition as sr
from pydub import AudioSegment
import spacy
from textblob import TextBlob

app = Flask(__name__)

# Load spaCy NLP model
nlp = spacy.load("en_core_web_sm")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_audio():
    if 'audio' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    # Debugging: Print received file info
    print(f"Received file: {audio_file.filename}")

    # Ensure uploads directory exists
    upload_folder = os.path.join("static", "uploads")
    os.makedirs(upload_folder, exist_ok=True)

    # Save the uploaded file
    save_path = os.path.join(upload_folder, audio_file.filename)
    audio_file.save(save_path)

    # Convert audio to WAV format
    try:
        wav_path = save_path.rsplit('.', 1)[0] + ".wav"
        audio = AudioSegment.from_file(save_path)
        audio.export(wav_path, format="wav")
        print(f"Converted to WAV: {wav_path}")
    except Exception as e:
        print("Audio conversion error:", e)
        return jsonify({"error": "Failed to process audio file"}), 500

    # Speech-to-Text using Google STT
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            response_text = recognizer.recognize_google(audio_data)
    except sr.UnknownValueError:
        response_text = "Could not understand audio."
    except sr.RequestError:
        response_text = "Google STT request failed."
    except Exception as e:
        print("STT error:", e)
        return jsonify({"error": "Speech recognition failed"}), 500

    # ✅ Text Enhancement
    def enhance_text(text):
        doc = nlp(text)
        corrected_text = TextBlob(text).correct()  # Fix grammar
        enhanced_text = " ".join([token.text.capitalize() if token.pos_ == "PROPN" else token.text for token in doc])
        return str(corrected_text) if corrected_text else enhanced_text

    enhanced_text = enhance_text(response_text)
    print(f"Enhanced Text: {enhanced_text}")

    # Return JSON response
    return jsonify({"text": enhanced_text, "audio": f"/{save_path}"})

if __name__ == '__main__':
    app.run(debug=True)
