import sqlite3

import click
from flask import current_app, g
from flask.cli import with_appcontext


# データベースに接続する
# 同じリクエスト中にすでに接続している場合は接続しているDBを返す
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db


# データベースの接続を閉じる
def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


# データベースを初期化
# テーブル定義とビュー定義データの読み込みと実行
def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


# 開発用の初期データの読み込みと実行
def insert_init_data():
    db = get_db()

    with current_app.open_resource('initdata.sql') as f:
        db.executescript(f.read().decode('utf8'))


# カスタムコマンドの定義
# シェルから flask init-db を実行可能にする
@click.command('init-db')
@with_appcontext
def init_db_command():
    init_db()
    click.echo('Initialized the database.')


# 開発用初期データの挿入も含んだカスタムコマンドの定義
@click.command('init-db-data')
@with_appcontext
def init_db_data_command():
    init_db()
    insert_init_data()
    click.echo('Initialized the database and insert initial data.')


# カスタムコマンドをアプリケーション（のインスタンス）に登録する関数
# アプリケーションのインスタンスに対して設定する
def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(init_db_data_command)