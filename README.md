# 🔥 Burn Alert — Privacy-first Focus Analytics

A dark-themed burnout detection dashboard built with Python Flask, HTML/CSS, and Chart.js. Tracks app usage patterns, context switching, and deep work to calculate a real-time burnout score.

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the app
```bash
python app.py
```

### 3. Open in browser
```
http://127.0.0.1:5000
```

### 4. Register an account
Sign up with any email + password. Demo data (30 days) is auto-seeded so all charts are populated immediately.

---

## Project Structure

```
burnalert/
├── app.py                  ← Flask backend (routes, API, auth, DB)
├── requirements.txt        ← Just Flask — no other dependencies
├── burnalert.db            ← SQLite database (auto-created on first run)
├── templates/
│   ├── login.html          ← Login + Register page
│   ├── dashboard.html      ← Main dashboard
│   └── about.html          ← About / Privacy page
└── static/
    ├── css/
    │   └── style.css       ← Full dark theme styles
    └── js/
        └── dashboard.js    ← Arc gauge, Chart.js charts, live polling
```

---

## Features

| Feature | Details |
|---|---|
| Auth | Email + password login, SHA-256 hashed, per-user data |
| Arc Gauge | Canvas-drawn semicircle gauge, animates on load |
| Live Score | Auto-refreshes every 30 seconds |
| 7-Day Trend | Smooth amber area chart |
| 30-Day Overview | Score trend + Work Split tab (deep / switch / distract) |
| App Usage | Per-app progress bars with category color coding |
| Alerts Panel | Dropdown of high-score days |
| Report Export | Download 30-day data as CSV |
| About Page | Privacy policy + how it works |

---

## Burnout Score Logic

| Condition | Points |
|---|---|
| Screen time > 8 hrs | +30 |
| Break/idle time < 20 min | +30 |
| Active after 10 PM | +20 |

**Risk States:**
- 0–34 → Focused Flow (green)
- 35–54 → Mild Strain (amber)
- 55–74 → Moderate Fatigue (amber/orange)
- 75–100 → High Burnout Risk (red)

---

## Tech Stack

- **Backend:** Python 3, Flask
- **Database:** SQLite (built-in, zero config)
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Charts:** Chart.js 4.4
- **Gauge:** HTML5 Canvas (custom drawn)
