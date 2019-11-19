# -*- coding: utf-8 -*-

"""Tests for the ska_python_skeleton module."""
import pytest

from docstatus.docstatus import *
from readthedocs.readthedocs import *


# TODO: Replace all the following examples with tests for the ska_python_skeleton package code
def test_something():
    """Example: Assert with no defined return value."""
    assert True


def test_readthedocs_connection():
    rtd = ReadtheDocs()
    assert rtd.base() is 200

