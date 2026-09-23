# Copyright (c) 2025 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

"""Tools module for Trae Agent."""

from trae_agent.tools.base import Tool, ToolCall, ToolExecutor, ToolResult
from trae_agent.tools.bash_tool import BashTool
from trae_agent.tools.ckg_tool import CKGTool
from trae_agent.tools.edit_tool import TextEditorTool
from trae_agent.tools.json_edit_tool import JSONEditTool
from trae_agent.tools.sequential_thinking_tool import SequentialThinkingTool
from trae_agent.tools.task_done_tool import TaskDoneTool

__all__ = [
    "Tool",
    "ToolResult",
    "ToolCall",
    "ToolExecutor",
    "BashTool",
    "TextEditorTool",
    "JSONEditTool",
    "SequentialThinkingTool",
    "TaskDoneTool",
    "CKGTool",
    "get_tool_class",
]

tools_registry: dict[str, type[Tool]] = {
    "bash": BashTool,
    "str_replace_based_edit_tool": TextEditorTool,
    "json_edit_tool": JSONEditTool,
    "sequentialthinking": SequentialThinkingTool,
    "task_done": TaskDoneTool,
    "ckg": CKGTool,
}


def get_tool_class(tool_name: str) -> type[Tool]:
    """Look up a tool by the name used in the `tools` configuration field."""
    tool_class = tools_registry.get(tool_name)
    if tool_class is None:
        available = ", ".join(sorted(tools_registry))
        raise ValueError(
            f"Unknown tool '{tool_name}' in the agent configuration. Available tools: "
            f"{available}. Run `trae-cli tools` for their descriptions."
        )
    return tool_class
