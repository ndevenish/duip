from flask import Flask

__version__ = "0.1.0"

app = Flask(__name__)


@app.route("/")
def hello():
    return "Hello, world"
