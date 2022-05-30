import os, re
from flask import Flask, Markup

from markdown2 import markdown


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

    # /authのブループリントをアプリケーションに登録
    from .routes import auth
    app.register_blueprint(auth.bp, url_prefix='/auth')

    # blogのブループリントをアプリケーションに登録
    from .routes import blog
    app.register_blueprint(blog.bp)
    app.add_url_rule('/', endpoint='index')

    # テンプレートのカスタムフィルターを登録
    @app.template_filter('markdown')
    def markdown_filter(str):
        return markdown(Markup.escape(str), extras=['tables'])

    @app.template_filter('remove_tag')
    def remove_tag_filter(str):
        return re.sub('<.+?>', ' ', str)

    return app
