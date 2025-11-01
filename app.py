from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///metrics.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class UsageMetric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.String(100), unique=True, nullable=False)
    first_seen = db.Column(db.String(100))
    error_count = db.Column(db.Integer, default=0)

@app.cli.command("init-db")
def init_db():
    """Initialize the database."""
    db.create_all()
    print("✅ Database initialized successfully.")

@app.route("/")
def home():
    return "<h2>TaxWazobia Flask + SQLite setup successful ✅</h2>"

if __name__ == "__main__":
    app.run(debug=True)
