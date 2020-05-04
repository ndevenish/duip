from duip.model import DUITree
from flask import abort, g, jsonify

from .routes import node_endpoints

# For now, store this globally on a per-process instance
# This isn't... a good way, but for now keeps the model super simple
_TREE = None


def init_tree():
    global _TREE
    _TREE = TreeController()


def get_tree():
    """Load the DUI tree controller onto the context, and return it."""
    assert _TREE
    if "tree" not in g:
        g.tree = _TREE
    return g.tree


class TreeController:
    """
    Interface between the app and the tree graph.

    By doing this in a separate object, we can allow for splitting the
    model out to a separate process in the future.
    """

    def __init__(self):
        self.tree = DUITree()

    def get_node(self, node_id):
        return self.tree.nodes[node_id]


@node_endpoints.route("/")
def all_nodes():
    tree = get_tree()
    return jsonify(tree.tree.to_dict())


@node_endpoints.route("/<node_id>")
def get_single_node(node_id):
    try:
        node = get_tree().get_node(node_id)
    except KeyError:
        abort(404)
    return node.to_dict()
