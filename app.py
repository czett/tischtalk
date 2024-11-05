from flask import Flask, render_template, redirect, request, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///votes.db'
db = SQLAlchemy(app)
app.secret_key = "gleezeborpglorpzyblopglorporbleflimb"

last_run_date = None
current_question = None

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    option = db.Column(db.String(50), nullable=False)
    count = db.Column(db.Integer, default=0)

with app.app_context():
    db.create_all()

def check_new_day():
    global last_run_date
    current_date = datetime.now().date()
    
    if last_run_date is None or current_date > last_run_date:
        last_run_date = current_date
        return True
    return False

def persons() -> list:
    with open("static/persons.csv", "r") as file:
        return [person for person in file.readline().split(",")]
    
def new_question():
    global current_question
    with open("static/questions.csv", "r") as file:
        questions = [q for q in file.readline().split(";")]
        current_question = random.choice(questions)

@app.route("/")
def start():
    if session:
        if check_new_day():
            new_question()
        return render_template("index.html", persons=persons(), li=session["logged_in"], voted=session["voted"], q=current_question)
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
    return render_template("results.html", votes=votes, total_votes=total_votes, q=current_question)

@app.route("/reset")
def reset_votes():
    global last_run_date
    global current_question
    
    last_run_date = None
    current_question = None

    db.session.query(Vote).delete()
    db.session.commit()

    session["voted"] = False
    session.modified = True

    return redirect("/")

# @app.errorhandler(Exception)
# def handle_error(error):
#     # Error handling will be done, however procrastinated :3
#     return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
