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

## Service Management (SSH)

```bash
sudo systemctl restart personal-tracker
sudo systemctl status personal-tracker
sudo journalctl -u personal-tracker -f
```
