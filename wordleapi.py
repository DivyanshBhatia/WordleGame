# Simple Flask backend to proxy Wordle API requests with word meanings
from flask import Flask, jsonify
from flask_cors import CORS
import requests
import datetime

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

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

@app.route('/wordle-word')
def get_wordle_word():
    try:
        date = datetime.date.today()
        url = f"https://www.nytimes.com/svc/wordle/v2/{date:%Y-%m-%d}.json"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        solution = data['solution'].upper()
        
        # Get word meaning
        word_info = get_word_meaning(solution)
        
        result = {
            'solution': solution,
            'date': str(date)
        }
        
        # Add meaning if found
        if word_info:
            result['meaning'] = word_info
        else:
            result['meaning'] = {
                'word': solution,
                'phonetic': '',
                'meanings': [{'partOfSpeech': 'unknown', 'definition': 'Definition not available'}]
            }
        
        return jsonify(result)
        
    except requests.RequestException as e:
        return jsonify({
            'error': f'Failed to fetch word: {str(e)}',
            'solution': 'REACT',
            'date': str(datetime.date.today()),
            'meaning': {
                'word': 'REACT',
                'phonetic': '/riˈækt/',
                'meanings': [
                    {
                        'partOfSpeech': 'verb',
                        'definition': 'respond or behave in a particular way in response to something'
                    }
                ]
            }
        }), 500
    except Exception as e:
        return jsonify({
            'error': f'Unexpected error: {str(e)}',
            'solution': 'REACT',
            'date': str(datetime.date.today()),
            'meaning': {
                'word': 'REACT',
                'phonetic': '/riˈækt/',
                'meanings': [
                    {
                        'partOfSpeech': 'verb', 
                        'definition': 'respond or behave in a particular way in response to something'
                    }
                ]
            }
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)

# To run:
# pip install flask flask-cors requests
# python wordleapi.py
# 
# Example response:
# {
#   "solution": "COMFY",
#   "date": "2025-06-26",
#   "meaning": {
#     "word": "COMFY",
#     "phonetic": "/ˈkʌmfi/",
#     "meanings": [
#       {
#         "partOfSpeech": "adjective",
#         "definition": "giving a feeling of physical relaxation and ease"
#       }
#     ]
#   }
# }
