CREATE TABLE IF NOT EXISTS daily_log (
    date          TEXT PRIMARY KEY,
    wake_time     TEXT,
    bed_time      TEXT,
    sleep_quality INTEGER,  -- 1-5
    weight_lbs    REAL
);

CREATE TABLE IF NOT EXISTS time_blocks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date        TEXT NOT NULL,
    start_time  TEXT NOT NULL,
    end_time    TEXT,
    category    TEXT NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS meals (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    event_time  TEXT NOT NULL,
    type        TEXT NOT NULL,  -- 'meal', 'snack', 'drink'
    description TEXT
);

CREATE TABLE IF NOT EXISTS meal_items (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT UNIQUE NOT NULL,
    use_count INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS exercise (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    event_time   TEXT NOT NULL,
    type         TEXT,
    duration_min REAL,
    intensity    INTEGER  -- 1-5
);

CREATE TABLE IF NOT EXISTS mood_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    event_time TEXT NOT NULL,
    energy     INTEGER NOT NULL,  -- 1-5
    mood       INTEGER NOT NULL   -- 1-5
);

CREATE TABLE IF NOT EXISTS substances (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    event_time TEXT NOT NULL,
    category   TEXT NOT NULL,  -- 'caffeine', 'cannabis', 'alcohol'
    type       TEXT NOT NULL,  -- coffee/espresso | flower/vape/edible | beer/wine/spirits
    notes      TEXT
);

CREATE TABLE IF NOT EXISTS naps (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    date         TEXT NOT NULL,
    start_time   TEXT NOT NULL,
    end_time     TEXT,
    duration_min REAL
);

CREATE TABLE IF NOT EXISTS hydration_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    event_time TEXT NOT NULL,
    amount     REAL NOT NULL DEFAULT 1.0  -- bottles (1.0 full, 0.5 half, 0.25 quarter)
);
