import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from trae_agent.cli import cli

CONFIG_TEMPLATE = """model_providers:
  fakeprovider:
    api_key: not-a-real-key
    provider: fakeprovider
models:
  fakemodel:
    model_provider: fakeprovider
    model: fakemodel
    temperature: 0.5
    top_p: 1
    top_k: 0
    max_tokens: 4096
    parallel_tool_calls: false
    max_retries: 1
agents:
  trae_agent:
    enable_lakeview: false
    model: fakemodel
    max_steps: {max_steps}
    tools:
      - bash
      - task_done
"""


def _agent_max_steps(cli_args: list[str], config_file: str) -> int:
    """Run a CLI command and return the max_steps the resolved config ended up with."""
    agent_cls = MagicMock()
    with (
        patch("trae_agent.cli.resolve_config_file", return_value=config_file),
        patch("trae_agent.cli.Agent", agent_cls),
        patch("trae_agent.cli.asyncio.run", MagicMock()),
        patch("trae_agent.cli.ConsoleFactory.create_console", MagicMock()),
        patch("trae_agent.cli._run_simple_interactive_loop", MagicMock()),
        patch("trae_agent.cli._run_rich_interactive_loop", MagicMock()),
    ):
        result = CliRunner().invoke(cli, cli_args)

    assert result.exception is None or isinstance(result.exception, SystemExit), (
        f"{cli_args[0]} crashed: {result.exception!r}"
    )
    assert agent_cls.call_args is not None, f"{cli_args[0]} never created an agent"
    return agent_cls.call_args[0][1].trae_agent.max_steps


class TestMaxStepsPrecedence(unittest.TestCase):
    """`max_steps` from the config file must win when the CLI flag is not given."""

    def setUp(self):
        self.runner = CliRunner()

    def _write_config(self, max_steps: int) -> str:
        path = Path("trae_config.yaml").resolve()
        path.write_text(CONFIG_TEMPLATE.format(max_steps=max_steps), encoding="utf-8")
        return str(path)

    def test_interactive_without_flag_keeps_config_max_steps(self):
        with self.runner.isolated_filesystem():
            config_file = self._write_config(50)
            self.assertEqual(_agent_max_steps(["interactive"], config_file), 50)

    def test_run_without_flag_keeps_config_max_steps(self):
        with self.runner.isolated_filesystem():
            config_file = self._write_config(50)
            self.assertEqual(_agent_max_steps(["run", "a task"], config_file), 50)

    def test_interactive_flag_overrides_config(self):
        with self.runner.isolated_filesystem():
            config_file = self._write_config(50)
            self.assertEqual(
                _agent_max_steps(["interactive", "--max-steps", "70"], config_file), 70
            )

    def test_run_flag_overrides_config(self):
        with self.runner.isolated_filesystem():
            config_file = self._write_config(50)
            self.assertEqual(
                _agent_max_steps(["run", "a task", "--max-steps", "70"], config_file), 70
            )


if __name__ == "__main__":
    unittest.main()
