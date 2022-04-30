import os
import tempfile

from flask import Flask, testing
import pytest

from flaskr import create_app
from flaskr.db import get_db, init_db


# テストデータを読み込み
with open(os.path.join(os.path.dirname(__file__), 'data.sql'), 'rb') as f:
    _data_sql = f.read().decode('utf-8')


@pytest.fixture
def app():
    # 一時ファイルの作成
    db_fd, db_path = tempfile.mkstemp()

    # アプリケーションのインスタンスを作成（テストモード）
    app = create_app({
        'TESTING': True,
        'DATABASE': db_path,
    })

    with app.app_context():
        init_db()
        get_db().executescript(_data_sql)

    # アプリケーションを返して待機（テストを開始する）
    yield app

    # テストが終わって処理が戻ったら一時ファイルの後始末する
    os.close(db_fd)
    os.unlink(db_path)


# テストモードのアプリケーションからサーバーに接続せずにリクエストを作成
@pytest.fixture
def client(app: Flask):
    return app.test_client()


# アプリケーションに登録されているカスタムコマンドを実行可能にする
@pytest.fixture
def runner(app: Flask):
    return app.test_cli_runner()


# ログイン・ログアウトを簡単に行うためのクラス
class AuthAction(object):
    def __init__(self, client: testing.FlaskClient) -> None:
        self._client = client

    def login(self, username='test', password='test'):
        return self._client.post(
            '/auth/login',
            data={'username': username, 'password': password}
        )

    def logout(self):
        return self._client.get('/auth/logout')


# ログイン・ログアウトのフィクスチャ
@pytest.fixture
def auth(client: testing.FlaskClient):
    return AuthAction(client)
