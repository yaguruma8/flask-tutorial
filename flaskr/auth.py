import functools

from flask import Blueprint, flash, redirect, request, url_for, session, g, render_template
from werkzeug.security import generate_password_hash, check_password_hash

from flaskr.db import get_db


bp = Blueprint('auth', __name__, url_prefix='/auth')


# 登録 '/auth/register' の処理を行う関数を登録
@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            # ユーザー名の欄が空
            error = 'Username is required.'
        elif not password:
            # パスワード欄が空
            error = 'Password is required.'
        elif db.execute(
            'SELECT id FROM user WHERE username = ?', (username,)
        ).fetchone() is not None:
            # すでに登録されているユーザー名
            error = f"User {username} is already registerd."

        # エラーが出なければ登録してログイン画面へ
        if error is None:
            db.execute(
                'INSERT INTO user (username, password) VALUES (?, ?)',
                (username, generate_password_hash(password))
            )
            db.commit()
            return redirect(url_for('auth.login'))
        # エラーがあればフラッシュで表示して
        flash(error)
    # 登録画面に戻る（GETの場合はここだけ実行）
    return render_template('auth/register.html')


# ログイン '/auth/login'を登録する
@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()
        if user is None:
            # ユーザー名が未登録
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            # パスワードが正しくない
            error = 'Incorrect password.'

        if error is None:
            # エラーがなければセッションに登録してトップページにリダイレクト
            session.clear()
            session['user-id'] = user['id']
            return redirect(url_for('index'))

        # エラーがある場合はフラッシュ表示して
        flash(error)
    # ログイン画面に戻る（GETの場合はここだけ実行）
    return render_template('auth/login.html')


# ログアウト '/auth/logout'
@bp.route('/logout')
def logout():
    session.clear()
    return 'auth/logout'


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
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view
