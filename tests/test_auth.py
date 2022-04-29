import pytest
from flask import testing, Flask

from flaskr.db import get_db


def test_register(client: testing.FlaskClient, app: Flask):
    assert client.get('/auth/register').status_code == 200
    res = client.post('/auth/register',
                      data={'username': 'a', 'password': 'a'})
    assert res.headers['Location'] in '/auth/login'
    assert res.status_code == 302

    with app.app_context():
        assert get_db().execute(
            "SELECT * FROM user WHERE username='a'"
        ).fetchone() is not None


# 同じテスト用関数を違う引数で走らせる
@pytest.mark.parametrize(('username', 'password', 'message'), (
                         ('', '', b'Username is required.'),
                         ('a', '', b'Password is required.'),
                         ('test', 'test', b'already registerd.')
                         ))
def test_register_validate(client: testing.FlaskClient, username, password, message):
    res = client.post('/auth/register',
                      data={'username': username, 'password': password})
    assert message in res.data
