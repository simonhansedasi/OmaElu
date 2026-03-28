# OmaElu

Life organization tools — the personal infrastructure branch of Edasi Motlev. Two integrated systems: a CLI weekly planner that syncs with Google Calendar, and a mobile-first personal health tracker running on a Raspberry Pi.

---

## Sub-projects

### `scheduling/` — Weekly Planner CLI

Interactive CLI for planning the week ahead. Pulls Google Calendar events, adds activities with time/location/tags/notes, pushes back to Calendar. Designed around a toddler nap window and weekly themed days. Supports multi-account GCal pull with timezone normalization (HST). Append-only week JSON archive for future data mining.

**Run:**
```bash
python plan.py show week
python plan.py add
python plan.py push
python plan.py pull
```

> Moved from standalone `simonhansedasi/scheduling` repo into OmaElu in March 2026.

---

### `personal_tracker/` — Personal Health Tracker

Mobile-first Flask app running on a Raspberry Pi (port 5001). Logs wake/sleep, mood, energy, food, exercise, weight, hydration (20 oz bottle, target 5–6/day), and naps. Accessible via Tailscale from anywhere.

Push notifications via ntfy.sh (`remember_dummy`) every 15 min — wake check, weight nudge, mood, hydration, and bedtime recommendation.

**Access:**
- Home: `http://192.168.88.9:5001`
- Away: `http://100.93.132.118:5001`

> Moved from `dada_science/personal_tracker/` into OmaElu in March 2026.

---

## Tech

Flask, SQLite, Python, Click, Rich, questionary, Google Calendar API, OAuth2, Raspberry Pi, Tailscale, systemd, ntfy.sh, cron

---

## Infrastructure

Both tools are deployed on a Raspberry Pi (HST timezone) via rsync + systemd services. Push notifications via [ntfy.sh](https://ntfy.sh) — topic `remember_dummy` for personal reminders.
