# Copyright (c) 2025 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

"""Tests for the ``remove`` operation of the standalone json_edit_tool CLI."""

import asyncio
import json
from pathlib import Path

from trae_agent.tools.json_edit_tool_cli import JSONEditTool


def run_remove(tmp_path: Path, payload: object, json_path: str):
    file_path = tmp_path / "data.json"
    file_path.write_text(json.dumps(payload), encoding="utf-8")
    result = asyncio.run(JSONEditTool()._remove_json_value(file_path, json_path, False))
    return result, json.loads(file_path.read_text(encoding="utf-8"))


def test_remove_array_element_only_deletes_the_match(tmp_path):
    result, data = run_remove(tmp_path, {"items": [10, 20, 30], "name": "keepme"}, "$.items[1]")

    assert result.error is None
    assert result.error_code == 0
    assert data == {"items": [10, 30], "name": "keepme"}


def test_remove_first_array_element_only_deletes_the_match(tmp_path):
    result, data = run_remove(tmp_path, {"items": [10, 20, 30]}, "$.items[0]")

    assert result.error is None
    assert result.error_code == 0
    assert data == {"items": [20, 30]}


def test_remove_nested_array_element_only_deletes_the_match(tmp_path):
    result, data = run_remove(
        tmp_path, {"servers": [{"name": "a", "tags": ["x", "y", "z"]}]}, "$.servers[0].tags[1]"
    )

    assert result.error is None
    assert result.error_code == 0
    assert data == {"servers": [{"name": "a", "tags": ["x", "z"]}]}
