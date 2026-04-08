# Personal Tracker

A mobile-first self-tracking app running on a Raspberry Pi. Logs time blocks by category, meals, exercise, mood, energy, weight, sleep, hydration, and naps. Built for tracking personal productivity and habits during a job search / parenting period.

> **Repo note:** Previously lived in `dada_science/personal_tracker/`. Moved to `OmaElu/personal_tracker/` in March 2026.

---

## Network Access

| Context | URL |
|---------|-----|
| At home | `http://192.168.88.9:5001` |
| Away (Tailscale) | `http://100.93.132.118:5001` |
| SSH at home | `ssh simonhans@192.168.88.9` |
| SSH away | `ssh simonhans@100.93.132.118` |

Runs as a systemd service on the same Pi as the dada tracker.

---

## Service Management

```bash
sudo systemctl status personal-tracker
sudo systemctl restart personal-tracker
sudo journalctl -u personal-tracker -f
```

---

## File Structure

```
personal_tracker/
├── app.py                Flask app — all routes
├── schema.sql            Database schema
├── analysis.py           Analysis module for notebook use
├── remind_personal.py    Cron reminder script (runs every 15 min on Pi)
├── INSTRUCTIONS.md       Day-to-day usage guide
├── README.md             This file
├── templates/
│   ├── base.html
│   ├── index.html     Home screen
│   ├── food.html      Meal/snack/drink logging
│   ├── exercise.html  Exercise logging
│   ├── today.html     Today's log view
│   └── edit.html      Edit/delete entries
└── static/
    └── style.css
```

`personal.db` lives on the Pi only — not committed to git.

---

## Database Schema

### `daily_log`
| Column | Type | Notes |
|--------|------|-------|
| date | TEXT (PK) | YYYY-MM-DD |
| wake_time | TEXT | HH:MM |
| bed_time | TEXT | HH:MM |
| sleep_quality | INTEGER | 1–5 |
| weight_lbs | REAL | optional daily weigh-in |

### `time_blocks`
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER (PK) | |
| date | TEXT | YYYY-MM-DD |
| start_time | TEXT | HH:MM |
| end_time | TEXT | HH:MM — null while running |
| category | TEXT | see categories below |
| description | TEXT | optional free text |

Categories: `💼 Job Search` · `🔗 LinkedIn` · `💻 Coding / Portfolio` · `📚 Learning` · `🏃 Exercise` · `🏠 Household` · `🛒 Errands` · `😴 Rest` · `👥 Social` · `🧘 Self Care` · `✏️ Other`

### `meals`
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER (PK) | |
| event_time | TEXT | YYYY-MM-DD HH:MM |
| type | TEXT | `meal`, `snack`, or `drink` |
| description | TEXT | |

### `meal_items`
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER (PK) | |
| name | TEXT (UNIQUE) | |
| use_count | INTEGER | drives sort order in quick-select |

### `exercise`
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER (PK) | |
| event_time | TEXT | YYYY-MM-DD HH:MM |
| type | TEXT | Walk / Run / Bike / Weights / Yoga / Swim / HIIT / Other |
| duration_min | REAL | optional |
| intensity | INTEGER | 1–5 |

### `mood_log`
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER (PK) | |
| event_time | TEXT | YYYY-MM-DD HH:MM |
| energy | INTEGER | 1–5 |
| mood | INTEGER | 1–5 |

### `hydration_log`
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER (PK) | |
| event_time | TEXT | YYYY-MM-DD HH:MM |
| amount | REAL | Bottles (1.0 = full ~20 oz, 0.5 = half, 0.25 = quarter) |

Target: 0.25–0.5 bottles/hour, 5–6 bottles/day (~100–120 oz). Logged via Full / ½ / ¼ buttons on home screen.

### `naps`
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER (PK) | |
| date | TEXT | YYYY-MM-DD |
| start_time | TEXT | HH:MM |
| end_time | TEXT | HH:MM — null while running |
| duration_min | REAL | computed on stop |

---

## Analysis (Laptop)

### Pull the database

```python
from OmaElu.personal_tracker.analysis import TrackerDB
db = TrackerDB()
db.sync()                    # pulls via local network
db.sync('100.93.132.118')   # pulls via Tailscale
```

Or manually:
```bash
scp simonhans@192.168.88.9:~/personal_tracker/personal.db ~/coding/OmaElu/personal_tracker/personal.db
```

### DataFrames

```python
from OmaElu.personal_tracker.analysis import TrackerDB
db = TrackerDB()

sleep_df      = db.sleep()              # daily log with computed night sleep hours
blocks_df     = db.time_blocks()        # all time blocks with duration_min computed
food_df       = db.food()               # all meals/snacks/drinks
exercise_df   = db.exercise()           # all exercise events
mood_df       = db.mood()               # all mood/energy logs
hydration_df  = db.hydration()          # all hydration events with daily totals
naps_df       = db.naps()               # all personal nap records
```

### Summaries and Aggregates

```python
db.daily_summary()               # today
db.daily_summary('2026-03-25')   # specific date

db.time_use_by_day()             # daily totals per category (good for stacked bar)
db.time_use_totals()             # overall totals per category across all days
db.productive_hours_per_day()    # hours on job-search categories per day
```

Productive categories: Job Search, LinkedIn, Coding / Portfolio, Learning.

---

## Timezone Changes

The Pi uses the system timezone for all `datetime.now()` calls. If you travel and the Pi is on the wrong timezone, fix it and backfill today's data.

### 1. Change the Pi's timezone

SSH in (or use Claude Code if connected) and run **without sudo**:

```bash
timedatectl set-timezone America/Los_Angeles   # PNW / Seattle
timedatectl set-timezone Pacific/Honolulu      # Hawaii
```

Note: `sudo timedatectl` requires a TTY and will fail over a non-interactive SSH session. Drop the `sudo` — it works without it on this Pi.

### 2. Backfill today's records

Run this on the Pi (via SSH or Claude Code), replacing `+3 hours` / `-3 hours` with the actual offset:

```python
import sqlite3
from datetime import datetime, timedelta

DB = '/home/simonhans/personal_tracker/personal.db'
today = '2026-04-06'   # change to target date
OFFSET = timedelta(hours=3)   # +3 to go HI→PNW; use -3 to go PNW→HI

def shift_hhmm(t):
    if not t: return t
    return (datetime.strptime(t, '%H:%M') + OFFSET).strftime('%H:%M')

def shift_dt(t):
    if not t: return t
    return (datetime.strptime(t, '%Y-%m-%d %H:%M') + OFFSET).strftime('%Y-%m-%d %H:%M')

db = sqlite3.connect(DB)

row = db.execute("SELECT wake_time, bed_time FROM daily_log WHERE date=?", (today,)).fetchone()
if row:
    db.execute("UPDATE daily_log SET wake_time=?, bed_time=? WHERE date=?",
               (shift_hhmm(row[0]), shift_hhmm(row[1]), today))

for r in db.execute("SELECT id, start_time, end_time FROM time_blocks WHERE date=?", (today,)).fetchall():
    db.execute("UPDATE time_blocks SET start_time=?, end_time=? WHERE id=?",
               (shift_hhmm(r[1]), shift_hhmm(r[2]), r[0]))

for table in ('meals', 'exercise', 'mood_log', 'substances', 'hydration_log'):
    for r in db.execute(f"SELECT id, event_time FROM {table} WHERE event_time LIKE ?", (today+'%',)).fetchall():
        db.execute(f"UPDATE {table} SET event_time=? WHERE id=?", (shift_dt(r[1]), r[0]))

for r in db.execute("SELECT id, start_time, end_time FROM naps WHERE date=?", (today,)).fetchall():
    ns, ne = shift_hhmm(r[1]), shift_hhmm(r[2])
    dur = max(0, int((datetime.strptime(ne, '%H:%M') - datetime.strptime(ns, '%H:%M')).total_seconds() / 60)) if r[2] else None
    db.execute("UPDATE naps SET start_time=?, end_time=?, duration_min=? WHERE id=?", (ns, ne, dur, r[0]))

db.commit()
print('Done')
```

### Architecture note

`remind_personal.py` hardcodes `DB_PATH = '/home/simonhans/personal_tracker/personal.db'`. The database lives **only on the Pi** at that path — not in this repo. The `personal.db` file in `OmaElu/personal_tracker/` is a local pull used for analysis only.

---

## Resetting Data

Clears all entries but keeps the schema:

```bash
cd ~/personal_tracker && venv/bin/python -c "
import sqlite3
conn = sqlite3.connect('personal.db')
conn.executescript('''
DELETE FROM time_blocks;
DELETE FROM meals;
DELETE FROM meal_items;
DELETE FROM exercise;
DELETE FROM mood_log;
DELETE FROM daily_log;
''')
conn.commit()
conn.close()
print('Done')
"
```
