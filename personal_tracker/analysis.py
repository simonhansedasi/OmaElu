"""
Simon Tracker — Analysis Module
=================================
Usage:
    from personal_tracker.analysis import TrackerDB
    db = TrackerDB()
    db.sync()           # pull from Pi (local)
    db.sync('100.93.132.118')  # Tailscale
"""

import sqlite3
import pandas as pd
import os
import subprocess
from datetime import datetime, timedelta

_SEARCH_PATHS = [
    os.path.expanduser('~/personal_tracker/personal.db'),
    os.path.join(os.path.dirname(__file__), 'personal.db'),
]

PRODUCTIVE_CATEGORIES = ['💼 Job Search', '🔗 LinkedIn', '💻 Coding / Portfolio', '📚 Learning']


class TrackerDB:
    def __init__(self, path=None):
        if path:
            self.path = path
        else:
            self.path = next((p for p in _SEARCH_PATHS if os.path.exists(p)), None)
        if self.path:
            print(f"Connected to: {self.path}")
        else:
            print("No db found. Run db.sync() to pull from Pi.")

    def _conn(self):
        if not self.path or not os.path.exists(self.path):
            raise FileNotFoundError("No db available. Run db.sync() first.")
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    # ------------------------------------------------------------------
    # Raw DataFrames
    # ------------------------------------------------------------------

    def sleep(self):
        with self._conn() as conn:
            df = pd.read_sql("SELECT * FROM daily_log ORDER BY date", conn)
        if df.empty:
            return pd.DataFrame({'date':[],'wake_time':[],'bed_time':[],'sleep_quality':[],'night_sleep_hr':[]})
        df['wake_time'] = pd.to_datetime(df['date'] + ' ' + df['wake_time'].fillna(''), errors='coerce')
        df['bed_time']  = pd.to_datetime(df['date'] + ' ' + df['bed_time'].fillna(''),  errors='coerce')
        df['night_sleep_start'] = df['bed_time'].shift(1)
        df['night_sleep_hr'] = (df['wake_time'] - df['night_sleep_start']).dt.total_seconds() / 3600
        return df

    def time_blocks(self):
        with self._conn() as conn:
            df = pd.read_sql("SELECT * FROM time_blocks ORDER BY date, start_time", conn)
        if df.empty:
            return df
        df['start_dt'] = pd.to_datetime(df['date'] + ' ' + df['start_time'], errors='coerce')
        df['end_dt']   = pd.to_datetime(df['date'] + ' ' + df['end_time'].fillna(''),   errors='coerce')
        df['duration_min'] = (df['end_dt'] - df['start_dt']).dt.total_seconds() / 60
        df['hour'] = df['start_dt'].dt.hour
        return df

    def time_use_by_day(self):
        """Daily totals per category — good for stacked bar charts."""
        df = self.time_blocks().dropna(subset=['duration_min'])
        if df.empty:
            return df
        return df.groupby(['date', 'category'])['duration_min'].sum().reset_index()

    def time_use_totals(self):
        """Overall totals per category across all days."""
        df = self.time_blocks().dropna(subset=['duration_min'])
        if df.empty:
            return df
        return df.groupby('category')['duration_min'].sum().sort_values(ascending=False).reset_index()

    def mood(self):
        with self._conn() as conn:
            df = pd.read_sql("SELECT * FROM mood_log ORDER BY event_time", conn)
        if df.empty:
            return df
        df['event_time'] = pd.to_datetime(df['event_time'])
        df['date'] = df['event_time'].dt.date.astype(str)
        df['hour'] = df['event_time'].dt.hour
        return df

    def food(self):
        with self._conn() as conn:
            df = pd.read_sql("SELECT * FROM meals ORDER BY event_time", conn)
        if df.empty:
            return df
        df['event_time'] = pd.to_datetime(df['event_time'])
        df['date'] = df['event_time'].dt.date.astype(str)
        df['hour'] = df['event_time'].dt.hour
        return df

    def exercise(self):
        with self._conn() as conn:
            df = pd.read_sql("SELECT * FROM exercise ORDER BY event_time", conn)
        if df.empty:
            return df
        df['event_time'] = pd.to_datetime(df['event_time'])
        df['date'] = df['event_time'].dt.date.astype(str)
        return df

    # ------------------------------------------------------------------
    # Summary helpers
    # ------------------------------------------------------------------

    def daily_summary(self, date=None):
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        with self._conn() as conn:
            daily  = conn.execute("SELECT * FROM daily_log WHERE date = ?", (date,)).fetchone()
            blocks = conn.execute("SELECT * FROM time_blocks WHERE date = ? ORDER BY start_time", (date,)).fetchall()
            food   = conn.execute("SELECT * FROM meals WHERE event_time LIKE ?", (date+'%',)).fetchall()
            ex     = conn.execute("SELECT * FROM exercise WHERE event_time LIKE ?", (date+'%',)).fetchall()
            moods  = conn.execute("SELECT * FROM mood_log WHERE event_time LIKE ?", (date+'%',)).fetchall()

        print(f"\n{'='*40}")
        print(f"  {date}")
        print(f"{'='*40}")

        wake = daily['wake_time'] if daily and daily['wake_time'] else '—'
        bed  = daily['bed_time']  if daily and daily['bed_time']  else '—'
        sq   = f"  sleep quality {daily['sleep_quality']}/5" if daily and daily['sleep_quality'] else ''
        print(f"\n🌅 Wake: {wake}   🌙 Bed: {bed}{sq}")

        print(f"\n⏱ Time Blocks ({len(blocks)}):")
        total = 0
        for b in blocks:
            dur = ''
            if b['start_time'] and b['end_time']:
                s = datetime.strptime(b['start_time'], '%H:%M')
                e = datetime.strptime(b['end_time'],   '%H:%M')
                mins = (e - s).seconds // 60
                total += mins
                dur = f" ({mins}min)"
            desc = f" — {b['description']}" if b['description'] else ''
            ongoing = ' [ongoing]' if not b['end_time'] else ''
            print(f"   {b['start_time']} {b['category']}{desc}{dur}{ongoing}")
        if total:
            print(f"   Total tracked: {total//60}h {total%60}m")

        print(f"\n🍎 Food ({len(food)}):")
        for f in food:
            print(f"   {f['event_time'][11:16]}  [{f['type']}]  {f['description']}")

        print(f"\n🏃 Exercise ({len(ex)}):")
        for e in ex:
            dur = f" {int(e['duration_min'])}min" if e['duration_min'] else ''
            print(f"   {e['event_time'][11:16]}  {e['type']}{dur}")

        print(f"\n😊 Mood/Energy ({len(moods)}):")
        for m in moods:
            print(f"   {m['event_time'][11:16]}  energy {m['energy']}/5  mood {m['mood']}/5")
        print()

    def productive_hours_per_day(self):
        """Hours spent on job-search related categories per day."""
        df = self.time_blocks().dropna(subset=['duration_min'])
        if df.empty:
            return df
        prod = df[df['category'].isin(PRODUCTIVE_CATEGORIES)]
        return prod.groupby('date')['duration_min'].sum().div(60).reset_index(name='productive_hours')

    def sync(self, pi_ip='192.168.88.9', user='simonhans'):
        dest = os.path.expanduser('~/personal_tracker/personal.db')
        os.makedirs(os.path.expanduser('~/personal_tracker'), exist_ok=True)
        src = f"{user}@{pi_ip}:~/personal_tracker/personal.db"
        print(f"Pulling {src} → {dest}")
        key = os.path.expanduser('~/.ssh/pi')
        ssh_opts = ['-i', key] if os.path.exists(key) else []
        result = subprocess.run(['scp'] + ssh_opts + [src, dest], capture_output=True, text=True)
        if result.returncode == 0:
            self.path = dest
            print("Done.")
        else:
            print(f"Error: {result.stderr}")
