import pytest


def pytest_addoption(parser):
    parser.addoption("--pause", action="store_true",
                     help="Pauses the tests just before login and password "
                          "will be entered to the provider login page.")