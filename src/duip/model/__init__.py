from __future__ import annotations

import uuid
from enum import Enum, auto
from io import StringIO
from threading import Lock
from typing import Dict, List

import networkx as nx

NODE_TYPES = {}


class DuplicateKeyError(Exception):
    pass


def register_node(node_subclass):
    NODE_TYPES[node_subclass.__name__] = node_subclass
    return node_subclass


def _render_graph(stream, node: Node, indent: str = "", last=True, first=True):
    """Draw a textual representation of the node graph"""
    if first:
        first_i = ""
        second_i = ""
    elif last:
        first_i = "└─"
        second_i = "  "
    else:
        first_i = "├─"
        second_i = "│ "
    stream.write(indent + first_i + str(node) + "\n")
    indent = indent + second_i
    for i, child in enumerate(list(node.children)):
        _render_graph(
            stream,
            child,
            indent=indent,
            last=(i + 1) == len(node.children),
            first=False,
        )


class NodeState(Enum):
    def _generate_next_value_(name, start, count, last_values):  # pylint: disable=E0213
        return name

    UNCONFIRMED = auto()  # Client-side: We expect this but haven't gotten confirmation
    CREATED = auto()  # Node exists but not confirmed running
    RUNNING = auto()  # Node is currently in progress
    FAILED = auto()  # Node ran but failed for some reason
    SUCCESS = auto()  # Node ran successfully


@register_node
class Node:
    """
    Generic object representing a single processing step.

    Node can have several parents.

    Args:
        tree: The DUI tree object this belongs to
        parents: List of parent nodes
        node_id: The tree-ID node, if known. If this is duplicate in the
            context of the tree, an exception will be thrown
        node_uuid: The UUID for this node. Will be generated if unspecified
    """

    def __init__(
        self,
        tree: DUITree,
        parents: List[Node] = None,
        node_id: str = None,
        node_uuid: str = None,
    ):
        self.tree = tree
        self.parents = list(parents or [])
        self.id = str(node_id) if node_id is not None else None
        self.uuid = node_uuid or uuid.uuid4().hex
        self.children = []
        self.state = NodeState.CREATED

        tree.add_node(self)

    # def attach_to(self, tree: DUITree, parents: List[Node]):
    #     """
    #     Attach this node to a node tree

    #     Args:
    #         tree: The tree object to attach to
    #         parents: The list of parent nodes in that tree
    #         node_id: The tree-local ID to use for the node
    #     """
    #     assert node_id, "Node ID must have value"
    #     assert node_id not in tree.nodes, f"Tree already has a node with id {node_id}"

    #     self.tree = tree
    #     tree.nodes[node_id] = self

    #     # synchronize the children pointers
    #     self.parents = list(parents)
    #     for parent in parents:
    #         assert (
    #             self not in parent.children
    #         ), "Parent already has this node as a child"
    #         parent.children.append(self)

    def as_dict(self):
        """Convert this node to a plain literal representation"""
        return {
            "type": type(self).__name__,
            "id": self._id,
            "uuid": self.uuid,
            "parents": [p.id for p in self.parents],
            "state": self.state.value,
        }

    @classmethod
    def from_dict(cls, tree: DUITree, data: Dict):
        """Recreate a node from it's dict literal description"""
        # Not perfect, as race condition, but checks dev environment
        # Problem is: This might be a superclass in which case subclass
        # might want to alter, after creation. At the moment we don't
        # anticipate loading from dict that often though.
        assert tree._lock.locked()

        node_id = data["id"]
        node_uuid = data["uuid"]
        # DAG, so we can assume that parents are made before children
        parents = [tree[parent_id] for parent_id in data.get("parents", [])]
        # The constructor recreates all the links
        node = cls(node_uuid)
        node.attach_to(tree, parents, node_id)
        node.state = NodeState(data["STATE"])

        return node

    def __str__(self):
        return f"Node {self.id}"


class DUITree:
    """Object coordinating the DUI DAG node graph"""

    def __init__(self):
        self._next_id = 1
        self.nodes = {}
        self._lock = Lock()
        self._roots = []

    def add_node(self, node: Node):
        # Validate first before changing anything
        if node.id in self.nodes:
            raise DuplicateKeyError(f"Node id {node.id} already exists in tree")
        if any(x.uuid == node.uuid for x in self.nodes.values()):
            raise DuplicateKeyError(f"Duplicate UUID: {node.uuid}")
        for parent in node.parents:
            if parent.id not in self.nodes:
                raise KeyError(f"Parent with ID {parent.id} not a member of tree")
            if self.nodes[parent.id] is not parent:
                raise ValueError(
                    f"Parent with ID {parent.id} is different to existing object"
                )
            if node in parent.children:
                raise RuntimeError(
                    "Node already exists in parent children list... bad tree"
                )

        with self._lock:
            # Check that the UUID doesn't already exist
            # Generate or use the node ID
            if node.id is None:
                node.id = str(self._next_id)
                self._next_id += 1
            self.nodes[node.id] = node
            # Wire up the parent links
            for parent in node.parents:
                parent.children.append(node)
            # Track roots
            if not node.parents:
                self._roots.append(node)

    def as_dict(self):
        return {node_id: node.as_dict() for node_id, node in self.nodes.items()}

    @classmethod
    def from_dict(self, data):
        all_nodes = {}
        # Determine construction order
        graph = nx.DiGraph()
        for node_data in data:
            node_id = node_data["id"]
            all_nodes[node_id] = node_data
            graph.add_node(node_id)
            for parent in node_data.get("parents", []):
                graph.add_edge(node_id, parent)
        assert nx.is_directed_acyclic_graph(graph), "Node graph non-DAG"
        node_order = list(reversed(list(nx.topological_sort(graph))))
        # Now sorted, safe to create
        tree = DUITree()
        for node_id in node_order:
            node_type = all_nodes[node_id].get("type", "Node")
            assert node_type in NODE_TYPES
            tree.nodes[node_id] = NODE_TYPES[node_type].from_dict(
                tree, all_nodes[node_id]
            )

    def render_graph(self):
        """Generate an Unicode graph showing the tree structure"""
        # Find the root nodes
        dest = StringIO()

        class FakeRoot:
            def __str__(self):
                return ""

        root = FakeRoot()
        root.children = [x for x in self.nodes.values() if not x.parents]
        # for root in roots:
        _render_graph(dest, root)
        return dest.getvalue()
