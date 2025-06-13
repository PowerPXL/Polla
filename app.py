from flask import Flask, render_template, request, redirect
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback-secret")  # Ha alltid en fallback under utveckling

DATABASE_URL = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Modell för votes
class Vote(db.Model):
    __tablename__ = 'votes'
    id = db.Column(db.Integer, primary_key=True)
    candidate = db.Column(db.String(100), unique=True, nullable=False)
    count = db.Column(db.Integer, nullable=False, default=0)

# Initiera databasen och populera kandidater (om inte finns)
def init_db():
    db.create_all()
    candidates = ['uffe', 'magda', 'jimmy', 'nooshi', 'annakarin', 'ebba', 'amandadaniel', 'romina']
    for candidate in candidates:
        if not Vote.query.filter_by(candidate=candidate).first():
            db.session.add(Vote(candidate=candidate, count=0))
    db.session.commit()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/vote', methods=['POST'])
def vote():
    choice = request.form['candidate']
    vote_entry = Vote.query.filter_by(candidate=choice).first()
    if vote_entry:
        vote_entry.count += 1
        db.session.commit()
    return redirect('/results')

@app.route('/results')
def results():
    votes = Vote.query.order_by(Vote.count.desc()).all()
    total_votes = sum(v.count for v in votes)
    results = []
    for i, vote in enumerate(votes, start=1):
        procent = (vote.count / total_votes * 100) if total_votes > 0 else 0
        results.append({
            "candidate": vote.candidate,
            "count": vote.count,
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
