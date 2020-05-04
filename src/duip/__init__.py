from pathlib import Path

from flask import Flask

from .command import command_endpoints
from .node import node_endpoints

__version__ = "0.1.0"


def create_app(test_config=None):
    app = Flask(__name__)
    # Other tut stuff
    # app.config.from_mapping(
    #     SECRET_KEY="dev",
    # )

    # Make it easier to inject custom configs on tests
    if test_config is not None:
        app.config.from_mapping(test_config)
    # else:
    #     app.config.from_pyfile("config.py", silent=True)

    # Ensure the instance folder ... exists
    # We might want to use this for DUI data files?
    Path(app.instance_path).mkdir(exist_ok=True)
    app.logger.info(f"Instance path: {app.instance_path}")

    app.register_blueprint(node_endpoints, url_prefix="/node")
    app.register_blueprint(command_endpoints, url_prefix="/command")

    return app
