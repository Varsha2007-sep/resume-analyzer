"""AI Resume Analyzer - Flask application."""
import json
import os
import sqlite3
from datetime import datetime

from flask import (Flask, Response, abort, g, jsonify, redirect, render_template, request,
                   send_from_directory, url_for)

from analyzer import WEIGHTS, analyze
from extractor import MAX_BYTES, ExtractionError, extract_text

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("RESUME_DB", os.path.join(BASE, "analyses.db"))

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_BYTES + 512 * 1024


# ------------------------------------------------------------------ database
def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    conn = g.pop("db", None)
    if conn:
        conn.close()


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT, resume_name TEXT NOT NULL, job_title TEXT NOT NULL,
            ats_score INTEGER NOT NULL, created_at TEXT NOT NULL, job_description TEXT NOT NULL,
            result_json TEXT NOT NULL)""")


@app.template_filter("pretty_date")
def pretty_date(value):
    return datetime.fromisoformat(value).strftime("%d %b %Y")


def score_label(score):
    if score >= 80:
        return "Excellent match", "good"
    if score >= 60:
        return "Good match", "ok"
    if score >= 40:
        return "Fair match", "warn"
    return "Needs work", "bad"


def load_analysis(aid):
    row = db().execute("SELECT * FROM analyses WHERE id = ?", (aid,)).fetchone()
    if not row:
        abort(404)
    return row, json.loads(row["result_json"])


# ------------------------------------------------------------------ pages
@app.route("/")
def home():
    return render_template("index.html", page="home")


@app.route("/analyze")
def analyzer_page():
    return render_template("analyze.html", page="analyze")


@app.route("/about")
def about():
    return render_template("about.html", page="about", weights=WEIGHTS)


@app.route("/history")
def history():
    rows = db().execute("SELECT id, resume_name, job_title, ats_score, created_at FROM analyses "
                        "ORDER BY id DESC LIMIT 100").fetchall()
    return render_template("history.html", page="history", rows=rows, score_label=score_label)


@app.route("/results/<int:aid>")
def results(aid):
    row, r = load_analysis(aid)
    label, tone = score_label(r["overall"])
    return render_template("results.html", page="analyze", r=r, row=row, label=label, tone=tone, weights=WEIGHTS)


@app.route("/report/<int:aid>")
def report(aid):
    row, r = load_analysis(aid)
    label, _ = score_label(r["overall"])
    html = render_template("report.html", r=r, row=row, label=label, weights=WEIGHTS)
    fname = f"resume-analysis-report-{aid}.html"
    return Response(html, mimetype="text/html", headers={"Content-Disposition": f'attachment; filename="{fname}"'})


@app.route("/samples/<path:name>")
def samples(name):
    return send_from_directory(os.path.join(BASE, "sample"), name, as_attachment=True)


@app.route("/api/sample-jd")
def sample_jd():
    with open(os.path.join(BASE, "sample", "sample_job_description.txt"), encoding="utf-8") as f:
        return jsonify(text=f.read())


# ------------------------------------------------------------------ API
@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    file = request.files.get("resume")
    jd = (request.form.get("job_description") or "").strip()
    title = (request.form.get("job_title") or "").strip()
    if not file or not file.filename:
        return jsonify(error="Please upload your resume (PDF or DOCX)."), 400
    if len(jd.split()) < 20:
        return jsonify(error="Please paste a job description (at least 20 words)."), 400
    try:
        text = extract_text(file.filename, file.read())
    except ExtractionError as exc:
        return jsonify(error=str(exc)), 400
    result = analyze(text, jd, resume_name=os.path.basename(file.filename), job_title=title)
    cur = db().execute(
        "INSERT INTO analyses (resume_name, job_title, ats_score, created_at, job_description, result_json) "
        "VALUES (?,?,?,?,?,?)",
        (result["resume_name"], result["job_title"], result["overall"], datetime.now().isoformat(timespec="seconds"),
         jd, json.dumps(result)))
    db().commit()
    return jsonify(id=cur.lastrowid, url=url_for("results", aid=cur.lastrowid))


@app.route("/api/history/<int:aid>", methods=["DELETE"])
def delete_analysis(aid):
    db().execute("DELETE FROM analyses WHERE id = ?", (aid,))
    db().commit()
    return jsonify(ok=True)


@app.errorhandler(413)
def too_large(_e):
    return jsonify(error="File is larger than 5 MB."), 413


@app.errorhandler(404)
def not_found(_e):
    return render_template("404.html", page=""), 404


init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
