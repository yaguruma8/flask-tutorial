from flask import Blueprint, render_template, request, flash, g, redirect, url_for
from werkzeug.exceptions import abort

from flaskr.db import get_db
from flaskr.routes.auth import login_required

bp = Blueprint('blog', __name__)


# blog.index  /  ログインして最初に表示されるホーム
@bp.get('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('blog/index.html', posts=posts)


# blog.article  /<int:id>/article  記事の詳細の表示
@bp.get('/<int:id>/article')
def article(id: int):
    post = get_post(id, check_author=False)
    return render_template('blog/article.html', post=post)


# blog.create /create 記事の作成　ログイン要
@bp.get('/create')
@login_required
def create():
    return render_template('blog/create.html')


@bp.post('/create')
@login_required
def create_post():
    title = request.form['title']
    body = request.form['body']
    error = None

    # バリデーション
    if not title:
        error = 'Title is required.'

    if error is None:
        db = get_db()
        db.execute(
            'INSERT INTO post (title, body, author_id)'
            ' VALUES (?, ?, ?);',
            (title, body, g.user['id'])
        )
        db.commit()
        return redirect(url_for('blog.index'))
    else:
        flash(error)
        return create()


# blog.update  /<int:id>/update  記事を更新する　ログイン要
@bp.get('/<int:id>/update')
@login_required
def update(id: int):
    post = get_post(id)
    return render_template('blog/update.html', post=post)


@bp.post('/<int:id>/update')
@login_required
def update_post(id: int):
    get_post(id)
    title = request.form['title']
    body = request.form['body']
    error = None

    # バリデーション
    if not title:
        error = 'Title is required.'

    if error is None:
        db = get_db()
        db.execute(
            'UPDATE post SET title = ?, body = ?'
            ' WHERE id = ?',
            (title, body, id)
        )
        db.commit()
        return redirect(url_for('blog.index'))
    else:
        flash(error)
        return update(id)


# blog.delete /<int:id>/delete 記事を削除する　ログイン要
@bp.post('/<int:id>/delete')
@login_required
def delete_post(id: int):
    # アクセスが投稿者かどうか確認する（投稿者でなければ403）
    get_post(id)
    db = get_db()
    db.execute(
        'DELETE FROM post WHERE id = ?',
        (id,)
    )
    db.commit()
    return redirect(url_for('blog.index'))


# 指定したidのpostを取得する
def get_post(id: int, check_author: bool = True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f'Post id {id} doesn\'t exist.')

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post
