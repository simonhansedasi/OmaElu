# Personal Tracker — Quick Reference

App runs at `http://192.168.88.9:5001` (home) or `http://100.93.132.118:5001` (Tailscale).

---

## Daily Flow

### Morning
1. **Wake Up** — tap, log sleep quality 1–5
2. **Weight** — optional daily weigh-in

### Throughout the day
- **Start Block** — pick a category, optional description, tap Confirm
- **Stop Block** — tap when switching tasks; duration computed automatically
- **Food / Drink** — quick-select or type; choose meal / snack / drink
- **Exercise** — type, duration, intensity 1–5
- **Mood / Energy** — tap both sliders 1–5 anytime
- **Hydration** — tap Full / ½ / ¼ each time you drink; progress bar on home screen shows daily total vs. target
- **Nap** — tap 😴 Nap to start; tap ⏰ Wake when done; duration computed automatically

### Evening
- **Bedtime** — tap when going to sleep

---

## Offset Bar

Every button opens a dialog with **"How long ago?"** — log things after the fact without rushing. Common offsets: Now / 5m / 10m / 15m / 20m / 30m / custom.

---

## Time Block Categories

| Category | Use for |
|----------|---------|
| 💼 Job Search | Applications, interviews, recruiter calls |
| 🔗 LinkedIn | Profile work, outreach, networking |
| 💻 Coding / Portfolio | Projects, side work, code practice |
| 📚 Learning | Courses, reading, skill building |
| 🏃 Exercise | Any physical activity |
| 🏠 Household | Chores, admin, home tasks |
| 🛒 Errands | Shopping, appointments |
| 😴 Rest | Naps, downtime |
| 👥 Social | Time with people |
| 🧘 Self Care | Mental health, meditation, personal time |
| ✏️ Other | Anything else |

---

## Today's Log

Tap **Today's Log** on the home screen to see all events for the current day. Tap any entry to edit or delete it.

---

## Hydration Target

20 oz bottle. Target 0.25–0.5 bottles/hour (5–6 bottles/day, ~100–120 oz). Progress bar on home screen is color-coded: green = on track, orange = behind. Resets at wake time each day.

---

## Push Notifications (ntfy.sh)

`remind_personal.py` runs every 15 min via cron on the Pi. Topic: `remember_dummy`. Sends:
- 8am: wake check if wake time not yet logged
- Weight: once daily nudge
- Mood: every 3h since last log
- Hydration: every 2h since last drink (includes current bottle count)
- Bedtime: when wake + 17h is reached (targets ~7h sleep)

---

## Service Management (SSH)

```bash
sudo systemctl restart personal-tracker
sudo systemctl status personal-tracker
sudo journalctl -u personal-tracker -f
```

---

## Traveling / Timezone Fix

If the Pi is on the wrong timezone, all new entries will log the wrong time.

**Fix the timezone** (no sudo needed on this Pi):
```bash
timedatectl set-timezone America/Los_Angeles   # Seattle / PNW
timedatectl set-timezone Pacific/Honolulu      # Hawaii
```

**Backfill today's entries** — see the "Timezone Changes" section in README.md for the full backfill script. Quick summary: SSH into the Pi, run the Python snippet with the correct offset (e.g. `+3 hours` for HI→PNW), and it will shift all of today's records in place.
