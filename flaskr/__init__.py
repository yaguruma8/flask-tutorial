import os
from flask import Flask


# Flaskインスタンスを作成するファクトリ関数
def create_app(test_config=None):
    # アプリケーションのインスタンスを作成
    app = Flask(__name__, instance_relative_config=True)
    # 標準設定
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )
    # 標準設定の上書き
    if test_config is None:
        # インスタンスフォルダに設定ファイルがあれば上書きする（なければ何もしない）
        app.config.from_pyfile('config.py', silent=True)
    else:
        # テスト用の設定ファイルが渡ってきている場合はそれに従う
        app.config.from_mapping(test_config)
    # インスタンスディレクトリの存在確認（なければ作成する）
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # ルーティングの設定
    @app.route('/hello')
    def hello():
        return 'Hello, Flask!'

    # カスタムコマンドをアプリケーション（のインスタンス）に登録
    from . import db
    db.init_app(app)

    return app
