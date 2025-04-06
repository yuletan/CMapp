from flask import Flask, request, jsonify, send_from_directory
from googletrans import Translator
from bs4 import BeautifulSoup

app = Flask(__name__, static_url_path='', static_folder='.')
translator = Translator()

@app.route('/')
def index():
    return send_from_directory('.', 'test.html')

# Translation endpoint to handle plain text translation from API responses
@app.route('/translate', methods=['POST'])
def translate():
    data = request.get_json()
    text = data.get('text', '')
    target_lang = data.get('target_lang', 'en')
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    try:
        translated = translator.translate(text, dest=target_lang)
        return jsonify({'translated_text': translated.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000)
