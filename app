from flask import Flask, render_template, request, redirect
import sqlite3
import os

app = Flask(__name__)

DB_FILE = 'database.db'

# Initiera databasen
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

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
