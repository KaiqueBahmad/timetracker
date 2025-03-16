DROP TABLE IF EXISTS subject;
DROP TABLE IF EXISTS user;

CREATE TABLE user (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  username      TEXT NOT NULL UNIQUE,
  email         TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE subject (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  name         TEXT NOT NULL,
  user_id      INTEGER NOT NULL,
  FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
  UNIQUE(name, user_id) -- Ensures a user can't have the same subject name twice
);

INSERT INTO user (username, email, password_hash) VALUES
  ('john_doe', 'john@example.com', 'hashed_password_1'),
  ('jane_smith', 'jane@example.com', 'hashed_password_2');

INSERT INTO subject (name, user_id) VALUES
  ('pina', 1),
  ('yupi', 1),
  ('pina', 2),
  ('yupi', 2)