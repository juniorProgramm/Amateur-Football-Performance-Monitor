PRAGMA foreign_keys = ON;

CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'coach', 'player')),
    approved INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE team (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    coach_id INTEGER,
    season TEXT,
    FOREIGN KEY (coach_id) REFERENCES user(id) ON DELETE SET NULL
);

CREATE TABLE player (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER UNIQUE,
    name TEXT NOT NULL,
    position TEXT,
    team_id INTEGER,
    age INTEGER,
    height REAL,
    weight REAL,

    FOREIGN KEY (team_id) REFERENCES team(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);


CREATE TABLE performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    date DATE NOT NULL,
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    passes_completed INTEGER DEFAULT 0,
    passes_attempted INTEGER DEFAULT 0,
    pass_accuracy REAL DEFAULT 0,
    tackles INTEGER DEFAULT 0,
    rating INTEGER DEFAULT 0,
    FOREIGN KEY (player_id) REFERENCES player(id) ON DELETE CASCADE
);

 CREATE TABLE training (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL,
    date DATE NOT NULL,
    focus TEXT,
    duration INTEGER,
    attendance INTEGER DEFAULT 0,
    FOREIGN KEY (team_id) REFERENCES team(id) ON DELETE CASCADE
);
CREATE
CREATE TABLE goal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER,
    team_id INTEGER,
    description TEXT,
    start_date DATE,
    end_date DATE,
    status TEXT CHECK (status IN ('open','in_progress','completed')) DEFAULT 'open',
    FOREIGN KEY (player_id) REFERENCES player(id) ON DELETE CASCADE,
    FOREIGN KEY (team_id) REFERENCES team(id) ON DELETE CASCADE
);
