from flask import Flask, render_template, request, redirect
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

DB_FILE = 'database.db'

# Definiera init_db FÖRST
def init_db():
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE votes (
                id INTEGER PRIMARY KEY,
                candidate TEXT NOT NULL,
                count INTEGER NOT NULL
            )
        ''')
        for candidate in ['uffe', 'magda', 'jimmy', 'nooshi', 'annakarin', 'ebba', 'amandadaniel', 'romina']:
            c.execute("INSERT INTO votes (candidate, count) VALUES (?, ?)", (candidate, 0))
        conn.commit()
        conn.close()
init_db()        

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/vote', methods=['POST'])
def vote():
    choice = request.form['candidate']
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE votes SET count = count + 1 WHERE candidate = ?", (choice,))
    conn.commit()
    conn.close()
    return redirect('/results')

@app.route('/results')
def results():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT candidate, count FROM votes ORDER BY count DESC")
    data = c.fetchall()
    conn.close()

    total_votes = sum(count for _, count in data)
    results = []
    for i, (candidate, count) in enumerate(data, start=1):
        procent = (count / total_votes * 100) if total_votes > 0 else 0
        results.append({
            "candidate": candidate,
            "count": count,
            "rank": i,
            "procent": procent
        })
    return render_template('results.html', results=results)
    
    # Lägg till rankning (1, 2, 3)
    ranked_results = []
    for i, (candidate, count) in enumerate(data, start=1):
        ranked_results.append({'candidate': candidate, 'count': count, 'rank': i})
    
    return render_template('results.html', results=ranked_results)

@app.route('/test-secret')
def test_secret():
    if app.secret_key:
        return f"Secret key is set! Length: {len(app.secret_key)}"
    else:
        return "Secret key is NOT set!"

# Kör servern EN gång
### DEBUG MODE ###
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)