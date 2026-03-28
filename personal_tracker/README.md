# Personal Tracker

A mobile-first self-tracking app running on a Raspberry Pi. Logs time blocks by category, meals, exercise, mood, energy, weight, and sleep. Built for tracking personal productivity and habits during a job search / parenting period.

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
├── app.py           Flask app — all routes
├── schema.sql       Database schema
├── analysis.py      Analysis module for notebook use
├── INSTRUCTIONS.md  Day-to-day usage guide
├── README.md        This file
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

---

## Analysis (Laptop)

### Pull the database

```python
from personal_tracker.analysis import TrackerDB
db = TrackerDB()
db.sync()                    # pulls via local network
db.sync('100.93.132.118')   # pulls via Tailscale
```

Or manually:
```bash
scp simonhans@192.168.88.9:~/personal_tracker/personal.db ~/personal_tracker/personal.db
```

### DataFrames

```python
from personal_tracker.analysis import TrackerDB
db = TrackerDB()

sleep_df    = db.sleep()              # daily log with computed night sleep hours
blocks_df   = db.time_blocks()        # all time blocks with duration_min computed
food_df     = db.food()               # all meals/snacks/drinks
exercise_df = db.exercise()           # all exercise events
mood_df     = db.mood()               # all mood/energy logs
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
