# DUI+

![Python 3.6+](https://img.shields.io/badge/Python-3.6%2B-blue)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)

Toy reimplementation of some of the DUI/idials basic model as a flask-based
server application.

This is currently (for simplicity of matching models and to avoid too large a
knowledge gap) designed as a single-instance server application, and works with
the active model in memory rather than abstracted out to a database or similar.
This should be developed with the expectation that this might change in the
future.
