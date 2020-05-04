"""
Command implementations, registration and views
"""

from flask import Blueprint, jsonify, url_for


class Command:
    """
    Central class for a command.

    A command is something that creates a new node given parent(s) in
    the DUI tree.

    Attributes:

    """

    name: str


COMMANDS = {}

command_endpoints = Blueprint("commands", __name__)


@command_endpoints.route("/")
def all_commands():
    return jsonify({name: url_for(".command_named", name=name) for name in COMMANDS})


@command_endpoints.route("/<name>")
def command_named(name):
    pass
