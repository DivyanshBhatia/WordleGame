# Simple Flask backend to proxy Wordle API requests
from flask import Flask, jsonify
from flask import request
from flask_cors import CORS
import requests
import datetime
import pytz
from deep_translator import GoogleTranslator

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

import random
from datetime import datetime, timedelta

@app.route('/wordle-word')
def get_wordle_word():
    try:
        # Get the 'today' parameter from query string, default to True
        today_param = request.args.get('today', 'true').lower()
        today = today_param == 'true'

        # Get current date in IST (Indian Standard Time)
        ist = pytz.timezone('Asia/Kolkata')
        current_date = datetime.now(ist).date()

        if today:
            # Use current date
            date = current_date
        else:
            # Generate random date within last 730 days (excluding today)
            days_back = random.randint(1, 730)
            date = current_date - timedelta(days=days_back)

        url = f"https://www.nytimes.com/svc/wordle/v2/{date:%Y-%m-%d}.json"
        response = requests.get(url)
        data = response.json()

        return jsonify({
            'solution': data['solution'].upper(),
            'date': str(date),
            'timezone': 'IST',
            'is_today': today
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
            'error': 'Word meaning not found in any dictionary source',
            'word': word.upper()
        }), 404

def get_hindi_translation(word):
    """Get Hindi translation of the word"""
    try:
        # Method 1: Using deep-translator (no API key needed) - RECOMMENDED
        translator_dt = GoogleTranslator(source='en', target='hi')
        return translator_dt.translate(word)
        
        # Method 2: Using googletrans (has cgi module issues in Python 3.13+)
        # translated = translator.translate(word, src='en', dest='hi')
        # return translated.text
        
        # Method 3: Using Google Cloud Translate (requires API key)
        # result = translate_client.translate(word, source_language='en', target_language='hi')
        # return result['translatedText']
        
    except Exception as e:
        print(f"Error translating {word} to Hindi: {e}")
        return None

def get_word_meaning(word):
    """Fetch word meaning from multiple dictionary APIs with fallback"""

    # Try primary API: Free Dictionary API
    meaning = get_meaning_from_free_dictionary(word)
    if meaning:
        return meaning

    # Try fallback API 1: Merriam-Webster Collegiate Dictionary
    meaning = get_meaning_from_merriam_webster_collegiate(word)
    if meaning:
        return meaning

    # Try fallback API 2: Merriam-Webster Learner's Dictionary
    meaning = get_meaning_from_merriam_webster_learners(word)
    if meaning:
        return meaning

    # Try fallback API 3: Built-in Dictionary (last resort)
    meaning = get_builtin_dictionary_meaning(word)
    if meaning:
        return meaning

    return None

def get_meaning_from_free_dictionary(word):
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
                    for meaning in entry['meanings'][:3]:  # Limit to first 3 parts of speech
                        part_of_speech = meaning.get('partOfSpeech', '')
                        definitions = meaning.get('definitions', [])

                        if definitions:
                            i = 0
                            while i < 5 and i < len(definitions):
                                definition = definitions[i].get('definition', '')
                                example = definitions[i].get('example', '')
                                if definition:
                                    meanings.append({
                                        'partOfSpeech': part_of_speech,
                                        'definition': definition,
                                        'example': example
                                    })
                                i = i + 1

                # Extract phonetics if available
                phonetic = ''
                if 'phonetics' in entry:
                    for p in entry['phonetics']:
                        if p.get('text'):
                            phonetic = p['text']
                            break
                hindi_translation = get_hindi_translation(word)
                return {
                    'word': word.upper(),
                    'phonetic': phonetic,
                    'meanings': meanings,
                    'source': 'Free Dictionary API',
                    'hindi_translation': hindi_translation if hindi_translation else ''
                }

        return None

    except Exception as e:
        print(f"Error fetching meaning from Free Dictionary API for {word}: {e}")
        return None

def get_meaning_from_merriam_webster_collegiate(word):
    """Fetch word meaning from Merriam-Webster Collegiate Dictionary API"""
    try:
        API_KEY = "9967016c-b19b-431c-937c-f661c4606e5d"
        url = f"https://www.dictionaryapi.com/api/v3/references/collegiate/json/{word.lower()}?key={API_KEY}"
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0 and isinstance(data[0], dict):
                entry = data[0]

                meanings = []
                if 'shortdef' in entry:
                    # Get the functional label (part of speech)
                    part_of_speech = entry.get('fl', 'unknown')

                    for definition in entry['shortdef'][:3]:  # Limit to 3 definitions
                        meanings.append({
                            'partOfSpeech': part_of_speech,
                            'definition': definition,
                            'example': ''
                        })

                # Get pronunciation if available
                phonetic = ''
                if 'hwi' in entry and 'prs' in entry['hwi']:
                    prs = entry['hwi']['prs']
                    if prs and len(prs) > 0 and 'mw' in prs[0]:
                        phonetic = f"/{prs[0]['mw']}/"
                hindi_translation = get_hindi_translation(word)
                if meanings:
                    return {
                        'word': word.upper(),
                        'phonetic': phonetic,
                        'meanings': meanings,
                        'source': 'Merriam-Webster Collegiate',
                        'hindi_translation': hindi_translation if hindi_translation else ''
                    }

        return None

    except Exception as e:
        print(f"Error fetching meaning from Merriam-Webster Collegiate for {word}: {e}")
        return None

def get_meaning_from_merriam_webster_learners(word):
    """Fetch word meaning from Merriam-Webster Learner's Dictionary API"""
    try:
        API_KEY = "80a563cd-5cf4-4ee1-afe7-1ca26f7b1b45"
        url = f"https://www.dictionaryapi.com/api/v3/references/learners/json/{word.lower()}?key={API_KEY}"
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0 and isinstance(data[0], dict):
                entry = data[0]

                meanings = []
                if 'shortdef' in entry:
                    # Get the functional label (part of speech)
                    part_of_speech = entry.get('fl', 'unknown')

                    for definition in entry['shortdef'][:3]:  # Limit to 3 definitions
                        meanings.append({
                            'partOfSpeech': part_of_speech,
                            'definition': definition,
                            'example': ''
                        })

                # Get pronunciation if available
                phonetic = ''
                if 'hwi' in entry and 'prs' in entry['hwi']:
                    prs = entry['hwi']['prs']
                    if prs and len(prs) > 0 and 'mw' in prs[0]:
                        phonetic = f"/{prs[0]['mw']}/"
                hindi_translation = get_hindi_translation(word)
                if meanings:
                    return {
                        'word': word.upper(),
                        'phonetic': phonetic,
                        'meanings': meanings,
                        'source': 'Merriam-Webster Learners',
                        'hindi_translation': hindi_translation if hindi_translation else ''
                    }

        return None

    except Exception as e:
        print(f"Error fetching meaning from Merriam-Webster Learners for {word}: {e}")
        return None

def get_meaning_from_dictionary_api(word):
    """This function is now replaced by get_builtin_dictionary_meaning"""
    return get_builtin_dictionary_meaning(word)

def get_builtin_dictionary_meaning(word):
    """Built-in fallback dictionary for common Wordle words"""
    try:
        # Simple fallback dictionary for common Wordle words
        fallback_definitions = {
            'react': {
                'word': word.upper(),
                'phonetic': '/riˈækt/',
                'meanings': [{
                    'partOfSpeech': 'verb',
                    'definition': 'respond or behave in a particular way as a result of or in response to something',
                    'example': 'He reacted angrily to the news'
                }],
                'source': 'Fallback Dictionary'
            },
            'words': {
                'word': word.upper(),
                'phonetic': '/wɜrdz/',
                'meanings': [{
                    'partOfSpeech': 'noun',
                    'definition': 'a single distinct meaningful element of speech or writing',
                    'example': 'He wrote down the words on paper'
                }],
                'source': 'Fallback Dictionary'
            },
            'build': {
                'word': word.upper(),
                'phonetic': '/bɪld/',
                'meanings': [{
                    'partOfSpeech': 'verb',
                    'definition': 'construct something by putting parts or material together',
                    'example': 'They are going to build a new house'
                }],
                'source': 'Fallback Dictionary'
            },
            'game': {
                'word': word.upper(),
                'phonetic': '/ɡeɪm/',
                'meanings': [{
                    'partOfSpeech': 'noun',
                    'definition': 'a form of play or sport with rules',
                    'example': 'Let us play a game of chess'
                }],
                'source': 'Built-in Dictionary'
            },
            'daily': {
                'word': word.upper(),
                'phonetic': '/ˈdeɪli/',
                'meanings': [{
                    'partOfSpeech': 'adjective',
                    'definition': 'done, produced, or occurring every day',
                    'example': 'Her daily routine includes morning exercise'
                }],
                'source': 'Built-in Dictionary'
            },
            'about': {
                'word': word.upper(),
                'phonetic': '/əˈbaʊt/',
                'meanings': [{
                    'partOfSpeech': 'preposition',
                    'definition': 'on the subject of; concerning',
                    'example': 'We talked about the weather'
                }],
                'source': 'Built-in Dictionary'
            },
            'first': {
                'word': word.upper(),
                'phonetic': '/fɜrst/',
                'meanings': [{
                    'partOfSpeech': 'adjective',
                    'definition': 'coming before all others in time or order',
                    'example': 'This is my first attempt'
                }],
                'source': 'Built-in Dictionary'
            },
            'other': {
                'word': word.upper(),
                'phonetic': '/ˈʌðər/',
                'meanings': [{
                    'partOfSpeech': 'adjective',
                    'definition': 'used to refer to a person or thing that is different',
                    'example': 'The other team won the game'
                }],
                'source': 'Built-in Dictionary'
            }
        }

        word_lower = word.lower()
        if word_lower in fallback_definitions:
            return fallback_definitions[word_lower]

        return None

    except Exception as e:
        print(f"Error fetching meaning from built-in dictionary for {word}: {e}")
        return None

if __name__ == '__main__':
    app.run(debug=True, port=5000)

# To run:
# pip install flask flask-cors requests pytz
# python app.py
# Then update the frontend to use: http://localhost:5000/wordle-word

# Additional APIs you can integrate:
# 1. WordsAPI via RapidAPI: https://rapidapi.com/dpventures/api/wordsapi/ (2500 free/day)
# 2. Oxford Dictionary API: https://developer.oxforddictionaries.com/
# 3. Cambridge Dictionary API: https://dictionary.cambridge.org/

# Current API chain provides excellent coverage:
# - Free Dictionary API (unlimited, free)
# - Merriam-Webster Collegiate (1000/day, high quality)
# - Merriam-Webster Learners (1000/day, simpler definitions)
# - Built-in dictionary (unlimited, basic coverage)
