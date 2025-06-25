from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import psycopg2
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    raise RuntimeError("SECRET_KEY environment variable is not set!")
app.secret_key = secret_key

DATABASE_URL = os.getenv("DATABASE_URL")

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

login_manager = LoginManager(app)
login_manager.login_view = "login"

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

class User(UserMixin):
    def __init__(self, id_, email):
        self.id = id_
        self.email = email

users = {}

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

@app.route('/')
def index():
    return render_template("index.html", logged_in=current_user.is_authenticated)

@app.route('/login')
def login():
    # Hämta next-param för att veta vart vi ska efter inloggning
    next_page = request.args.get('next') or url_for('index')
    redirect_uri = url_for('authorize', _external=True, next=next_page)
    print(f"🔁 Redirect URI sent to Google: {redirect_uri}")  # Lägg till denna
    return oauth.google.authorize_redirect(redirect_uri)
    
@app.route('/authorize')
def authorize():
    token = google.authorize_access_token()
    user_info = google.get('https://openidconnect.googleapis.com/v1/userinfo').json()
    user = User(user_info['sub'], user_info['email'])
    users[user.id] = user
    login_user(user)
    # Hämta next och redirecta dit
    next_page = request.args.get('next') or url_for('index')
    return redirect(next_page)
    
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route('/vote', methods=['GET', 'POST'])
def vote():
    if request.method == 'POST':
        candidate = request.form.get('candidate')
    else:
        candidate = request.args.get('candidate')

    if not current_user.is_authenticated:
        login_url = url_for('login', next=request.url)
        return redirect(login_url)

    if candidate:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE votes SET count = count + 1 WHERE candidate = %s;", (candidate,))
        conn.commit()
        cur.close()
        conn.close()

    return redirect(url_for('results'))

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)



