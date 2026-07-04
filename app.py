from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
import sqlite3, hashlib, os, random, io
from datetime import datetime, timedelta, date

app = Flask(__name__)
app.secret_key = "burnalert_secret_2024"
DB = "burnalert.db"

# ── DB helpers ────────────────────────────────────────────────────────────────
def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    c = db()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS app_usage(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        app_name TEXT,
        category TEXT,
        date TEXT,
        duration_minutes REAL
    );
    CREATE TABLE IF NOT EXISTS burnout_scores(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        date TEXT,
        score INTEGER,
        context_switches INTEGER,
        deep_work_minutes REAL,
        screen_hours REAL
    );
    """)
    c.commit(); c.close()

def hp(p): return hashlib.sha256(p.encode()).hexdigest()

# ── Seed demo data ────────────────────────────────────────────────────────────
def seed(uid):
    c = db()
    if c.execute("SELECT COUNT(*) FROM burnout_scores WHERE user_id=?", (uid,)).fetchone()[0] > 0:
        c.close(); return
    APPS = [
        ("VS Code","deep"),("Terminal","deep"),("Chrome","switch"),
        ("Slack","switch"),("YouTube","distract"),("Notion","deep"),
        ("Gmail","switch"),("Spotify","distract"),("Zoom","switch"),("Calendar","switch")
    ]
    today = date.today()
    scores = [28,35,42,58,71,65,52,44,38,46,55,63,49,37,43,50,68,72,60,48,41,36,53,57,44,49,62,55,43,37]
    for i in range(30):
        d = (today - timedelta(days=29-i)).isoformat()
        sc = scores[i] if i < len(scores) else random.randint(25,70)
        sw = random.randint(8, 35)
        dw = random.uniform(0.5, 3.5) if sc < 60 else random.uniform(0.2, 1.2)
        sh = random.uniform(5, 11)
        c.execute("INSERT INTO burnout_scores(user_id,date,score,context_switches,deep_work_minutes,screen_hours) VALUES(?,?,?,?,?,?)",
                  (uid, d, sc, sw, round(dw*60,1), round(sh,1)))
        for app_name, cat in APPS:
            base = {"deep":90,"switch":45,"distract":60}[cat]
            dur = max(5, base + random.randint(-30,30))
            if sc > 60 and cat == "distract": dur += random.randint(20,60)
            if sc < 40 and cat == "deep": dur += random.randint(30,60)
            c.execute("INSERT INTO app_usage(user_id,app_name,category,date,duration_minutes) VALUES(?,?,?,?,?)",
                      (uid, app_name, cat, d, round(dur,1)))
    c.commit(); c.close()

# ── Auth routes ───────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return redirect("/dashboard" if "uid" in session else "/login")

@app.route("/login", methods=["GET","POST"])
def login():
    err = None
    if request.method == "POST":
        c = db()
        u = c.execute("SELECT * FROM users WHERE email=? AND password=?",
                      (request.form["email"].strip(), hp(request.form["password"]))).fetchone()
        c.close()
        if u:
            session["uid"] = u["id"]; session["email"] = u["email"]
            seed(u["id"]); return redirect("/dashboard")
        err = "Invalid email or password."
    return render_template("login.html", err=err)

@app.route("/register", methods=["GET","POST"])
def register():
    err = None
    if request.method == "POST":
        try:
            c = db()
            c.execute("INSERT INTO users(email,password) VALUES(?,?)",
                      (request.form["email"].strip(), hp(request.form["password"])))
            c.commit()
            u = c.execute("SELECT * FROM users WHERE email=?", (request.form["email"].strip(),)).fetchone()
            c.close()
            session["uid"] = u["id"]; session["email"] = u["email"]
            seed(u["id"]); return redirect("/dashboard")
        except: err = "Email already registered."
    return render_template("login.html", err=err, reg=True)


@app.route("/logout")
def logout():
    session.clear(); return redirect("/login")

# ── Page routes ───────────────────────────────────────────────────────────────
@app.route("/dashboard")
def dashboard():
    if "uid" not in session: return redirect("/login")
    return render_template("dashboard.html", email=session["email"])

@app.route("/about")
def about():
    if "uid" not in session: return redirect("/login")
    return render_template("about.html")

# ── API: live score ───────────────────────────────────────────────────────────
@app.route("/api/live")
def api_live():
    if "uid" not in session: return jsonify({}), 401
    uid = session["uid"]
    c = db()
    today = date.today().isoformat()
    row = c.execute("SELECT * FROM burnout_scores WHERE user_id=? AND date=? LIMIT 1", (uid, today)).fetchone()
    if not row:
        hour = datetime.now().hour
        base = 30 + (hour - 8) * 3 if hour >= 8 else 20
        score = max(10, min(95, base + random.randint(-8, 8)))
        sw = random.randint(5, 20); dw = random.uniform(20, 120)
        sh = round((hour - 8) * 0.9, 1) if hour >= 8 else 0
        c.execute("INSERT INTO burnout_scores(user_id,date,score,context_switches,deep_work_minutes,screen_hours) VALUES(?,?,?,?,?,?)",
                  (uid, today, score, sw, round(dw,1), sh))
        c.commit()
        row = c.execute("SELECT * FROM burnout_scores WHERE user_id=? AND date=?", (uid, today)).fetchone()
    score = row["score"]
    state = ("Focused Flow" if score < 35 else
             "Mild Strain" if score < 55 else
             "Moderate Fatigue" if score < 75 else "High Burnout Risk")
    color = "#22c55e" if score < 35 else ("#f59e0b" if score < 65 else "#ef4444")
    c.close()
    return jsonify(score=score, state=state, color=color,
                   context_switches=row["context_switches"],
                   deep_work=round(row["deep_work_minutes"]/60, 1),
                   screen_hours=row["screen_hours"])

# ── API: 7-day trend ──────────────────────────────────────────────────────────
@app.route("/api/trend7")
def api_trend7():
    if "uid" not in session: return jsonify({}), 401
    c = db()
    rows = c.execute("SELECT date, score FROM burnout_scores WHERE user_id=? ORDER BY date DESC LIMIT 7",
                     (session["uid"],)).fetchall()
    c.close()
    rows = list(reversed(rows))
    labels = [datetime.strptime(r["date"],"%Y-%m-%d").strftime("%a") for r in rows]
    scores = [r["score"] for r in rows]
    avg = round(sum(scores)/len(scores)) if scores else 0
    return jsonify(labels=labels, scores=scores, avg=avg)

# ── API: 30-day overview ──────────────────────────────────────────────────────
@app.route("/api/overview30")
def api_overview30():
    if "uid" not in session: return jsonify({}), 401
    c = db()
    rows = c.execute("SELECT date, score FROM burnout_scores WHERE user_id=? ORDER BY date DESC LIMIT 30",
                     (session["uid"],)).fetchall()
    c.close()
    rows = list(reversed(rows))
    scores = [r["score"] for r in rows]
    month_avg = round(sum(scores)/len(scores)) if scores else 0
    week_scores = scores[-7:] if len(scores) >= 7 else scores
    week_avg = round(sum(week_scores)/len(week_scores)) if week_scores else 0
    trend = ("Rising" if len(scores) >= 9 and scores[-1] > scores[-8] else
             "Falling" if len(scores) >= 9 and scores[-1] < scores[-8] else "Stable")
    labels = [datetime.strptime(r["date"],"%Y-%m-%d").strftime("%d %b") for r in rows]
    return jsonify(labels=labels, scores=scores, month_avg=month_avg, week_avg=week_avg, trend=trend)

# ── API: work split ───────────────────────────────────────────────────────────
@app.route("/api/worksplit")
def api_worksplit():
    if "uid" not in session: return jsonify({}), 401
    c = db()
    rows = c.execute("""SELECT category, SUM(duration_minutes) as total
                        FROM app_usage WHERE user_id=? AND date >= date('now','-30 days')
                        GROUP BY category""", (session["uid"],)).fetchall()
    c.close()
    data = {r["category"]: round(r["total"]/60, 1) for r in rows}
    return jsonify(deep=data.get("deep",0), switch=data.get("switch",0), distract=data.get("distract",0))

# ── API: app usage ────────────────────────────────────────────────────────────
@app.route("/api/apps")
def api_apps():
    if "uid" not in session: return jsonify({}), 401
    c = db()
    today = date.today().isoformat()
    rows = c.execute("""SELECT app_name, category, SUM(duration_minutes) as total
                        FROM app_usage WHERE user_id=? AND date=?
                        GROUP BY app_name ORDER BY total DESC LIMIT 10""",
                     (session["uid"], today)).fetchall()
    if not rows:
        rows = c.execute("""SELECT app_name, category, AVG(duration_minutes) as total
                            FROM app_usage WHERE user_id=?
                            GROUP BY app_name ORDER BY total DESC LIMIT 10""",
                         (session["uid"],)).fetchall()
    c.close()
    max_t = max((r["total"] for r in rows), default=1)
    result = []
    for r in rows:
        hrs = round(r["total"]/60, 1)
        col = "#22c55e" if r["category"]=="deep" else ("#f59e0b" if r["category"]=="switch" else "#6b7280")
        result.append({"app": r["app_name"], "hours": hrs,
                        "pct": round(r["total"]/max_t*100), "color": col, "cat": r["category"]})
    deep_h = round(sum(x["hours"] for x in result if x["cat"]=="deep"),1)
    sw_h   = round(sum(x["hours"] for x in result if x["cat"]=="switch"),1)
    return jsonify(apps=result, deep_hours=deep_h, switch_hours=sw_h)

# ── API: alerts ───────────────────────────────────────────────────────────────
@app.route("/api/alerts")
def api_alerts():
    if "uid" not in session: return jsonify({}), 401
    c = db()
    rows = c.execute("""SELECT date, score FROM burnout_scores WHERE user_id=? AND score >= 60
                        ORDER BY date DESC LIMIT 10""", (session["uid"],)).fetchall()
    c.close()
    alerts = [{"date": r["date"], "score": r["score"],
               "msg": "High burnout risk detected" if r["score"] >= 75 else "Moderate fatigue level"}
              for r in rows]
    return jsonify(alerts=alerts)

# ── API: PDF report ───────────────────────────────────────────────────────────
@app.route("/api/report/pdf")
def api_report_pdf():
    from generate_report import generate_pdf
    import io

    data = {
        "generated": "Today",
        "score": 45,
        "summary": [
            ("Focus Time", "2h"),
            ("Context Switches", "10"),
            ("Screen Hours", "6h"),
        ],
        "trend7": [("Mon",30),("Tue",40),("Wed",50),("Thu",60),("Fri",70),("Sat",35),("Sun",25)],
        "apps": [("VS Code",2.5,"Deep Work"),("YouTube",3,"Context Switch")]
    }

    pdf_bytes = generate_pdf(data)

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name="test-report.pdf"
    )
# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    print("\n✅  Burn Alert running → http://127.0.0.1:5000\n")
    app.run(debug=True)
