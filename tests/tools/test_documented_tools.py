# Copyright (c) 2025 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

"""Keeps docs/tools.md and the agent configuration names aligned with the tool registry."""

import re
import unittest
from pathlib import Path

from trae_agent.tools import get_tool_class, tools_registry

DOCS_PATH = Path(__file__).resolve().parents[2] / "docs" / "tools.md"


def documented_tool_names() -> list[str]:
    return re.findall(r"^## (.+)$", DOCS_PATH.read_text(encoding="utf-8"), flags=re.MULTILINE)


class TestDocumentedTools(unittest.TestCase):
    def test_every_documented_tool_exists(self):
        undocumented = [name for name in documented_tool_names() if name not in tools_registry]
        self.assertEqual(
            undocumented,
            [],
            "docs/tools.md documents tool names that cannot be used in a configuration",
        )

    def test_every_registered_tool_is_documented(self):
        missing = sorted(set(tools_registry) - set(documented_tool_names()))
        self.assertEqual(
            missing,
            [],
            "tools that can be listed under `tools:` in trae_config.yaml have no docs/tools.md "
            "section, so users cannot find their name or parameters",
        )

    def test_documented_tool_count_is_current(self):
        claimed = re.search(r"provides (\w+) built-in tools", DOCS_PATH.read_text("utf-8"))
        self.assertIsNotNone(claimed, "docs/tools.md no longer states how many tools it lists")
        words_to_numbers = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6}
        self.assertEqual(
            words_to_numbers[claimed.group(1)],
            len(tools_registry),
            "the tool count sentence in docs/tools.md drifted from tools_registry",
        )


class TestUnknownToolName(unittest.TestCase):
    def test_unknown_tool_names_the_tool_and_lists_valid_ones(self):
        # `sequential_thinking` is the spelling docs/tools.md used before this test existed;
        # the registry key has never had the underscore.
        with self.assertRaises(ValueError) as context:
            get_tool_class("sequential_thinking")

        message = str(context.exception)
        self.assertIn("sequential_thinking", message)
        for tool_name in tools_registry:
            self.assertIn(tool_name, message)
        self.assertIn("trae-cli tools", message)

    def test_known_tool_names_resolve(self):
        for tool_name, tool_class in tools_registry.items():
            self.assertIs(get_tool_class(tool_name), tool_class)


if __name__ == "__main__":
    unittest.main()
