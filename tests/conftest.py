"""
Basic fixtures for setting up an app
"""
import pytest
from duip import create_app
from duip.node import init_tree


@pytest.fixture
def app(tmp_path):
    app = create_app({"TESTING": True,})

    with app.app_context():
        init_tree()

    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def test_req(client):
    assert b"Hello, world" in client.get("/").data
