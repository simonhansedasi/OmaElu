from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime, timedelta
import os

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), 'personal.db')

CATEGORIES = [
    ('💼', 'Job Search'),
    ('🔗', 'LinkedIn'),
    ('💻', 'Coding / Portfolio'),
    ('📚', 'Learning'),
    ('🏃', 'Exercise'),
    ('🏠', 'Household'),
    ('🛒', 'Errands'),
    ('😴', 'Rest'),
    ('👥', 'Social'),
    ('🧘', 'Self Care'),
    ('✏️', 'Other'),
]

EXERCISE_TYPES = ['Walk', 'Run', 'Bike', 'Weights', 'Yoga', 'Swim', 'HIIT', 'Other']


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with open(os.path.join(os.path.dirname(__file__), 'schema.sql')) as f:
        with get_db() as conn:
            conn.executescript(f.read())


def migrate_db():
    with get_db() as db:
        try:
            db.execute("ALTER TABLE daily_log ADD COLUMN weight_lbs REAL")
        except Exception:
            pass
        try:
            db.execute("""CREATE TABLE IF NOT EXISTS substances (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                event_time TEXT NOT NULL,
                category   TEXT NOT NULL,
                type       TEXT NOT NULL,
                notes      TEXT
            )""")
        except Exception:
            pass
        try:
            db.execute("""CREATE TABLE IF NOT EXISTS naps (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                date         TEXT NOT NULL,
                start_time   TEXT NOT NULL,
                end_time     TEXT,
                duration_min REAL
            )""")
        except Exception:
            pass
        try:
            db.execute("""CREATE TABLE IF NOT EXISTS hydration_log (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                event_time TEXT NOT NULL,
                amount     REAL NOT NULL DEFAULT 1.0
            )""")
        except Exception:
            pass


def event_time(offset_min):
    t = datetime.now() - timedelta(minutes=int(offset_min or 0))
    return t.strftime('%Y-%m-%d %H:%M')


# --- Daily log ---

@app.route('/')
def index():
    db = get_db()
    today = datetime.now().strftime('%Y-%m-%d')
    open_nap = db.execute(
        "SELECT id, start_time FROM naps WHERE date = ? AND end_time IS NULL ORDER BY id DESC LIMIT 1",
        (today,)
    ).fetchone()
    open_block = db.execute(
        "SELECT id, category FROM time_blocks WHERE date = ? AND end_time IS NULL ORDER BY id DESC LIMIT 1",
        (today,)
    ).fetchone()
    daily = db.execute("SELECT wake_time, weight_lbs FROM daily_log WHERE date = ?", (today,)).fetchone()
    today_weight = daily['weight_lbs'] if daily and daily['weight_lbs'] else None

    # Hydration
    hydration_total = db.execute(
        "SELECT COALESCE(SUM(amount), 0) as total FROM hydration_log WHERE event_time LIKE ?", (today + '%',)
    ).fetchone()['total']

    # Rate check: expected bottles by now based on wake time
    hydration_on_track = None
    if daily and daily['wake_time']:
        from datetime import datetime as _dt
        wake_dt = _dt.strptime(f"{today} {daily['wake_time']}", '%Y-%m-%d %H:%M')
        hours_awake = max(0, (_dt.now() - wake_dt).total_seconds() / 3600)
        expected = hours_awake * ((HYDRATION_RATE_LOW + HYDRATION_RATE_HIGH) / 2)
        hydration_on_track = hydration_total >= expected * 0.75  # within 75% of midpoint rate

    return render_template('index.html', open_block=open_block, open_nap=open_nap,
                           categories=CATEGORIES,
                           today_weight=today_weight,
                           hydration_total=hydration_total,
                           hydration_on_track=hydration_on_track,
                           hydration_target=HYDRATION_TARGET,
                           hydration_max=HYDRATION_MAX)


@app.route('/wake', methods=['POST'])
def wake():
    t = event_time(request.form.get('offset_min', 0))
    sleep_quality = request.form.get('sleep_quality') or None
    with get_db() as db:
        db.execute(
            "INSERT INTO daily_log (date, wake_time, sleep_quality) VALUES (?, ?, ?) "
            "ON CONFLICT(date) DO UPDATE SET wake_time = ?, sleep_quality = ?",
            (t[:10], t[11:], sleep_quality, t[11:], sleep_quality)
        )
    return redirect(url_for('index'))


@app.route('/bed', methods=['POST'])
def bed():
    t = event_time(request.form.get('offset_min', 0))
    sleep_quality = request.form.get('sleep_quality') or None
    with get_db() as db:
        db.execute(
            "INSERT INTO daily_log (date, bed_time) VALUES (?, ?) "
            "ON CONFLICT(date) DO UPDATE SET bed_time = ?",
            (t[:10], t[11:], t[11:])
        )
    return redirect(url_for('index'))


@app.route('/weight', methods=['POST'])
def weight():
    date = datetime.now().strftime('%Y-%m-%d')
    lbs = request.form.get('weight_lbs', '').strip()
    if lbs:
        with get_db() as db:
            db.execute(
                "INSERT INTO daily_log (date, weight_lbs) VALUES (?, ?) "
                "ON CONFLICT(date) DO UPDATE SET weight_lbs = ?",
                (date, float(lbs), float(lbs))
            )
    return redirect(url_for('index'))


# --- Time blocks ---

@app.route('/block/start', methods=['POST'])
def block_start():
    t = event_time(request.form.get('offset_min', 0))
    category = request.form.get('category')
    description = request.form.get('description', '').strip() or None
    with get_db() as db:
        db.execute(
            "INSERT INTO time_blocks (date, start_time, category, description) VALUES (?, ?, ?, ?)",
            (t[:10], t[11:], category, description)
        )
    return redirect(url_for('index'))


@app.route('/block/end', methods=['POST'])
def block_end():
    t = event_time(request.form.get('offset_min', 0))
    today = t[:10]
    with get_db() as db:
        block = db.execute(
            "SELECT id FROM time_blocks WHERE date = ? AND end_time IS NULL ORDER BY id DESC LIMIT 1",
            (today,)
        ).fetchone()
        if block:
            db.execute("UPDATE time_blocks SET end_time = ? WHERE id = ?", (t[11:], block['id']))
    return redirect(url_for('index'))


# --- Meals ---

@app.route('/food', methods=['GET', 'POST'])
def food():
    db = get_db()
    if request.method == 'POST':
        t = event_time(request.form.get('offset_min', 0))
        meal_type = request.form.get('type')
        description = request.form.get('description', '').strip()
        other = request.form.get('other', '').strip()

        if other:
            description = other
            db.execute(
                "INSERT INTO meal_items (name, use_count) VALUES (?, 1) "
                "ON CONFLICT(name) DO UPDATE SET use_count = use_count + 1",
                (description,)
            )
            db.commit()
        elif description:
            db.execute(
                "UPDATE meal_items SET use_count = use_count + 1 WHERE name = ?",
                (description,)
            )
            db.commit()

        with db:
            db.execute(
                "INSERT INTO meals (event_time, type, description) VALUES (?, ?, ?)",
                (t, meal_type, description)
            )
        return redirect(url_for('index'))

    items = db.execute("SELECT name FROM meal_items ORDER BY use_count DESC").fetchall()
    return render_template('food.html', items=items)


# --- Exercise ---

@app.route('/exercise', methods=['GET', 'POST'])
def exercise():
    if request.method == 'POST':
        t = event_time(request.form.get('offset_min', 0))
        etype = request.form.get('type', '').strip()
        duration = request.form.get('duration_min', '').strip()
        intensity = request.form.get('intensity') or None
        duration = float(duration) if duration else None
        with get_db() as db:
            db.execute(
                "INSERT INTO exercise (event_time, type, duration_min, intensity) VALUES (?, ?, ?, ?)",
                (t, etype, duration, intensity)
            )
        return redirect(url_for('index'))
    return render_template('exercise.html', exercise_types=EXERCISE_TYPES)


# --- Naps ---

@app.route('/nap/start', methods=['POST'])
def nap_start():
    t = event_time(request.form.get('offset_min', 0))
    with get_db() as db:
        db.execute("INSERT INTO naps (date, start_time) VALUES (?, ?)", (t[:10], t[11:]))
    return redirect(url_for('index'))


@app.route('/nap/end', methods=['POST'])
def nap_end():
    t = event_time(request.form.get('offset_min', 0))
    today = t[:10]
    with get_db() as db:
        nap = db.execute(
            "SELECT id, start_time FROM naps WHERE date = ? AND end_time IS NULL ORDER BY id DESC LIMIT 1",
            (today,)
        ).fetchone()
        if nap:
            start = datetime.strptime(f"{today} {nap['start_time']}", '%Y-%m-%d %H:%M')
            end   = datetime.strptime(t, '%Y-%m-%d %H:%M')
            duration = max(0, int((end - start).total_seconds() / 60))
            db.execute("UPDATE naps SET end_time = ?, duration_min = ? WHERE id = ?",
                       (t[11:], duration, nap['id']))
    return redirect(url_for('index'))


# --- Hydration ---

HYDRATION_RATE_LOW  = 0.25  # bottles/hour
HYDRATION_RATE_HIGH = 0.50
HYDRATION_TARGET    = 5.5   # daily sweet-spot (midpoint of 5-6)
HYDRATION_MAX       = 7.0

@app.route('/hydration', methods=['POST'])
def hydration():
    amount = request.form.get('amount', '1.0').strip()
    try:
        amount = float(amount)
    except ValueError:
        amount = 1.0
    t = event_time(request.form.get('offset_min', 0))
    with get_db() as db:
        db.execute("INSERT INTO hydration_log (event_time, amount) VALUES (?, ?)", (t, amount))
    return redirect(url_for('index'))


# --- Substances ---

SUBSTANCE_TYPES = {
    'caffeine': ['Coffee', 'Espresso'],
    'cannabis': ['Flower', 'Vape', 'Edible'],
    'alcohol':  ['Beer', 'Wine', 'Spirits'],
}

@app.route('/substance', methods=['GET', 'POST'])
def substance():
    if request.method == 'POST':
        t        = event_time(request.form.get('offset_min', 0))
        category = request.form.get('category', '').strip()
        stype    = request.form.get('type', '').strip()
        notes    = request.form.get('notes', '').strip() or None
        with get_db() as db:
            db.execute(
                "INSERT INTO substances (event_time, category, type, notes) VALUES (?, ?, ?, ?)",
                (t, category, stype, notes)
            )
        return redirect(url_for('index'))
    return render_template('substance.html', substance_types=SUBSTANCE_TYPES)


# --- Mood / Energy ---

@app.route('/mood', methods=['POST'])
def mood():
    t = event_time(request.form.get('offset_min', 0))
    energy = request.form.get('energy')
    mood_val = request.form.get('mood')
    with get_db() as db:
        db.execute(
            "INSERT INTO mood_log (event_time, energy, mood) VALUES (?, ?, ?)",
            (t, energy, mood_val)
        )
    return redirect(url_for('index'))


# --- Edit / Delete ---

EDIT_CONFIG = {
    'block':     {'table': 'time_blocks', 'fields': ['date', 'start_time', 'end_time', 'category', 'description']},
    'food':      {'table': 'meals',       'fields': ['event_time', 'type', 'description']},
    'exercise':  {'table': 'exercise',    'fields': ['event_time', 'type', 'duration_min', 'intensity']},
    'mood':      {'table': 'mood_log',    'fields': ['event_time', 'energy', 'mood']},
    'substance': {'table': 'substances',  'fields': ['event_time', 'category', 'type', 'notes']},
    'nap':       {'table': 'naps',        'fields': ['date', 'start_time', 'end_time', 'duration_min']},
}

@app.route('/edit/<etype>/<eid>', methods=['GET', 'POST'])
def edit(etype, eid):
    if etype not in EDIT_CONFIG:
        return redirect(url_for('today'))
    cfg = EDIT_CONFIG[etype]
    db = get_db()
    if request.method == 'POST':
        updates = {f: request.form.get(f, '').strip() or None for f in cfg['fields']}
        set_clause = ', '.join(f"{f} = ?" for f in cfg['fields'])
        db.execute(f"UPDATE {cfg['table']} SET {set_clause} WHERE id = ?",
                   list(updates.values()) + [eid])
        db.commit()
        return redirect(url_for('today'))
    row = db.execute(f"SELECT * FROM {cfg['table']} WHERE id = ?", (eid,)).fetchone()
    if not row:
        return redirect(url_for('today'))
    return render_template('edit.html', etype=etype, eid=eid, row=dict(row), fields=cfg['fields'])


@app.route('/delete/<etype>/<eid>', methods=['POST'])
def delete(etype, eid):
    if etype not in EDIT_CONFIG:
        return redirect(url_for('today'))
    cfg = EDIT_CONFIG[etype]
    with get_db() as db:
        db.execute(f"DELETE FROM {cfg['table']} WHERE id = ?", (eid,))
    return redirect(url_for('today'))


# --- Today view ---

@app.route('/today')
def today():
    date = datetime.now().strftime('%Y-%m-%d')
    db = get_db()
    daily      = db.execute("SELECT * FROM daily_log WHERE date = ?", (date,)).fetchone()
    blocks     = db.execute("SELECT * FROM time_blocks WHERE date = ? ORDER BY start_time", (date,)).fetchall()
    naps       = db.execute("SELECT * FROM naps WHERE date = ? ORDER BY start_time", (date,)).fetchall()
    food       = db.execute("SELECT * FROM meals WHERE event_time LIKE ? ORDER BY event_time", (date+'%',)).fetchall()
    ex         = db.execute("SELECT * FROM exercise WHERE event_time LIKE ? ORDER BY event_time", (date+'%',)).fetchall()
    moods      = db.execute("SELECT * FROM mood_log WHERE event_time LIKE ? ORDER BY event_time", (date+'%',)).fetchall()
    substances = db.execute("SELECT * FROM substances WHERE event_time LIKE ? ORDER BY event_time", (date+'%',)).fetchall()

    # Compute block durations
    block_totals = {}
    for b in blocks:
        if b['end_time']:
            s = datetime.strptime(b['start_time'], '%H:%M')
            e = datetime.strptime(b['end_time'],   '%H:%M')
            mins = (e - s).seconds // 60
        else:
            mins = 0
        block_totals[b['category']] = block_totals.get(b['category'], 0) + mins

    return render_template('today.html', daily=daily, blocks=blocks, naps=naps, food=food,
                           exercise=ex, moods=moods, substances=substances,
                           block_totals=block_totals, date=date)


if __name__ == '__main__':
    init_db()
    migrate_db()
    app.run(host='0.0.0.0', port=5001, debug=False)
