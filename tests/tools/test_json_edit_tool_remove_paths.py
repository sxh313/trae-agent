# Copyright (c) 2025 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

"""Tests for the remove operation of JSONEditTool on paths that address the root's children."""

import json
import unittest
from unittest.mock import mock_open, patch

from trae_agent.tools.base import ToolCallArguments
from trae_agent.tools.json_edit_tool import JSONEditTool


class TestJSONEditToolRemoveRootChildPaths(unittest.IsolatedAsyncioTestCase):
    """`remove` has to delete any matched value from its parent container, including the root."""

    def setUp(self):
        """Set up the test environment."""
        self.tool = JSONEditTool()
        self.test_file_path = "/test_dir/test_file.json"

        self.sample_data = {
            "config": {"enabled": True, "version": "1.1.0"},
            "users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
            "count": 3,
        }

    def mock_file_read(self, json_data=None):
        """Helper to mock file reading operations."""
        if json_data is None:
            json_data = self.sample_data

        read_content = json.dumps(json_data)
        m_open = mock_open(read_data=read_content)

        # Patch open and path checks
        self.open_patcher = patch("builtins.open", m_open)
        self.exists_patcher = patch("pathlib.Path.exists", return_value=True)
        self.is_absolute_patcher = patch("pathlib.Path.is_absolute", return_value=True)

        self.open_patcher.start()
        self.exists_patcher.start()
        self.is_absolute_patcher.start()

    def tearDown(self):
        """Stop the file system patches."""
        self.open_patcher.stop()
        self.exists_patcher.stop()
        self.is_absolute_patcher.stop()

    async def _remove(self, json_path: str) -> tuple[int, str | None, str | None]:
        """Run the remove operation and return (error_code, error, output)."""
        self.mock_file_read()
        result = await self.tool.execute(
            ToolCallArguments(
                {
                    "operation": "remove",
                    "file_path": self.test_file_path,
                    "json_path": json_path,
                }
            )
        )
        assert result.error_code is not None
        return result.error_code, result.error, result.output

    @patch("json.dump")
    async def test_remove_top_level_object_key(self, mock_json_dump):
        """Removing an object that sits directly under the root must work."""
        error_code, error, _ = await self._remove("$.config")

        self.assertEqual(error_code, 0)
        self.assertIsNone(error)
        written_data = mock_json_dump.call_args[0][0]
        self.assertNotIn("config", written_data)
        self.assertIn("users", written_data)

    @patch("json.dump")
    async def test_remove_top_level_scalar_key(self, mock_json_dump):
        """Removing a scalar directly under the root must work too."""
        error_code, error, _ = await self._remove("$.count")

        self.assertEqual(error_code, 0)
        self.assertIsNone(error)
        written_data = mock_json_dump.call_args[0][0]
        self.assertNotIn("count", written_data)

    @patch("json.dump")
    async def test_remove_top_level_key_with_bracket_notation(self, mock_json_dump):
        """The bracket form of a root child is the same location and must behave the same."""
        error_code, error, _ = await self._remove("$['config']")

        self.assertEqual(error_code, 0)
        self.assertIsNone(error)
        written_data = mock_json_dump.call_args[0][0]
        self.assertNotIn("config", written_data)

    @patch("json.dump")
    async def test_remove_all_top_level_keys_with_wildcard(self, mock_json_dump):
        """`$.*` selects every value under the root, so all of them must be removed."""
        error_code, error, _ = await self._remove("$.*")

        self.assertEqual(error_code, 0)
        self.assertIsNone(error)
        written_data = mock_json_dump.call_args[0][0]
        self.assertEqual(written_data, {})

    @patch("json.dump")
    async def test_remove_document_root_is_reported_as_invalid(self, mock_json_dump):
        """The root has no parent to delete it from, which must be stated as a config-free error."""
        error_code, error, _ = await self._remove("$")

        self.assertEqual(error_code, -1)
        self.assertIsNotNone(error)
        assert error is not None
        self.assertIn("root", error.lower())
        self.assertNotIn("attribute", error)
        mock_json_dump.assert_not_called()

    @patch("json.dump")
    async def test_remove_nested_key_still_works(self, mock_json_dump):
        """Guards the already working multi segment path against this change."""
        error_code, error, _ = await self._remove("$.config.enabled")

        self.assertEqual(error_code, 0)
        self.assertIsNone(error)
        written_data = mock_json_dump.call_args[0][0]
        self.assertNotIn("enabled", written_data["config"])
        self.assertEqual(written_data["config"]["version"], "1.1.0")

    @patch("json.dump")
    async def test_remove_array_element_still_works(self, mock_json_dump):
        """Guards the already working array index path against this change."""
        error_code, error, _ = await self._remove("$.users[0]")

        self.assertEqual(error_code, 0)
        self.assertIsNone(error)
        written_data = mock_json_dump.call_args[0][0]
        self.assertEqual(len(written_data["users"]), 1)
        self.assertEqual(written_data["users"][0]["name"], "Bob")

    @patch("json.dump")
    async def test_remove_matches_only_their_own_parent_still_works(self, mock_json_dump):
        """Guards recursive descent, which resolves to several different parents, against this change."""
        error_code, error, _ = await self._remove("$..name")

        self.assertEqual(error_code, 0)
        self.assertIsNone(error)
        written_data = mock_json_dump.call_args[0][0]
        self.assertEqual(list(written_data["users"]), [{"id": 1}, {"id": 2}])


if __name__ == "__main__":
    unittest.main()
