import pytest
from flask import testing, Flask

from conftest import AuthAction

from flaskr.db import get_db


# indexのテスト(1)
# indexのviewはテストデータを表示する
# ログインしていないとき - indexはログイン・登録のリンクを表示する
# ログインしているとき - indexはログアウトのリンクを表示する
# 22/5/4 仕様変更によりindexはarticleへのリンクを（loginしてなくても）表示するはず
def test_index(client: testing.FlaskClient, auth: AuthAction):
    res = client.get('/')
    assert b'Login' in res.data
    assert b'Register' in res.data
    assert b'/1' in res.data

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

    res = client.post('/1/comment/2/delete')
    assert b'comment is not exist.' in res.data


def test_comment_delete_error2(app: Flask, client: testing.FlaskClient, auth: AuthAction):
    """コメント削除エラー（コメント投稿者と異なるユーザー）のテスト"""
    with app.app_context():
        db = get_db()
        db.execute('UPDATE comment SET commenter_id = 2 WHERE id = 1')
        db.commit()

    auth.login()

    res = client.post('/1/comment/1/delete')
    assert b'permission to delete.' in res.data


def test_comment_delete(app: Flask, client: testing.FlaskClient, auth: AuthAction):
    """コメント削除のテスト"""
    auth.login()
    res = client.post('/1/comment/1/delete')
    assert res.headers['Location'] == '/1'

    with app.app_context():
        db = get_db()
        comment = db.execute('SELECT * FROM comment WHERE id = 1').fetchone()
        assert comment is None
