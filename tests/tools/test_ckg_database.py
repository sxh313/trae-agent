# Copyright (c) 2025 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

"""Tests for the Python class method signatures built by the CKG database."""

import unittest
from typing import override

from tree_sitter_languages import get_parser

from trae_agent.tools.ckg.base import ClassEntry, FunctionEntry
from trae_agent.tools.ckg.ckg_database import CKGDatabase

SAMPLE_CLASS = """
class Service:
    @property
    def readable(self) -> str:
        return "r"

    def plain(self, value: int) -> bool:
        return True

    @staticmethod
    def wrapped(name: str) -> list[str]:
        return [name]
"""


class _CollectingDatabase(CKGDatabase):
    """CKGDatabase that keeps visited entries in memory instead of writing sqlite."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        self.entries: list[ClassEntry | FunctionEntry] = []

    @override
    def _insert_entry(self, entry: FunctionEntry | ClassEntry) -> None:
        self.entries.append(entry)

    @override
    def __del__(self) -> None:
        pass


def _build_class(source: str) -> ClassEntry:
    database = _CollectingDatabase()
    tree = get_parser("python").parse(source.encode())
    database._recursive_visit_python(tree.root_node, "sample.py")
    classes = [entry for entry in database.entries if isinstance(entry, ClassEntry)]
    assert len(classes) == 1, f"expected one class, got {len(classes)}"
    return classes[0]


class TestPythonClassMethods(unittest.TestCase):
    def test_undecorated_method_keeps_return_type(self):
        methods = _build_class(SAMPLE_CLASS).methods
        self.assertIsNotNone(methods)
        self.assertIn("- plain(self, value: int) -> bool", methods or "")

    def test_decorated_method_keeps_return_type(self):
        methods = _build_class(SAMPLE_CLASS).methods
        self.assertIsNotNone(methods)
        self.assertIn("- readable(self) -> str", methods or "")
        self.assertIn("- wrapped(name: str) -> list[str]", methods or "")


if __name__ == "__main__":
    unittest.main()
