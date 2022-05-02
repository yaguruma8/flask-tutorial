import functools

from flask import Blueprint, flash, redirect, request, url_for, session, g, render_template
from werkzeug.security import generate_password_hash, check_password_hash

from flaskr.db import get_db


bp = Blueprint('auth', __name__)


# 登録 '/auth/register' の処理を行う関数を登録
@bp.get('/register')
def register():
    return render_template('auth/register.html')


@bp.post('/register')
def register_post():
    username = request.form['username']
    password = request.form['password']
    db = get_db()
    error = None

    # バリデーション
    if not username:
        error = 'Username is required.'
    elif not password:
        error = 'Password is required.'
    elif db.execute(
        'SELECT id FROM user WHERE username = ?', (username,)
    ).fetchone() is not None:
        error = f"User {username} is already registerd."

    if error is None:
        db.execute(
            'INSERT INTO user (username, password) VALUES (?, ?)',
            (username, generate_password_hash(password))
        )
        db.commit()
        return redirect(url_for('auth.login'))
    else:
        flash(error)
        return register()


# ログイン '/auth/login'を登録する
@bp.get('/login')
def login():
    return render_template('auth/login.html')


@bp.post('/login')
def login_post():
    username = request.form['username']
    password = request.form['password']
    db = get_db()
    error = None
    user = db.execute(
        'SELECT * FROM user WHERE username = ?', (username,)
    ).fetchone()

    # バリデーション
    if user is None:
        error = 'Incorrect username.'
    elif not check_password_hash(user['password'], password):
        error = 'Incorrect password.'

    if error is None:
        session.clear()
        session['user-id'] = user['id']
        return redirect(url_for('blog.index'))
    else:
        flash(error)
        return login()


# ログアウト '/auth/logout'
@bp.get('/logout')
def logout():
    session.clear()
    return redirect(url_for('blog.index'))


# リクエストがあったときにビューの関数よりも前に実行する関数を登録する
@bp.before_app_request
def load_logged_in_user():
    # セッションを調べる
    user_id = session.get('user-id')

    if user_id is None:
        # セッションに登録されていなければNoneを格納する
        g.user = None
    else:
        # セッションに登録されていればユーザーが存在するのでSQLでユーザー情報を取り出して
        # g（リクエスト中に複数の関数からアクセスできる特別なオブジェクト）に格納する
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()


# 他のviewでの認証の要求
# ラップしたviewを返し、そのラップの中でログインしているかを調べる
# g.user がNone＝ログインしていない ので、auth.loginにリダイレクトする
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(*args, **kwargs)

    return wrapped_view
