import sqlite3

from flask import Flask, testing
import pytest

from flaskr.db import get_db


def test_get_close_db(app: Flask):
    """get_db()のテスト"""
    # 同じコンテキスト内ではget_db()は常に同じ接続を返す
    with app.app_context():
        db = get_db()
        assert db is get_db()

    # pytest.raises(exception)  異常系のテスト
    # sqlite3にエラーが生じた時、出力されるエラーの文言に'closed'が含まれている
    with pytest.raises(sqlite3.ProgrammingError) as e:
        db.execute('SELECT 1')
    assert 'closed' in str(e.value)


def test_init_db_command(runner: testing.FlaskCliRunner, monkeypatch: pytest.MonkeyPatch):
    """init-dbコマンドのテスト"""
    # 差し替え用のクラスの作成
    class Recorder(object):
        called = False

    # init_db()の実行時に差し替える関数
    def fake_init_db():
        Recorder.called = True

    # init-db()を差し替えた上でinit-dbコマンドを走らせる
    monkeypatch.setattr('flaskr.db.init_db', fake_init_db)
    result = runner.invoke(args=['init-db'])
    assert 'Initialized' in result.output
    assert Recorder.called
