#!/usr/bin/env python3
"""
Personal tracker reminder script — runs every 15 min via cron.
Sends push notifications to ntfy topic: remember_dummy
"""
import sqlite3, json, os, subprocess
from datetime import datetime, timedelta

DB_PATH    = '/home/simonhans/personal_tracker/personal.db'
STATE_PATH = '/home/simonhans/personal_tracker/remind_personal_state.json'
TOPIC      = 'remember_dummy'
BASE_URL   = 'http://100.93.132.118:5001'

TARGET_SLEEP_H = 7


def notify(title, body, url=None):
    args = ['curl', '-s',
            '-H', f'Title: {title}',
            '-d', body]
    if url:
        args += ['-H', f'Click: {url}']
    args.append(f'https://ntfy.sh/{TOPIC}')
    subprocess.run(args, capture_output=True)


def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH) as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_PATH, 'w') as f:
        json.dump(state, f)


def key(name):
    return f"{name}_{datetime.now().strftime('%Y-%m-%d')}"


def sent_recently(state, name, cooldown_min):
    k = key(name)
    if k not in state:
        return False
    last = datetime.fromisoformat(state[k])
    return (datetime.now() - last).total_seconds() / 60 < cooldown_min


def mark(state, name):
    state[key(name)] = datetime.now().isoformat()


def parse_dt(today, hhmm):
    return datetime.strptime(f"{today} {hhmm.replace('T', ' ')[:16]}", '%Y-%m-%d %H:%M')


def parse_event(event_time_str):
    return datetime.strptime(event_time_str.replace('T', ' ')[:16], '%Y-%m-%d %H:%M')


def main():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    today = datetime.now().strftime('%Y-%m-%d')
    now   = datetime.now()
    state = load_state()

    daily = db.execute("SELECT wake_time, weight_lbs FROM daily_log WHERE date = ?", (today,)).fetchone()
    wake_logged = daily and daily['wake_time']

    # --- 8am wake check ---
    if now.hour == 8 and now.minute < 15 and not wake_logged:
        if not sent_recently(state, 'wake_check', 60):
            notify('🌅 Morning!', "Log your wake time", f'{BASE_URL}/wake')
            mark(state, 'wake_check')

    if not wake_logged:
        save_state(state)
        return

    wake_dt = parse_dt(today, daily['wake_time'])

    # --- Weight — once after wake, skip if already logged ---
    if not (daily and daily['weight_lbs']) and not sent_recently(state, 'weight', 480):
        notify('⚖️ Weight check', 'Log your weight', f'{BASE_URL}/weight')
        mark(state, 'weight')

    # --- Mood/energy — every 3h, skip if logged in last 2h ---
    last_mood = db.execute(
        "SELECT event_time FROM mood_log WHERE event_time LIKE ? ORDER BY event_time DESC LIMIT 1",
        (today + '%',)
    ).fetchone()
    ref = parse_event(last_mood['event_time']) if last_mood else wake_dt
    if (now - ref).total_seconds() / 60 >= 180 and not sent_recently(state, 'mood', 120):
        notify('😊 Mood check', 'How are you feeling?', f'{BASE_URL}/mood')
        mark(state, 'mood')

    # --- Hydration — if no log in last 2h ---
    last_hydration = db.execute(
        "SELECT event_time FROM hydration_log WHERE event_time LIKE ? ORDER BY event_time DESC LIMIT 1",
        (today + '%',)
    ).fetchone()
    ref = parse_event(last_hydration['event_time']) if last_hydration else wake_dt
    if (now - ref).total_seconds() / 60 >= 120 and not sent_recently(state, 'hydration', 120):
        total = db.execute(
            "SELECT COALESCE(SUM(amount), 0) as t FROM hydration_log WHERE event_time LIKE ?",
            (today + '%',)
        ).fetchone()['t']
        notify('💧 Hydration', f'Log your water — {total:.1f} bottles so far today', f'{BASE_URL}/')
        mark(state, 'hydration')

    # --- Bedtime recommendation — wake_time + 17h (targeting 7h sleep) ---
    # 17h awake + 7h sleep = 24h. Fire reminder 30min before.
    bedtime_dt = wake_dt + timedelta(hours=17)
    remind_dt  = bedtime_dt - timedelta(minutes=30)
    if now >= remind_dt and not sent_recently(state, 'bedtime', 60):
        notify('🌙 Bedtime soon', f'Target bedtime {bedtime_dt.strftime("%H:%M")} for 7h sleep', f'{BASE_URL}/bed')
        mark(state, 'bedtime')

    save_state(state)


if __name__ == '__main__':
    main()


