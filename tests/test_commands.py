from duip import command
from flask import json


class FakeCommand(command.Command):
    name = "fake_command"


def test_node_list(client, monkeypatch):
    monkeypatch.setattr(command, "COMMANDS", {"fake_command": FakeCommand})
    # Get a tree controller from the app
    resp = client.get("/command/")
    assert resp.status_code == 200
    assert json.loads(resp.data) == {"fake_command": "/command/fake_command"}
