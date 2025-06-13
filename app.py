from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Läs Supabase/Postgres-connection från miljövariabel
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Definiera Vote-modell (ersätter SQLite-tabellen)
class Vote(db.Model):
    __tablename__ = 'votes'
    id = db.Column(db.Integer, primary_key=True)
    candidate = db.Column(db.String(50), nullable=False, unique=True)
    count = db.Column(db.Integer, nullable=False, default=0)

# Initiera databasen (skapa tabellen om den inte finns)
@app.before_first_request
def init_db():
    db.create_all()
    # Om inga kandidater finns, lägg till dem
    if Vote.query.count() == 0:
        candidates = ['uffe', 'magda', 'jimmy', 'nooshi', 'annakarin', 'ebba', 'amandadaniel', 'romina']
        for candidate in candidates:
            vote = Vote(candidate=candidate, count=0)
            db.session.add(vote)
        db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/vote', methods=['POST'])
def vote():
    choice = request.form['candidate']
    vote = Vote.query.filter_by(candidate=choice).first()
    if vote:
        vote.count += 1
        db.session.commit()
    return redirect('/results')

@app.route('/results')
def results():
    votes = Vote.query.order_by(Vote.count.desc()).all()
    total_votes = sum(v.count for v in votes)
    results = []
    for i, v in enumerate(votes, start=1):
        procent = (v.count / total_votes * 100) if total_votes > 0 else 0
        results.append({
            "candidate": v.candidate,
            "count": v.count,
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
    app.run(debug=True, host='0.0.0.0', port=port)
