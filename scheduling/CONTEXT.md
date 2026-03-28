# Project Context — Weekly Planner CLI

## What this is

A personal CLI weekly planner built in Python. Started as a trip planner for a family holiday in Waikoloa, Big Island, Hawaii, and generalised into an ongoing weekly planning tool used before transferring to a paper planner.

The core workflow: draft the week in the terminal, review it, push to Google Calendar for phone access and real-time edits on the go.

---

## Why it was built

The owner wanted a programmable, archivable planning layer between thinking-about-the-week and committing it to a paper planner. Key constraints:

- Family with a toddler: nap window (12:00–14:00) is a hard daily constraint that shapes all scheduling
- Recurring weekly themes (Movement Monday, Library Tuesday, etc.) that need to carry forward automatically
- All weeks kept as structured archive for later data mining
- Google Calendar integration so the plan is accessible on a phone and family members can see it

---

## Tech stack

| Layer | Choice |
|---|---|
| Language | Python 3.7 |
| Terminal UI | `rich` — panels, rules, coloured text |
| Interactive prompts | `questionary` (`<2.0` for Python 3.7 compat) |
| Data storage | JSON files, one per week (`weeks/YYYY-WXX.json`) |
| Calendar sync | Google Calendar API v3 via `google-api-python-client` |
| Auth | OAuth2, `google-auth-oauthlib`, token stored locally |

---

## Architecture

```
plan.py      CLI entry point + all commands
gcal.py      Google Calendar integration (auth, push, pull)
config.json  Global config: nap times, weekly themes, GCal settings
weeks/       Append-only archive of week files (YYYY-WXX.json)
archive/     Historical data (original Waikoloa trip itinerary)
credentials/ OAuth token + client secret (gitignored)
```

### Week file format

Each week is a self-contained JSON file keyed by ISO date. Activities carry an optional `gcal_event_id` that gets written back after a push, enabling idempotent re-pushes (update in place, no duplicates).

```json
{
  "week": "2026-W14",
  "days": {
    "2026-03-30": {
      "nap_override": null,
      "activities": [
        {
          "id": "m30a1",
          "time": "09:00",
          "title": "Pu'ukohola Heiau NHS",
          "notes": "...",
          "tags": ["🧒", "🏛️"],
          "gcal_event_id": "abc123"
        }
      ]
    }
  }
}
```

### Nap window

The nap is not stored in week files. It is injected at display time from `config.json` and sorted into the timeline like any other activity. Per-day overrides are stored as `nap_override` in the day object. This keeps the nap universally present without polluting the data files, and makes it trivial to change globally.

---

## Google Calendar integration

### Multi-account pull

The owner has three Google accounts:
- `simonhansedasi` — authenticated account (business/tertiary)
- `woses21` — personal account with recurring events
- `vitruviansandwich` — shared account used by wife

`woses21` and `vitruviansandwich` calendars were shared into `simonhansedasi`. The `pull` command queries all three calendar IDs in parallel and deduplicates by event ID. Pulled events are displayed inline with plan activities, sorted by time, labelled by source account.

Push targets the primary calendar of the authenticated account only.

### Timezone handling

Pulled events are converted to `Pacific/Honolulu` (HST, UTC-10, no DST) regardless of the timezone they were created in. This matters because shared calendars from mainland accounts store event times in ET/PT/UTC, which would otherwise display incorrectly.

### Idempotent push

On first push, event IDs returned by the API are written back into the week JSON. Subsequent pushes for the same week call `events.update()` rather than `events.insert()`, so editing an activity and re-pushing updates the calendar event in place rather than creating a duplicate.

---

## CLI commands

```
plan show week [YYYY-WXX]   Week view (defaults to current)
plan show next / prev        Navigate weeks
plan show today              Day view
plan show YYYY-MM-DD         Specific day
plan add                     Interactive activity creation
plan edit                    Interactive edit / delete (incl. nap override)
plan nap                     Update global nap window
plan check                   Outstanding ⚠️ items across all weeks
plan auth                    Google OAuth setup
plan whoami                  Show authenticated Google account
plan calendars               List all calendars visible to that account
plan push [YYYY-WXX]         Push week to Google Calendar
plan pull [YYYY-WXX]         Week view with GCal events overlaid
```

---

## Notable decisions

**Append-only week archive** — week files are never deleted or overwritten wholesale. This was an intentional design choice to support future data mining (activity patterns, theme adherence, seasonal planning).

**Nap as config, not data** — keeping the nap in `config.json` rather than duplicating it into every day of every week means changing the nap time is a one-line edit with instant global effect.

**No ORM, no database** — plain JSON files. The dataset is small (one file per week, forever), human-readable, trivially diffable in git, and requires no setup to run on a new machine.

**`questionary<2.0` pin** — `questionary` 2.0 dropped Python 3.7 support. Pinned to `>=1.10,<2.0` to maintain compatibility without requiring a Python upgrade.

**Location / Maps** — activities have an optional `location` field. In the terminal it renders as a clickable 📍 Google Maps link (OSC 8 hyperlink). Location is included in GCal push (`location` field on the event) and captured on pull from GCal events that have a location set.

**Pull writes to JSON** — `plan pull` fetches GCal events and writes them into the week JSON as activities with `"gcal_source": true`. They appear in magenta with a 📅 marker and calendar label. Pull is idempotent — re-running won't duplicate already-imported events. `push` skips `gcal_source` activities so they are never sent back to GCal.

---

## Owner profile

Geophysicist. Strong interest in geology, volcanology, astronomy, and cultural heritage — this shows in the activity data (petroglyph sites, lava field walks, anchialine ponds, heiau). Family of three with a toddler. The planner is a personal productivity tool, not production software.
