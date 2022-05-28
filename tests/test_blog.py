import pytest
from flask import testing, Flask

from conftest import AuthAction

from flaskr.db import get_db


# indexのテスト(1)
# indexのviewはテストデータを表示する
# ログインしていないとき - indexはログイン・登録のリンクを表示する
# ログインしているとき - indexはログアウトのリンクを表示する
# 22/5/4 仕様変更によりindexはarticleへのリンクを（loginしてなくても）表示するはず
# 22/5/12 indexはvoteの票数を（loginしてなくても）表示するはず
def test_index(client: testing.FlaskClient, auth: AuthAction):
    res = client.get('/')
    assert b'Login' in res.data
    assert b'Register' in res.data
    assert b'/1' in res.data
    assert '賛成(0) 反対(0)' in res.get_data(as_text=True)

    auth.login()
    res = client.get('/')
    assert b'Logout' in res.data
    assert b'test title' in res.data
    assert b'by test' in res.data
    assert b'/1' in res.data


# indexのテスト(2)
# /create, /<id>/update, /<id>/delete へのアクセスはログイン要
# ログインしていない場合は /auth/login へ飛ぶはず
@pytest.mark.parametrize('path', ('/create', '/1/update', '/1/delete'))
def test_login_requierd(client: testing.FlaskClient, path):
    res = client.post(path)
    assert res.headers['Location'] == '/auth/login'


# /<id>/update, /<id>/delete へのアクセスは書いたユーザーのみ
# 書いたユーザー以外がアクセスしたら403エラーが出るはず
def test_author_required(app: Flask, client: testing.FlaskClient, auth: AuthAction):
    # DBをいじってid=1の投稿のauthorをauthor_id=1から2に変更する
    with app.app_context():
        db = get_db()
        db.execute('UPDATE post SET author_id = 2 WHERE id = 1')
        db.commit()

    # author_id=1 (test) でログインして、投稿にアクセスできないことを確認する
    auth.login()
    assert client.post('/1/update').status_code == 403
    assert client.post('/1/delete').status_code == 403
    res = client.get('/')
    assert b'/1/update' not in res.data


# 存在しない投稿のテスト
@pytest.mark.parametrize('path', ('/2/update', '/2/delete'))
def test_exists_required(client: testing.FlaskClient, auth: AuthAction, path):
    auth.login()
    assert client.post(path).status_code == 404


# createのテスト
# ログインしていればGETは200を返すはず
# ログインしていればPOSTで新しい投稿ができるはず
def test_create(app: Flask, client: testing.FlaskClient, auth: AuthAction):
    auth.login()
    assert client.get('/create').status_code == 200

    client.post('/create', data={'title': 'created', 'body': ''})
    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM post').fetchone()[0]
        assert count == 2


# updateのテスト
# ログインしていればGETは200を返すはず
# ログインしていればPOSTで投稿の修正ができるはず
def test_update(app: Flask, client: testing.FlaskClient, auth: AuthAction):
    auth.login()
    assert client.get('/1/update').status_code == 200

    client.post('/1/update', data={'title': 'updated', 'body': ''})
    with app.app_context():
        db = get_db()
        post = db.execute('SELECT * FROM post WHERE id = 1').fetchone()
        assert post['title'] == 'updated'


# create, updateのテスト
# タイトルを入力しないで投稿した場合はエラーが表示されるはず
@pytest.mark.parametrize('path', ('/create', '/1/update'))
def test_create_update_validate(client, auth: AuthAction, path):
    auth.login()
    res = client.post(path, data={'title': '', 'body': ''})
    assert b'Title is required.' in res.data


# deleteのテスト
# 削除したらindexにリダイレクトするはず
# 削除したらそのidの投稿はデータベースからなくなっているはず
def test_delete(app: Flask, client: testing.FlaskClient, auth: AuthAction):
    auth.login()
    res = client.post('/1/delete')
    assert res.headers['Location'] == '/'

    with app.app_context():
        db = get_db()
        post = db.execute('SELECT * FROM post WHERE id = 1').fetchone()
        assert post is None


# articleのテスト
# loginしてもしなくても記事の詳細は表示されるはず
# loginしていればupdateへのリンクがあり、loginしてなければないはず
def test_article(client: testing.FlaskClient, auth: AuthAction):
    res = client.get('/1')
    assert b'test title' in res.data
    assert b'by test' in res.data
    assert b'test\nbody' in res.data
    assert b'/1/update' not in res.data

    auth.login()
    res = client.get('/1')
    assert b'test title' in res.data
    assert b'by test' in res.data
    assert b'test\nbody' in res.data
    assert b'/1/update' in res.data


# commentのテスト
def test_comment(client: testing.FlaskClient, auth: AuthAction):
    """コメントの表示のテスト"""
    res = client.get('/1')
    assert b'maxlength="40"' not in res.data

    auth.login()
    res = client.get('/1')
    assert b'maxlength="40"' in res.data


@pytest.mark.parametrize(('body', 'message'), (
    ('', b'comment is empty.'),
    ('あいうえおあいうえおあいうえおあいうえおあいうえおあいうえおあいうえおあいうえおあ', b'comment is too long.')
))
def test_comment_create_error(client: testing.FlaskClient, auth: AuthAction, body, message):
    """コメント入力エラーのテスト"""
    auth.login()

    res = client.post('/1/comment/create', data={'body': body})
    assert message in res.data


def test_comment_create(app: Flask, client: testing.FlaskClient, auth: AuthAction):
    """コメント入力のテスト"""
    auth.login()

    client.post('/1/comment/create', data={'body': 'Hello, Good-bye.'})
    with app.app_context():
        db = get_db()
        comment = db.execute('SELECT * FROM comment WHERE id = 2').fetchone()
        assert comment['body'] == 'Hello, Good-bye.'


def test_comment_delete_error(client: testing.FlaskClient, auth: AuthAction):
    """コメント削除エラー（存在しないコメント）のテスト"""
    auth.login()

    res = client.post('/1/comment/delete', data={'comment_id': '2'})
    assert b'comment is not exist.' in res.data

    res = client.post('/1/comment/delete', data={'comment_id': 'hello'})
    assert b'comment is not exist.' in res.data


def test_comment_delete_error2(app: Flask, client: testing.FlaskClient, auth: AuthAction):
    """コメント削除エラー（コメント投稿者と異なるユーザー）のテスト"""
    with app.app_context():
        db = get_db()
        db.execute('UPDATE comment SET commenter_id = 2 WHERE id = 1')
        db.commit()

    auth.login()

    res = client.post('/1/comment/delete', data={'comment_id': '1'})
    assert b'permission to delete.' in res.data


def test_comment_delete(app: Flask, client: testing.FlaskClient, auth: AuthAction):
    """コメント削除のテスト"""
    auth.login()
    res = client.post('/1/comment/delete', data={'comment_id': '1'})
    assert res.headers['Location'] == '/1'

    with app.app_context():
        db = get_db()
        comment = db.execute('SELECT * FROM comment WHERE id = 1').fetchone()
        assert comment is None


def test_vote(app: Flask, client: testing.FlaskClient, auth: AuthAction):
    """投票のテスト"""
    auth.login()
    res = client.post('/1/vote', data={'intention': '1'})
    assert res.headers['Location'] == '/1'

    with app.app_context():
        vote = get_db().execute('SELECT * FROM vote WHERE post_id = 1 AND user_id = 1').fetchone()
        assert vote['intention'] == 1


def test_vote_error(app: Flask, client: testing.FlaskClient, auth: AuthAction):
    """投票のエラーのテスト"""
    auth.login()
    # postの値の不足
    res = client.post('/1/vote')
    assert res.status_code == 400

    # 不正な値をpost
    res = client.post('/1/vote', data={'intention': '2'})
    assert b'illegal value.' in res.data

    # 重複投票
    with app.app_context():
        client.post('/1/vote', data={'intention': '1'})
        res = client.post('/1/vote', data={'intention': '0'})
        assert b'you are already vote.' in res.data


def test_vote_view(client: testing.FlaskClient, auth: AuthAction):
    """投票の表示のテスト"""
    # ログインしていなければ投票結果のみ
    res = client.get('/1')
    assert '賛成(0) 反対(0)' in res.get_data(as_text=True)
    assert b'name="intention" value="1"' not in res.data

    # ログインしていれば投票ボタンが表示される
    auth.login()
    res = client.get('/1')
    assert b'name="intention" value="1"' in res.data

    # 投票済の場合は投票取り消しボタンが表示される
    client.post('/1/vote', data={'intention': '1'})
    res = client.get('/1')
    assert '賛成(1) 反対(0)' in res.get_data(as_text=True)
    assert '賛成に投票済' in res.get_data(as_text=True)
    assert '取り消す' in res.get_data(as_text=True)


def test_vote_cancel(app: Flask, client: testing.FlaskClient, auth: AuthAction):
    """投票の取り消しのテスト"""
    # preprocess
    auth.login()
    with app.app_context():
        res = client.post('/1/vote', data={'intention': '1'})
        vote = get_db().execute(
            'SELECT * FROM vote WHERE post_id = 1 AND user_id = 1').fetchone()
        assert vote is not None

    # 投票を取り消しするとDBから削除される
    res = client.post('/1/vote/cancel')
    assert res.headers['Location'] == '/1'

    # 投票を取り消した場合は再び記事詳細ページに投票ボタンが表示される
    res = client.get('/1')
    assert b'name="intention" value="1"' in res.data
    assert '取り消す' not in res.get_data(as_text=True)

    # データベースからは削除されている
    with app.app_context():
        vote = get_db().execute(
            'SELECT * FROM vote WHERE post_id = 1 AND user_id = 1').fetchone()
        assert vote is None

    # 重複して削除しようとした場合はエラーになる
    res = client.post('/1/vote/cancel')
    assert b'you are not vote.' in res.data


def test_author_search(app: Flask, client: testing.FlaskClient):
    '''投稿者の検索のテスト'''
    # preprocess
    with app.app_context():
        db = get_db()
        db.execute(
            'INSERT INTO post (title, body, author_id, created) '
            ' VALUES ("test title2", "test2", 2, "2018-01-01 00:00:00");'
        )
        db.commit()
    # 投稿者名（全文一致）
    res = client.get('/search?author=test')
    assert '1件' in res.get_data(as_text=True)

    # 投稿者名（一部一致）
    res = client.get('/search?author=t')
    assert '2件' in res.get_data(as_text=True)

    # 投稿者名が存在しなければ0件
    res = client.get('/search?author=hoge')
    assert '0件' in res.get_data(as_text=True)

    # クエリパラメータのkeyが異なる場合はindexにリダイレクト
    res = client.get('/search?hoge=fuga')
    assert res.headers['Location'] == '/'

    # 空白で送信した場合は0件+flash
    res = client.get('/search?author=')
    assert '0件' in res.get_data(as_text=True)
    assert '検索条件を指定してください' in res.get_data(as_text=True)
