# OmaElu

Life organization tools — the personal infrastructure branch of Edasi Motlev. Two integrated systems: a CLI weekly planner that syncs with Google Calendar, and a mobile-first personal health tracker running on a Raspberry Pi.

---

## Sub-projects

### `scheduling/` — Weekly Planner CLI
Interactive CLI for planning the week ahead. Pulls Google Calendar events, adds activities with time/location/tags/notes, pushes back to Calendar. Designed around a toddler nap window and weekly themed days.

**Run:**
```bash
python plan.py show week
python plan.py add
python plan.py push
```

### `personal_tracker/` — Personal Health Tracker
Mobile-first Flask app running on a Raspberry Pi (port 5001). Logs wake/sleep, mood, energy, food, exercise, substances, hydration, and naps. Accessible via Tailscale from anywhere.

**Access:**
- Home: `http://192.168.88.9:5001`
- Away: `http://100.93.132.118:5001`

---

## Tech

Flask, SQLite, Python, Click, Rich, questionary, Google Calendar API, Raspberry Pi, Tailscale, systemd, ntfy (push notifications), cron

---

## Infrastructure

Both tools are deployed on a Raspberry Pi (HST timezone) via rsync + systemd services. Push notifications via [ntfy.sh](https://ntfy.sh) — topic `remember_dummy` for personal reminders.
