from flask import Flask, render_template, request, redirect
import os
import psycopg2

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback-secret")

DATABASE_URL = os.getenv("DATABASE_URL")

# Skapa en global databasanslutning (enkelt men inte trådsäkert – duger för mindre appar)
def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

# Initiera databasen och skapa tabellen om den inte finns
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            id SERIAL PRIMARY KEY,
            candidate TEXT UNIQUE NOT NULL,
            count INTEGER NOT NULL DEFAULT 0
        );
    """)
    conn.commit()

    candidates = ['uffe', 'magda', 'jimmy', 'nooshi', 'annakarin', 'ebba', 'amandadaniel', 'romina']
    for candidate in candidates:
        cur.execute("INSERT INTO votes (candidate, count) VALUES (%s, 0) ON CONFLICT (candidate) DO NOTHING;", (candidate,))
    conn.commit()
    cur.close()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/vote', methods=['POST'])
def vote():
    choice = request.form['candidate']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE votes SET count = count + 1 WHERE candidate = %s;", (choice,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/results')

@app.route('/results')
def results():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT candidate, count FROM votes ORDER BY count DESC;")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    total_votes = sum(row[1] for row in rows)
    results = []
    for i, row in enumerate(rows, start=1):
        candidate, count = row
        procent = (count / total_votes * 100) if total_votes > 0 else 0
        results.append({
            "candidate": candidate,
            "count": count,
            "rank": i,
            "procent": procent
        })

    return render_template('results.html', results=results)

@app.route('/test-secret')
def test_secret():
    return f"Secret key is set! Length: {len(app.secret_key)}"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    a
