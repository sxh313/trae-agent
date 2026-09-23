# Copyright (c) 2025 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

"""Tests that an edit leaves the bytes of every line it did not touch alone."""

import os
import tempfile
import unittest
from pathlib import Path

from trae_agent.tools.edit_tool import TextEditorTool


class TestLineEndingsSurviveAnEdit(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.tool = TextEditorTool()

    def _file(self, name: str, raw: bytes) -> Path:
        path = Path(self.tmp.name) / name
        path.write_bytes(raw)
        return path

    async def _edit(self, path: Path, **arguments: str) -> None:
        result = await self.tool.execute({"command": "str_replace", "path": str(path), **arguments})
        self.assertIsNone(result.error, result.error)

    async def test_a_replacement_rewrites_only_the_replaced_line(self):
        for terminator in (b"\n", b"\r\n", b"\r"):
            with self.subTest(terminator=terminator):
                lines = [b"a = 1", b"b = 2", b"c = 3"]
                path = self._file("replaced.py", terminator.join(lines) + terminator)

                await self._edit(path, old_str="b = 2", new_str="b = 20")

                expected = terminator.join([b"a = 1", b"b = 20", b"c = 3"]) + terminator
                self.assertEqual(path.read_bytes(), expected)

    async def test_an_insertion_rewrites_only_the_inserted_line(self):
        for terminator in (b"\n", b"\r\n"):
            with self.subTest(terminator=terminator):
                lines = [b"first", b"last"]
                path = self._file("inserted.txt", terminator.join(lines) + terminator)

                result = await self.tool.execute(
                    {
                        "command": "insert",
                        "path": str(path),
                        "insert_line": 1,
                        "new_str": "middle",
                    }
                )
                self.assertIsNone(result.error, result.error)

                expected = terminator.join([b"first", b"middle", b"last"]) + terminator
                self.assertEqual(path.read_bytes(), expected)

    async def test_a_file_that_mixes_terminators_keeps_its_most_common_one(self):
        path = self._file("mixed.txt", b"a = 1\r\nb = 2\nc = 3\r\n")

        await self._edit(path, old_str="b = 2", new_str="b = 20")

        self.assertEqual(path.read_bytes(), b"a = 1\r\nb = 20\r\nc = 3\r\n")

    async def test_a_created_file_still_uses_the_platform_default(self):
        """Nothing is there to preserve yet, so `create` is deliberately left alone."""
        path = Path(self.tmp.name) / "created.txt"

        result = await self.tool.execute(
            {"command": "create", "path": str(path), "file_text": "line one\nline two\n"}
        )
        self.assertIsNone(result.error, result.error)

        terminator = os.linesep.encode()
        self.assertEqual(path.read_bytes(), b"line one" + terminator + b"line two" + terminator)
