import pytest
from duip.model import NODE_TYPES, DUITree, DuplicateKeyError, Node


def test_node_types():
    assert "Node" in NODE_TYPES


def test_node_creation_manipulation():
    tree = DUITree()
    nodeA = tree.attach(Node())
    assert nodeA.id
    assert nodeA in tree.nodes.values()
    nodeB = tree.attach(Node([nodeA]))
    assert nodeB.id != nodeA.id
    assert nodeB in nodeA.children
    assert nodeA in nodeB.parents
    # Try creating with duplicate id
    with pytest.raises(DuplicateKeyError):
        tree.attach(Node(node_id=nodeA.id))
    # And duplicate UUID...
    with pytest.raises(DuplicateKeyError):
        tree.attach(Node([], node_uuid=nodeA.uuid))

    node_other = Node(node_id="-424242")
    with pytest.raises(KeyError):
        tree.attach(Node(parents=[node_other]))

    tree.attach(Node([nodeA]))
    tree.attach(Node())
    print("\n" + tree.render_graph())
