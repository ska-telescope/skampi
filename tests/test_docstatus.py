#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the ska_python_skeleton module."""
# import pytest

from docstatus import GitLabRepo, Repository


# TODO: Replace all the following examples with tests for the ska_python_skeleton package code
def test_something():
    """Example: Assert with no defined return value."""
    assert True


def test_docs_exist():
    """Check if docs folders exist"""
    test_gl_repo_tmp = GitLabRepo("tmp", "me")
    test_gl_repo_1 = GitLabRepo("test1", "me")
    test_gl_repo_2 = GitLabRepo("test2", "me")

    test_repo_tmp = Repository(test_gl_repo_tmp.name, gitlab_repo=test_gl_repo_tmp)
    test_repo_tmp.set_folder_exists()
    test_repo_1 = Repository(test_gl_repo_1.name, gitlab_repo=test_gl_repo_1)
    test_repo_1.set_folder_exists()
    test_repo_2 = Repository(test_gl_repo_2.name, gitlab_repo=test_gl_repo_2)
    test_repo_2.set_folder_exists()

    assert test_repo_tmp.docs_folder_exists is False
    assert test_repo_1.docs_folder_exists is False
    assert test_repo_2
