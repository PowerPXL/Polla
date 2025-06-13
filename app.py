from flask import Flask, render_template, request, redirect
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

DATABASE_URL = os.getenv("DATABASE_URL")

# Initiera databasen (om tabellen inte finns)
def init_db():
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS votes (
                id SERIAL PRIMARY KEY,
                candidate TEXT UNIQUE NOT NULL,
                count INTEGER NOT NULL DEFAULT 0
            )
        ''')
        candidates = ['uffe', 'magda', 'jimmy', 'nooshi', 'annakarin', 'ebba', 'amandadaniel', 'romina']
        for candidate in candidates:
            c.execute("INSERT INTO votes (candidate, count) VALUES (%s, 0) ON CONFLICT (candidate) DO NOTHING", (candidate,))
        conn.commit()
        conn.close()
    except Exception as e:
        print("Error initializing DB:", e)

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/vote', methods=['POST'])
def vote():
    choice = request.form['candidate']
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        c = conn.cursor()
        c.execute("UPDATE votes SET count = count + 1 WHERE candidate = %s", (choice,))
        conn.commit()
        conn.close()
    except Exception as e:
        print("Error during vote:", e)
    return redirect('/results')

@app.route('/results')
def results():
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        c = conn.cursor()
        c.execute("SELECT candidate, count FROM votes ORDER BY count DESC")
        data = c.fetchall()
        conn.close()
    except Exception as e:
        print("Error fetching results:", e)
        data = []

    total_votes = sum(item['count'] for item in data)
    results = []
    for i, item in enumerate(data, start=1):
        procent = (item['count'] / total_votes * 100) if total_votes > 0 else 0
        results.append({
            "candidate": item['candidate'],
            "count": item['count'],
            "rank": i,
            "procent": procent
        })
    return render_template('results.html', results=results)

@app.route('/test-secret')
def test_secret():
    if app.secret_key:
        return f"Secret key is set! Length: {len(app.secret_key)}"
    else:
        return "Secret key is NOT set!"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
