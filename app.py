from flask import Flask, render_template, redirect, request, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///votes.db'
db = SQLAlchemy(app)
app.secret_key = "gleezeborpglorpzyblopglorporbleflimb"

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
    if session:
        return render_template("index.html", persons=persons, li=session["logged_in"], voted=session["voted"])
    else:
        return redirect("/session_config")
    
@app.route("/session_config")
def config():
    session["logged_in"] = False
    session["voted"] = False

    return redirect("/")

@app.route("/session_clear")
def clear():
    session.clear()
    return redirect("/")

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

    session["voted"] = True
    session.modified = True

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

    session["voted"] = False
    session.modified = True

    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
