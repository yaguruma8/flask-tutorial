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
        'SELECT p.id, p.title, p.body, p.created, p.author_id, u.username, COALESCE(c.cnt, 0) AS comment_count '
        ' FROM post AS p '
        ' INNER JOIN user AS u '
        ' ON p.author_id = u.id '
        ' LEFT OUTER JOIN (SELECT post_id, count(*) AS cnt FROM comment GROUP BY post_id) AS c '
        ' ON p.id = c.post_id '
        ' ORDER BY p.created DESC; '
    ).fetchall()
    return render_template('blog/index.html', posts=posts)


# blog.article  /<int:id>  記事の詳細の表示
@bp.get('/<int:id>')
def article(id: int):
    post = get_post(id, check_author=False)
    comments = get_comments(id)
    vote = get_vote(id)
    vote_result = get_db().execute(
        'SELECT '
        ' COALESCE(SUM(CASE WHEN intention = 1 THEN 1 ELSE 0 END), 0) AS agree, '
        ' COALESCE(SUM(CASE WHEN intention = 0 THEN 1 ELSE 0 END), 0) AS disagree '
        ' FROM vote '
        ' WHERE post_id = ? ',
        (id,)
    ).fetchone()

    return render_template('blog/article.html',
                           post=post, comments=comments, vote=vote, vote_result=vote_result)


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


# blog.comment_create_post /<int:id>/comment/create コメントを書き込む　ログイン要
@bp.post('/<int:id>/comment/create')
@login_required
def comment_create_post(id: int):
    """記事にコメントを登録する"""

    body = request.form['body']
    error = None

    if not body:
        error = 'comment is empty.'
    elif len(body) > 40:
        error = 'comment is too long.'

    if error is None:
        db = get_db()
        db.execute(
            'INSERT INTO comment (post_id, commenter_id, body) '
            ' VALUES (?, ?, ?);',
            (id, g.user['id'], body)
        )
        db.commit()
        return redirect(url_for('blog.article', id=id))
    else:
        flash(error)
        return article(id)


# blog.comment_delete_post  /<int:id>/comment/<int:comment_id>/delete コメントを削除する　ログイン要
@bp.post('/<int:id>/comment/<int:comment_id>/delete')
@login_required
def comment_delete_post(id: int, comment_id: int):
    """指定したコメントIDのコメントを削除する"""

    db = get_db()
    comment = db.execute(
        'SELECT post_id, commenter_id FROM comment WHERE id = ? ; ',
        (comment_id,)
    ).fetchone()
    error = None

    if comment is None:
        error = 'comment is not exist.'
    elif comment['post_id'] != id:
        error = 'defferent post.'
    elif comment['commenter_id'] != g.user['id']:
        error = 'don\'t have permission to delete.'

    if error is None:
        db.execute(
            'DELETE FROM comment WHERE id = ?;',
            (comment_id,)
        )
        db.commit()
        return redirect(url_for('blog.article', id=id))
    else:
        flash(error)
        return article(id)


@bp.post('/<int:id>/vote')
@login_required
def vote_post(id: int):
    """投票をデータベースに登録する"""
    intention = int(request.form['intention'])
    print(intention)
    vote = get_vote(id)
    error = None

    # バリデーション
    if vote is not None:
        error = 'you are already vote.'
    if intention < 0 or intention > 1:
        error = 'illegal value.'

    if error is None:
        db = get_db()
        db.execute(
            'INSERT INTO vote (post_id, user_id, intention) VALUES (?, ?, ?);',
            (id, g.user['id'], intention)
        )
        db.commit()
        return redirect(url_for('blog.article', id=id))
    else:
        flash(error)
        return article(id)


@bp.post('/<int:id>/vote/cancel')
@login_required
def vote_cancel_post(id: int):
    """投票を取り消す（DBから削除する）"""
    vote = get_vote(id)
    print('取り消しされました')
    return redirect(url_for('blog.article', id=id))


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


def get_comments(post_id: int) -> list:
    """指定したidの投稿へのコメントを新しい順で取得する"""

    comments = get_db().execute(
        'SELECT c.id, c.post_id, c.commenter_id, c.created, c.body, u.username '
        ' FROM comment AS c '
        ' INNER JOIN user AS u '
        ' ON c.commenter_id = u.id '
        ' WHERE c.post_id = ? '
        ' ORDER BY c.created DESC; ',
        (post_id,)
    ).fetchall()

    return comments


def get_vote(post_id: int):
    """指定したidの投稿への投票を取得する"""
    vote = get_db().execute(
        'SELECT * FROM vote '
        ' WHERE post_id = ? AND user_id = ?',
        (post_id, g.user['id'])
    ).fetchone()

    return vote
