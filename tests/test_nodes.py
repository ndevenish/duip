from duip.model import Node
from duip.node import get_tree
from flask import json


def test_node_list(app, client):
    # Get a tree controller from the app
    with app.app_context():
        tree = get_tree()
        assert tree is get_tree()
        resp = client.get("/node/",)
        assert resp.status_code == 200
        assert json.loads(resp.data) == []

        base_node = tree.tree.attach(Node())
        resp = client.get("/node/")
        assert resp.status_code == 200
        one_node_list = json.loads(resp.data)
        assert one_node_list == [base_node.to_dict()]

        resp = client.get(f"/node/{base_node.id}")
        assert resp.status_code == 200
        reconstructed = json.loads(resp.data)
        assert reconstructed == base_node.to_dict()

        # Bad node returns 404
        resp = client.get(f"/node/424242")
        assert resp.status_code == 404
