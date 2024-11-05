from flask import Flask, render_template, redirect, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///votes.db'
db = SQLAlchemy(app)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    option = db.Column(db.String(50), nullable=False)
    count = db.Column(db.Integer, default=0)

with app.app_context():
    db.create_all()

# Liste der Personen
persons = ['Adrian', 'Anna', 'Annika', 'Bjarne', 'Connor', 'Eike', 'Elias', 'Finn', 'Jara', 'Johannes', 'Joseph', 'Lilith', 'Richard', 'Simon', 'Timo']

@app.route("/")
def start():
    return render_template("index.html", persons=persons)

@app.route("/vote", methods=["POST"])
def vote_handling():
    name = request.form["person"]
    vote = Vote.query.filter_by(option=name).first()
    if vote:
        vote.count += 1
    else:
        vote = Vote(option=name, count=1)
        db.session.add(vote)
    db.session.commit()
    return redirect("/results")

@app.route("/results", methods=["GET"])
def results():
    votes = Vote.query.order_by(Vote.count.desc()).all()
    total_votes = db.session.query(db.func.sum(Vote.count)).scalar() or 0
    return render_template("results.html", votes=votes, total_votes=total_votes)

@app.route("/reset_votes")
def reset_votes():
    db.session.query(Vote).delete()
    db.session.commit()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
