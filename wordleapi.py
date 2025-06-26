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

if __name__ == '__main__':
    app.run(debug=True, port=5000)

# To run:
# pip install flask flask-cors requests pytz
# python app.py
# Then update the frontend to use: http://localhost:5000/wordle-word
