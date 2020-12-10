import logging
import os

from flask import Flask

from coursenotify import manager


def create_app():
    # create and configure the app
    app = Flask(__name__,
                instance_relative_config=True,
                static_folder="static/frontend/dist/",
                static_url_path="")
    app.app_context()

    env = os.environ.get("ENV")
    if env is None or env == "development":
        app.config.from_pyfile("dev/config.dev.py", silent=False)
    elif env == "production":
        app.config.from_pyfile("prod/config.prod.py")

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    # logging
    app.logger.setLevel(logging.INFO)

    with app.app_context():
        try:
            manager.check_db_connection()
        except Exception:
            app.logger.error("Fail to connect DB")
            return None

    if app.config["UPDATE_COLLECTION"]:
        with app.app_context():
            manager.init_course_db()

    # register blueprints
    from coursenotify.views.index import frontend
    from coursenotify.views.api import api
    app.register_blueprint(frontend)
    app.register_blueprint(api)

    return app
