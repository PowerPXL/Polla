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
        for candidate in ['kristersson', 'svantesson', 'forssell']:
            c.execute("INSERT INTO votes (candidate, count) VALUES (?, ?)", (candidate, 0))
        conn.commit()
        conn.close()

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
    c.execute("SELECT candidate, count FROM votes")
    data = c.fetchall()
    conn.close()
    return render_template('results.html', results=data)

@app.route('/test-secret')
def test_secret():
    if app.secret_key:
        return f"Secret key is set! Length: {len(app.secret_key)}"
    else:
        return "Secret key is NOT set!"

# Kör servern EN gång
### DEBUG MODE ###
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)