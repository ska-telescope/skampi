# -*- coding: utf-8 -*-

"""Tests for the ska_python_skeleton module."""
import pytest

from docstatus.docstatus import *
from readthedocs import *


# TODO: Replace all the following examples with tests for the ska_python_skeleton package code
def test_something():
    """Example: Assert with no defined return value."""
    assert True


# def test_docs_exist():
#     """Check if docs folders exist"""
#     test_gl_repo_tmp = GitLabRepo("tmp", "me", "")
#     test_gl_repo_1 = GitLabRepo("test1", "me", "")
#     test_gl_repo_2 = GitLabRepo("test2", "me", "")
#
#     test_repo_tmp = Repository(test_gl_repo_tmp.name, gitlab_repo=test_gl_repo_tmp)
#     test_repo_tmp.set_folder_exists()
#     test_repo_1 = Repository(test_gl_repo_1.name, gitlab_repo=test_gl_repo_1)
#     test_repo_1.set_folder_exists()
#     test_repo_2 = Repository(test_gl_repo_2.name, gitlab_repo=test_gl_repo_2)
#     test_repo_2.set_folder_exists()
#
#     assert test_repo_tmp.docs_folder_exists is False
#     assert test_repo_1.docs_folder_exists is False
#     assert test_repo_2


def test_google_sheet_access():
    sheet1 = google_sheet(0)
    print(sheet1.acell('A1').value)
    assert sheet1.acell('A1').value == "Name"


def test_second_sheet():
    sheet2 = google_sheet(1)
    assert sheet2.acell('A1').value == "Reponame"


def test_connect_readthedocs():
    """Check if connection to RTD works"""
    rtd = ReadtheDocs()
    assert rtd.base().json()['projects'] == 'https://readthedocs.org/api/v3/projects/'


def test_set_users():

