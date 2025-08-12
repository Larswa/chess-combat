-- Chess Combat Database Schema
CREATE TABLE players (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE games (
    id SERIAL PRIMARY KEY,
    white_id INTEGER REFERENCES players(id),
    black_id INTEGER REFERENCES players(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_finished VARCHAR DEFAULT 'false',
    result VARCHAR,
    termination VARCHAR,
    finished_at TIMESTAMP
);

CREATE TABLE moves (
    id SERIAL PRIMARY KEY,
    game_id INTEGER REFERENCES games(id),
    move VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
