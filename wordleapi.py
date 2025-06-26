# Simple Flask backend to proxy Wordle API requests
from flask import Flask, jsonify
from flask_cors import CORS
import requests
import datetime
import pytz

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

@app.route('/wordle-word')
def get_wordle_word():
    try:
        # Get current date in IST (Indian Standard Time)
        ist = pytz.timezone('Asia/Kolkata')
        date = datetime.datetime.now(ist).date()

        url = f"https://www.nytimes.com/svc/wordle/v2/{date:%Y-%m-%d}.json"
        response = requests.get(url)
        data = response.json()
        return jsonify({
            'solution': data['solution'].upper(),
            'date': str(date),
            'timezone': 'IST'
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'fallback': 'REACT'
        }), 500


@app.route('/word-meaning/<word>')
def get_word_meaning_endpoint(word):
    """Standalone endpoint to get meaning of any word"""
    if not word or len(word) != 5:
        return jsonify({'error': 'Please provide a 5-letter word'}), 400

    meaning = get_word_meaning(word)
    if meaning:
        return jsonify(meaning)
    else:
        return jsonify({
            'error': 'Word meaning not found',
            'word': word.upper()
        }), 404

def get_word_meaning(word):
    """Fetch word meaning from Free Dictionary API"""
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word.lower()}"
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                entry = data[0]

                # Extract meanings
                meanings = []
                if 'meanings' in entry:
                    for meaning in entry['meanings'][:2]:  # Limit to first 2 parts of speech
                        part_of_speech = meaning.get('partOfSpeech', '')
                        definitions = meaning.get('definitions', [])

                        if definitions:
                            definition = definitions[0].get('definition', '')
                            if definition:
                                meanings.append({
                                    'partOfSpeech': part_of_speech,
                                    'definition': definition
                                })

                # Extract phonetics if available
                phonetic = ''
                if 'phonetics' in entry:
                    for p in entry['phonetics']:
                        if p.get('text'):
                            phonetic = p['text']
                            break

                return {
                    'word': word.upper(),
                    'phonetic': phonetic,
                    'meanings': meanings
                }

        return None


    except Exception as e:
        print(f"Error fetching meaning for {word}: {e}")
        return None


if __name__ == '__main__':
    app.run(debug=True, port=5000)

# To run:
# pip install flask flask-cors requests
# python app.py
# Then update the frontend to use: http://localhost:5000/wordle-word
