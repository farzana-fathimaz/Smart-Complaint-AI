"""
app.py
──────
Flask Sentiment Analysis App for Complaint Text.
Analyzes polarity, subjectivity, tone, and stores history.

Run:
    python app.py
Visit:
    http://127.0.0.1:5000
"""

from flask          import Flask, render_template, request, jsonify
from textblob       import TextBlob
from flask_sqlalchemy import SQLAlchemy
from datetime       import datetime
import os

# ── App setup ────────────────────────────────────────────
app = Flask(__name__)

# SQLite database stored in the same folder
app.config["SQLALCHEMY_DATABASE_URI"]        = "sqlite:///sentiment_history.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"]                     = "sentiment-secret-2024"

db = SQLAlchemy(app)


# ─────────────────────────────────────────────────────────
#  DATABASE MODEL
# ─────────────────────────────────────────────────────────

class SentimentRecord(db.Model):
    """Stores each analysis result in the database."""
    id          = db.Column(db.Integer, primary_key=True)
    text        = db.Column(db.Text, nullable=False)
    polarity    = db.Column(db.Float, nullable=False)
    subjectivity= db.Column(db.Float, nullable=False)
    label       = db.Column(db.String(20), nullable=False)   # Positive / Negative / Neutral
    tone        = db.Column(db.String(20), nullable=False)   # Angry / Neutral / Positive
    emoji       = db.Column(db.String(5),  nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id"          : self.id,
            "text"        : self.text,
            "polarity"    : round(self.polarity, 3),
            "subjectivity": round(self.subjectivity, 3),
            "label"       : self.label,
            "tone"        : self.tone,
            "emoji"       : self.emoji,
            "created_at"  : self.created_at.strftime("%d %b %Y, %I:%M %p"),
        }


# ─────────────────────────────────────────────────────────
#  SENTIMENT ANALYSIS LOGIC
# ─────────────────────────────────────────────────────────

def analyze_text(text: str) -> dict:
    """
    Analyzes complaint text using TextBlob.

    TextBlob polarity range: -1.0 (negative) to +1.0 (positive)
    TextBlob subjectivity:    0.0 (objective) to  1.0 (subjective)

    Returns a dict with all analysis results.
    """
    blob = TextBlob(text)

    polarity     = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity

    # ── Determine sentiment label ────────────────────────
    if polarity > 0.1:
        label = "Positive"
    elif polarity < -0.1:
        label = "Negative"
    else:
        label = "Neutral"

    # ── Determine complaint tone ─────────────────────────
    # Angry: very negative + highly subjective
    # Urgent: negative with urgent keywords
    angry_words = ["furious", "angry", "terrible", "horrible", "worst",
                   "disgusting", "outrageous", "useless", "pathetic", "unacceptable"]

    text_lower = text.lower()

    if polarity < -0.4 and subjectivity > 0.6:
        tone = "Angry"
    elif polarity < -0.4 and any(w in text_lower for w in angry_words):
        tone = "Angry"
    elif polarity < -0.1:
        tone = "Frustrated"
    elif polarity > 0.2:
        tone = "Positive"
    else:
        tone = "Neutral"

    # ── Assign emoji ─────────────────────────────────────
    emoji_map = {
        "Angry"     : "😡",
        "Frustrated": "😤",
        "Neutral"   : "😐",
        "Positive"  : "😊",
    }
    emoji = emoji_map.get(tone, "😐")

    return {
        "polarity"    : polarity,
        "subjectivity": subjectivity,
        "label"       : label,
        "tone"        : tone,
        "emoji"       : emoji,
    }


# ─────────────────────────────────────────────────────────
#  ROUTES
# ─────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Main page — shows the input form and analysis dashboard."""
    # Fetch last 10 records for history display
    history = SentimentRecord.query.order_by(
        SentimentRecord.created_at.desc()
    ).limit(10).all()

    return render_template("index.html", history=history)


@app.route("/analyze", methods=["POST"])
def analyze():
    """
    POST /analyze
    Accepts complaint text, analyzes it, saves to DB, returns JSON.
    """
    data = request.get_json()
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "No text provided"}), 400

    if len(text) < 5:
        return jsonify({"error": "Text too short to analyze"}), 400

    # Run analysis
    result = analyze_text(text)

    # Save to database
    record = SentimentRecord(
        text         = text,
        polarity     = result["polarity"],
        subjectivity = result["subjectivity"],
        label        = result["label"],
        tone         = result["tone"],
        emoji        = result["emoji"],
    )
    db.session.add(record)
    db.session.commit()

    # Include the saved record ID in response
    result["id"]         = record.id
    result["text"]       = text
    result["created_at"] = record.created_at.strftime("%d %b %Y, %I:%M %p")

    return jsonify(result)


@app.route("/history")
def history():
    """GET /history — returns all analysis records as JSON."""
    records = SentimentRecord.query.order_by(
        SentimentRecord.created_at.desc()
    ).all()
    return jsonify([r.to_dict() for r in records])


@app.route("/history/clear", methods=["POST"])
def clear_history():
    """POST /history/clear — deletes all records."""
    SentimentRecord.query.delete()
    db.session.commit()
    return jsonify({"message": "History cleared."})


@app.route("/stats")
def stats():
    """GET /stats — returns aggregate stats for the dashboard."""
    total    = SentimentRecord.query.count()
    positive = SentimentRecord.query.filter_by(label="Positive").count()
    negative = SentimentRecord.query.filter_by(label="Negative").count()
    neutral  = SentimentRecord.query.filter_by(label="Neutral").count()
    angry    = SentimentRecord.query.filter_by(tone="Angry").count()

    return jsonify({
        "total"   : total,
        "positive": positive,
        "negative": negative,
        "neutral" : neutral,
        "angry"   : angry,
    })


# ─────────────────────────────────────────────────────────
#  APP ENTRY
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    with app.app_context():
        db.create_all()   # Create DB tables if they don't exist
        print("✅ Database ready.")
    print("🚀 Sentiment Analysis App running at http://127.0.0.1:5000")
    app.run(debug=True, port=5000)