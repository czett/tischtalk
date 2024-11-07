from flask import Flask, render_template, redirect, request, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random, os

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default_secret_key")  # Retrieve secret key from env

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Initialize global variables
last_run_date = None
current_question = None

# Models
class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    option = db.Column(db.String(50), nullable=False)
    count = db.Column(db.Integer, default=0)

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)

# Create tables in the database (if not already created)
with app.app_context():
    db.create_all()

# Helper functions
def get_last_run_date():
    setting = Setting.query.filter_by(key="LAST_UPDATE_DATE").first()
    return setting.value if setting else None

def set_last_run_date(date):
    setting = Setting.query.filter_by(key="LAST_UPDATE_DATE").first()
    if setting:
        setting.value = date
    else:
        setting = Setting(key="LAST_UPDATE_DATE", value=date)
        db.session.add(setting)
    db.session.commit()

def check_new_day():
    global last_run_date
    current_date = datetime.now().date()

    env_last_run_date = get_last_run_date()  # Get from DB
    
    if last_run_date is None:
        if env_last_run_date:
            last_run_date = datetime.strptime(env_last_run_date, "%Y-%m-%d").date()
        else:
            last_run_date = current_date  # Set initial value to today's date

    if current_date > last_run_date:
        last_run_date = current_date
        set_last_run_date(current_date)  # Save to DB
        return True
    return False

def persons() -> list:
    ps = os.getenv("FRIENDS")
    if ps:
        return [person for person in ps.split(",")]
    return []

def new_question():
    global current_question
    with open("static/questions.csv", "r") as file:
        questions = [q.strip() for q in file.read().split(";") if q.strip()]
        print("Geladene Fragen:", questions)
        if questions:
            current_question = random.choice(questions)
        else:
            current_question = "Keine Frage verfügbar."

# Routes
@app.route("/")
def start():
    global current_question
    if session:
        if check_new_day():
            new_question()
        if not current_question:
            current_question = "Keine Frage verfügbar."
        return render_template("index.html", persons=persons(), li=session.get("logged_in", False), voted=session.get("voted", False), q=current_question)
    else:
        return redirect("/session_config")

@app.route("/session_config")
def config():
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

# Run the app
if __name__ == "__main__":
    app.run(debug=True)
