from __future__ import annotations

import uuid
from enum import Enum, auto
from io import StringIO
from threading import Lock
from typing import Dict, List, Optional, Sequence, Union

import networkx as nx

NODE_TYPES = {}


class DuplicateKeyError(Exception):
    pass


def register_node(node_subclass):
    """Decorator to register a node subclass"""
    NODE_TYPES[node_subclass.__name__] = node_subclass
    return node_subclass


def _render_graph(stream, node: Node, indent: str = "", last=True, first=True):
    """Draw a textual representation of the node graph"""
    if first:
        first_i = ""
        second_i = ""
    elif last:
        first_i = "╰─"
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
        parents: Either a parent node, or a list of parent nodes
        node_id: The tree-ID node, if known. If this is duplicate in the
            context of the tree, an exception will be thrown
        node_uuid: The UUID for this node. Will be generated if unspecified
        tree: The DUI tree object this will belong to
    """

    def __init__(
        self,
        parents: Union[Sequence[Node], Node] = None,
        *,
        node_id: str = None,
        node_uuid: str = None,
    ):
        self.tree: Optional[DUITree] = None
        # Handle non-list parents
        if parents is not None:
            if isinstance(parents, Sequence):
                self.parents = list(parents)
            else:
                self.parents = [parents]
        else:
            self.parents = []
        self.id = str(node_id) if node_id is not None else None
        self.uuid = node_uuid or uuid.uuid4().hex
        self._children: List[Node] = []
        self.state = NodeState.CREATED

    @property
    def children(self):
        return tuple(self._children)

    def to_dict(self):
        """Convert this node to a plain literal representation"""
        out = {
            "type": type(self).__name__,
            "id": self.id,
            "uuid": self.uuid,
            "state": self.state.value,
        }
        if self.parents:
            out["parents"] = [p.id for p in self.parents]
        return out

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
        parents = [tree.nodes[parent_id] for parent_id in data.get("parents", [])]
        # The constructor recreates all the links
        node = cls(parents=parents, node_id=node_id, node_uuid=node_uuid)
        node.state = NodeState(data["STATE"])
        tree.attach(node)

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

    def attach(self, node: Node) -> Node:
        """Attach a Node to this tree.

        If it has an .id, it will be used, if it doesn't already exist,
        otherwise it will have one assigned.

        Returns the node.
        """
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
            node.tree = self
            self.nodes[node.id] = node
            # Wire up the parent links
            for parent in node.parents:
                parent._children.append(node)
            # Track roots
            if not node.parents:
                self._roots.append(node)

        return node

    def to_dict(self):
        return [node.to_dict() for node_id, node in self.nodes.items()]

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
