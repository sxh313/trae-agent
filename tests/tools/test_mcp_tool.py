import unittest
from unittest.mock import AsyncMock, MagicMock

import mcp

from trae_agent.tools.base import ToolCallArguments, ToolExecResult
from trae_agent.tools.mcp_tool import MCPTool


class TestMCPTool(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # simulate a tool schema
        self.mock_tool = MagicMock()
        self.mock_tool.name = "test_tool"
        self.mock_tool.description = "A test tool"
        self.mock_tool.inputSchema = {
            "required": ["param1"],
            "properties": {
                "param1": {"type": "string", "description": "First parameter"},
                "param2": {"type": "integer", "description": "Second parameter"},
            },
        }

        # simulate client side
        self.mock_client = MagicMock()
        self.tool = MCPTool(self.mock_client, self.mock_tool, model_provider="test_provider")

    def test_get_name(self):
        self.assertEqual(self.tool.get_name(), "test_tool")

    def test_get_description(self):
        self.assertEqual(self.tool.get_description(), "A test tool")

    def test_get_model_provider(self):
        self.assertEqual(self.tool.get_model_provider(), "test_provider")

    def test_get_parameters(self):
        params = self.tool.get_parameters()
        self.assertEqual(len(params), 2)
        self.assertTrue(any(p.name == "param1" and p.required for p in params))
        self.assertTrue(any(p.name == "param2" and not p.required for p in params))

    async def test_execute_success(self):
        mock_response = MagicMock()
        mock_response.isError = False
        mock_response.content = [MagicMock(text="Execution successful")]
        self.mock_client.call_tool = AsyncMock(return_value=mock_response)

        arguments = ToolCallArguments(arguments={"param1": "value", "param2": 123})
        result: ToolExecResult = await self.tool.execute(arguments)

        self.assertIsNone(result.error)
        self.assertEqual(result.output, "Execution successful")

    async def test_execute_failure(self):
        mock_response = MagicMock()
        mock_response.isError = True
        mock_response.content = [MagicMock(text="Something went wrong")]
        self.mock_client.call_tool = AsyncMock(return_value=mock_response)

        arguments = ToolCallArguments(arguments={"param1": "value"})
        result: ToolExecResult = await self.tool.execute(arguments)

        self.assertIsNone(result.output)
        self.assertEqual(result.error, "Something went wrong")

    async def test_execute_exception(self):
        self.mock_client.call_tool = AsyncMock(side_effect=RuntimeError("Tool crashed"))

        arguments = ToolCallArguments(arguments={"param1": "value"})
        result: ToolExecResult = await self.tool.execute(arguments)

        self.assertIn("Error running mcp tool", result.error)
        self.assertEqual(result.error_code, -1)


class TestMCPToolOptionalSchemaFields(unittest.TestCase):
    """`type` and `description` are optional in JSON Schema, so a server may omit either."""

    def _tool(self, input_schema: dict, description: str | None = None) -> MCPTool:
        return MCPTool(
            MagicMock(),
            mcp.types.Tool(name="search", description=description, inputSchema=input_schema),
            model_provider="openai",
        )

    def test_property_without_description(self):
        tool = self._tool(
            {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            }
        )
        parameters = tool.get_parameters()
        self.assertEqual(parameters[0].name, "query")
        self.assertEqual(parameters[0].description, "")

    def test_property_without_type(self):
        tool = self._tool(
            {
                "type": "object",
                "properties": {"payload": {"description": "Unconstrained value"}},
            }
        )
        parameters = tool.get_parameters()
        self.assertEqual(parameters[0].type, "string")
        self.assertEqual(parameters[0].description, "Unconstrained value")

    def test_input_schema_is_sendable_to_a_provider(self):
        tool = self._tool(
            {
                "type": "object",
                "properties": {"query": {}, "limit": {"type": "integer"}},
                "required": ["query", "limit"],
            }
        )
        self.assertEqual(
            tool.get_input_schema()["properties"],
            {
                "query": {"type": "string", "description": ""},
                "limit": {"type": "integer", "description": ""},
            },
        )

    def test_tool_without_description(self):
        self.assertEqual(self._tool({"type": "object", "properties": {}}).get_description(), "")


if __name__ == "__main__":
    unittest.main()
