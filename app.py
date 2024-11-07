from flask import Flask, render_template, redirect, request, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random, os
from dotenv import load_dotenv

load_dotenv()  # .env file

app = Flask(__name__)
app.secret_key = "gleezeborpglorpzyblopglorporbleflimb"

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

last_run_date = None
current_question = None

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    option = db.Column(db.String(50), nullable=False)
    count = db.Column(db.Integer, default=0)

with app.app_context():
    db.create_all()

def get_last_run_date():
    return os.getenv("LAST_UPDATE_DATE")

def set_last_run_date(date):
    with open(".env", "r") as f:
        lines = f.readlines()

    found = False
    for i in range(len(lines)):
        if lines[i].startswith("LAST_UPDATE_DATE="):
            lines[i] = f"LAST_UPDATE_DATE={date}\n"
            found = True
            break

    if not found:
        lines.append(f"LAST_UPDATE_DATE={date}\n")

    with open(".env", "w") as f:
        f.writelines(lines)

    load_dotenv()

def check_new_day():
    global last_run_date
    current_date = datetime.now().date()

    env_last_run_date = os.getenv("LAST_UPDATE_DATE")
    
    if last_run_date is None:
        if env_last_run_date:
            last_run_date = datetime.strptime(env_last_run_date, "%Y-%m-%d").date()
        else:
            last_run_date = current_date

    if current_date > last_run_date:
        last_run_date = current_date
        set_last_run_date(current_date)
        return True
    return False

def persons() -> list:
    ps = os.getenv("FRIENDS")
    return [person for person in ps.split(",")]
    
def new_question():
    global current_question
    with open("static/questions.csv", "r") as file:
        questions = [q.strip() for q in file.read().split(";") if q.strip()]
        print("Geladene Fragen:", questions)
        if questions:
            current_question = random.choice(questions)
        else:
            current_question = "Keine Frage verfügbar."

@app.route("/")
def start():
    global current_question
    if session:
        if check_new_day():
            new_question()
        if not current_question:
            current_question = "Keine Frage verfügbar."
        return render_template("index.html", persons=persons(), li=session["logged_in"], voted=session["voted"], q=current_question)
    else:
        return redirect("/session_config")

    
@app.route("/session_config")
def config():
    # more to come, just creating foundations
    session["logged_in"] = False
    session["name"] = ""
    session["profile_id"] = ""
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
