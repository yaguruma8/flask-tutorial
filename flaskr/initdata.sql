-- 初期データ
-- ユーザー
INSERT INTO user (username, password)
  VALUES 
  ('test', 'pbkdf2:sha256:260000$0KdKJEg3ytLeZAxY$ad3511bc89202d813af43d4c20d75c922d43bbcf722cfe68ab2edf3c3e5fbec8'),
  ('hoge','pbkdf2:sha256:260000$CWGSIqZThCrkw0km$4b5a3692236650361d216c7a1bd6846b3ce020b515000c1171cc33cde625c082'),
  ('fuga','pbkdf2:sha256:260000$3cd9mlrLjz9DsqG1$a4922fbfdd0455a7ca469cbd8b5795afe83267d8f8ce34ec00af2b99a0753898'),
  ('piyo','pbkdf2:sha256:260000$iXwijzzhkqd1rYkG$fcee639e897919e86a36498122c0e12c3d581fe81a9024597b41c80897b857e7')
  ;

-- 記事
INSERT INTO post (author_id, title, body)
  VALUES
  (1, 'testの投稿1', 'testの投稿'),
  (1, 'testの投稿2', 'testの長めの投稿。とてもとてもとてもとてもとてもとてもとてもとてもとてもとてもとてもとてもとてもとてもとてもとてもとてもとてもとてもとてもとてもとてもとてもとてもとてもとてもとてもとてもとてもとてもとてもとても長い。'),
  (2, 'hogeの投稿', 'this is a pen. you are a girl. hogehogehogehoge'),
  (3, 'fugaの投稿はタイトルがとてもすごく精一杯気持ちよくうんざりと長い長い長い長いすごく長い長い長い長い長い長い長い長い長い長い', 'fugaの投稿はこんなもんでしょう多分おそらくきっと'),
  (3, 'fugaの短めの投稿', 'あ'),
  (4, 'piyoの投稿。', 'piyopiyo')
  ;

-- コメント
INSERT INTO comment (post_id, commenter_id, body)
  VALUES
  (1, 1, 'testが自分の投稿にコメントする'),
  (1, 2, 'testの投稿にhogeがコメントする'),
  (4, 1, 'testがfugaの投稿にコメントする。フガフガ'),
  (5, 4, 'fugaの投稿にpiyoがコメント。'),
  (6, 4, 'piyoが自分の投稿にコメントする。')
  ;

-- 投票
INSERT INTO vote (post_id, user_id, intention)
  VALUES
  (1, 2, 0),
  (1, 3, 1),
  (1, 4, 1),
  (2, 1, 0),
  (3, 1, 1)
  ;
