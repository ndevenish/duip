"""
Command implementations, registration and views
"""

from __future__ import annotations

import logging
from typing import Dict

from flask import Blueprint, abort, jsonify, request, url_for

logger = logging.getLogger(__name__)

# Global list of registered commands
COMMANDS: Dict[str, Command] = {}


class Command:
    """
    Central class for a command.

    A command is something that will manages the parameters, validates,
    and creates a new node given parent(s) in the DUI tree.

    Attributes:
        name: The name of the command, what is sent to the client and
            what is used for the endpoint
    """

    name: str

    def __init__(self, name: str, description=None):
        self.name = name
        self.description = description or ""

    def to_dict(self) -> Dict:
        data = {
            "name": self.name,
            "endpoint": url_for(".command_named", name=self.name),
        }
        if self.description:
            data["description"] = self.description
        return data


def register_command(command: Command) -> None:
    """Register a command class"""
    global COMMANDS
    assert command.name not in COMMANDS
    COMMANDS[command.name] = command


command_endpoints = Blueprint("commands", __name__)


def init_commands(dials_bin=None):
    """
    Read a dials bin dir and extract command information for each command
    """
    global COMMANDS
    COMMANDS = {}
    register_command(Command("dials.import"))
    register_command(Command("dials.find_spots"))
    register_command(Command("dials.refine"))
    register_command(Command("dials.refine_bravais_settings"))
    register_command(Command("dials.reindex"))
    register_command(Command("dials.integrate"))
    register_command(Command("dials.symmetry"))
    register_command(Command("dials.scale"))
    register_command(Command("export"))
    register_command(Command("mask", description="Generate and apply a mask"))


@command_endpoints.route("/", strict_slashes=False)
def all_commands():
    if request.args.get("node", None):
        # Given a node. Return valid commands for this node.
        logger.warn("Per-node command lists not currently implemented")
    return jsonify({name: url_for(".command_named", name=name) for name in COMMANDS})


@command_endpoints.route("/<name>")
def command_named(name):
    if name not in COMMANDS:
        abort(404)
    command = COMMANDS[name]
    return command.to_dict()
