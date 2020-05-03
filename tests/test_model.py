import pytest
from duip.model import NODE_TYPES, DUITree, DuplicateKeyError, Node


def test_node_types():
    assert "Node" in NODE_TYPES


def test_node_creation_manipulation():
    tree = DUITree()
    nodeA = Node(tree, [])
    assert nodeA.id
    assert nodeA in tree.nodes.values()
    nodeB = Node(tree, [nodeA])
    assert nodeB.id != nodeA.id
    assert nodeB in nodeA.children
    assert nodeA in nodeB.parents
    # Try creating with duplicate id
    with pytest.raises(DuplicateKeyError):
        Node(tree, [], node_id="1")
    # And duplicate UUID...
    with pytest.raises(DuplicateKeyError):
        Node(tree, [], node_uuid=nodeA.uuid)

    tree2 = DUITree()
    node_other = Node(tree2, node_id="-424242")
    with pytest.raises(KeyError):
        Node(tree, [node_other])

    Node(tree, [nodeA])
    Node(tree, [])
    print("\n" + tree.render_graph())
