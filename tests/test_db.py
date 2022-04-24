import sqlite3

from flask import Flask
import pytest

from flaskr.db import get_db


def test_get_close_db(app: Flask) -> None:
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