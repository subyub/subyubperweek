CREATE TABLE comments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  episode_id TEXT NOT NULL,
  nickname TEXT,
  body TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX idx_comments_episode_id ON comments(episode_id);
