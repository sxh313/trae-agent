# Copyright (c) 2025 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

"""Regression tests for whole-number arguments to the sequential thinking tool."""

import json
import unittest

from trae_agent.tools.base import ToolCallArguments
from trae_agent.tools.sequential_thinking_tool import SequentialThinkingTool


def _status(payload: str) -> dict[str, object]:
    """Read back the JSON status block the tool returns on success."""
    return json.loads(payload.split("Status:\n", 1)[1])


def _arguments(**overrides: str | int | float | bool | None) -> ToolCallArguments:
    arguments: ToolCallArguments = {
        "thought": "working on it",
        "thought_number": 1,
        "total_thoughts": 5,
        "next_thought_needed": True,
    }
    arguments.update(overrides)
    return arguments


class TestSequentialThinkingIntegerArguments(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.tool = SequentialThinkingTool()

    def test_tool_publishes_integer_type_for_the_counters(self) -> None:
        types = {parameter.name: parameter.type for parameter in self.tool.parameters}
        self.assertEqual(types["thought_number"], "integer")
        self.assertEqual(types["total_thoughts"], "integer")
        self.assertEqual(types["revises_thought"], "integer")
        self.assertEqual(types["branch_from_thought"], "integer")

    async def test_whole_number_counters_are_accepted(self) -> None:
        result = await self.tool.execute(_arguments(thought_number=1.0, total_thoughts=5.0))

        self.assertIsNone(result.error)
        self.assertEqual(0, result.error_code)
        status = _status(result.output or "")
        self.assertEqual(1, status["thought_number"])
        self.assertEqual(5, status["total_thoughts"])

    async def test_whole_number_revision_counters_are_accepted(self) -> None:
        result = await self.tool.execute(
            _arguments(
                thought_number=2.0,
                total_thoughts=4.0,
                next_thought_needed=False,
                is_revision=True,
                revises_thought=1.0,
                branch_from_thought=2.0,
                branch_id="alternative",
            )
        )

        self.assertIsNone(result.error)
        self.assertEqual(0, result.error_code)

    async def test_plain_integer_counters_are_still_accepted(self) -> None:
        result = await self.tool.execute(_arguments())

        self.assertIsNone(result.error)
        self.assertEqual(0, result.error_code)
        status = _status(result.output or "")
        self.assertIsInstance(status["total_thoughts"], int)

    async def test_fractional_counter_is_rejected(self) -> None:
        result = await self.tool.execute(_arguments(total_thoughts=2.5))

        self.assertEqual(-1, result.error_code)
        self.assertIn("total_thoughts", result.error or "")

    async def test_non_numeric_counter_is_rejected(self) -> None:
        result = await self.tool.execute(_arguments(thought_number="one"))

        self.assertEqual(-1, result.error_code)
        self.assertIn("thought_number", result.error or "")

    async def test_counter_below_minimum_is_rejected(self) -> None:
        result = await self.tool.execute(_arguments(total_thoughts=0.0))

        self.assertEqual(-1, result.error_code)
        self.assertIn("at least 1", result.error or "")

    async def test_boolean_counter_is_rejected(self) -> None:
        result = await self.tool.execute(_arguments(revises_thought=2.5, is_revision=True))

        self.assertEqual(-1, result.error_code)
        self.assertIn("revises_thought", result.error or "")

    async def test_missing_counter_is_rejected(self) -> None:
        arguments = _arguments()
        del arguments["total_thoughts"]
        result = await self.tool.execute(arguments)

        self.assertEqual(-1, result.error_code)
        self.assertIn("total_thoughts", result.error or "")
