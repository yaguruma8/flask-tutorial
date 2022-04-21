import os
import tempfile

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
def client(app):
    return app.test_client()


# アプリケーションに登録されているカスタムコマンドを実行可能にする
@pytest.fixture
def runner(app):
    return app.test_cli_runner()
