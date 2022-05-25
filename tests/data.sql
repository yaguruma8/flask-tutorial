DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS post;
DROP TABLE IF EXISTS comment;
DROP TABLE IF EXISTS vote;
DROP VIEW IF EXISTS vote_count;
DROP VIEW IF EXISTS comment_count;
DROP VIEW IF EXISTS all_posts;

-- テーブル定義
CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE post (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  FOREIGN KEY (author_id) REFERENCES user (id)
);

CREATE TABLE comment (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  post_id INTEGER NOT NULL,
  commenter_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  body TEXT NOT NULL,
  FOREIGN KEY (post_id) REFERENCES post (id),
  FOREIGN KEY (commenter_id) REFERENCES user (id)
);

CREATE TABLE vote (
  post_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  intention INTEGER NOT NULL,
  FOREIGN KEY (post_id) REFERENCES post (id),
  FOREIGN KEY (user_id) REFERENCES user (id)
);


-- ビュー定義
-- 投稿ごとのコメント数
CREATE VIEW comment_count (post_id, cnt)
AS
  SELECT
    post_id,
    count(*)
  FROM comment
  GROUP BY post_id
;

-- 投稿ごとの投票数
CREATE VIEW vote_count (post_id, agree, disagree)
AS
  SELECT
    post_id,
    SUM(CASE WHEN intention = 1 THEN 1 ELSE 0 END),
    SUM(CASE WHEN intention = 0 THEN 1 ELSE 0 END)
  FROM vote
  GROUP BY post_id
;

-- 投稿＋投稿者名＋コメント数＋投票数 の一覧
CREATE VIEW all_posts 
  (id, title, body, created, author_id, 
  author_name, 
  comment_count, 
  agree, disagree)
AS
  SELECT
    p.id, p.title, p.body, p.created, p.author_id,
    u.username,
    c.cnt,
    v.agree, v.disagree
  FROM post AS p
    INNER JOIN user AS u 
      ON p.author_id = u.id
    LEFT OUTER JOIN comment_count AS c
      ON p.id = c.post_id
    LEFT OUTER JOIN vote_count AS v 
      ON p.id = v.post_id
;


-- テストデータ
INSERT INTO user (username, password)
VALUES
  ('test', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f'),
  ('other', 'pbkdf2:sha256:50000$kJPKsz6N$d2d4784f1b030a9761f5ccaeeaca413f27f2ecb76d6168407af962ddce849f79');

INSERT INTO post (title, body, author_id, created)
VALUES
  ('test title', 'test' || x'0a' || 'body', 1, '2018-01-01 00:00:00');

INSERT INTO comment (post_id, commenter_id, body)
VALUES
  (1, 1, 'test comment')