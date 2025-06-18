from flask import Flask, render_template, request, redirect, url_for
import os
import psycopg2
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback-secret")

DATABASE_URL = os.getenv("DATABASE_URL")

# --- Databasanslutning och init ---
def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

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

# --- Flask-Login setup ---
login_manager = LoginManager(app)
login_manager.login_view = "login"

# --- OAuth setup ---
oauth = OAuth(app)

google = oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# --- User klass och in-memory storage ---
class User(UserMixin):
    def __init__(self, id_, email):
        self.id = id_
        self.email = email

users = {}

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

# --- Routes ---
@app.route('/')
def index():
    if current_user.is_authenticated:
        return f"Inloggad som {current_user.email} <br><a href='/logout'>Logga ut</a>"
    else:
        return "Inte inloggad <br><a href='/login'>Logga in med Google</a>"

@app.route('/login')
def login():
    redirect_uri = url_for('authorize', _external=True)
    print(f"[DEBUG] Redirect URI = {redirect_uri}")
    return google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    try:
        token = google.authorize_access_token()
        print("[DEBUG] Token:", token)

        resp = google.get('userinfo')
        print("[DEBUG] Userinfo response:", resp)

        user_info = resp.json()
        print("[DEBUG] User info JSON:", user_info)

        user = User(user_info['id'], user_info['email'])
        users[user.id] = user
        login_user(user)
        return redirect('/')
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"OAuth Error: {str(e)}", 500

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route('/vote', methods=['POST'])
@login_required
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

@app.route('/debug-redirect-uri')
def debug_redirect_uri():
    return url_for('authorize', _external=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

@app.route('/debug-oauth-vars')
def debug_vars():
    return {
        "client_id_raw": os.getenv("GOOGLE_CLIENT_ID"),
        "client_id_repr": repr(os.getenv("GOOGLE_CLIENT_ID")),
        "client_secret_set": bool(os.getenv("GOOGLE_CLIENT_SECRET")),
        "client_secret_repr": repr(os.getenv("GOOGLE_CLIENT_SECRET"))
    }

@app.route('/debug-env')
def debug_env():
    from flask import jsonify
    return jsonify({
        "GOOGLE_CLIENT_ID": os.getenv("GOOGLE_CLIENT_ID"),
        "GOOGLE_CLIENT_SECRET": os.getenv("GOOGLE_CLIENT_SECRET"),
        "SECRET_KEY": os.getenv("SECRET_KEY")
    })
