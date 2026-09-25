# Copyright (c) 2025 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import unittest

from trae_agent.utils.config import Config, ConfigError

VALID_LAKEVIEW_YAML = """
model_providers:
    anthropic:
        provider: anthropic
        api_key: test-api-key
        base_url: https://api.anthropic.com
models:
    lakeview_model:
        model_provider: anthropic
        model: claude-sonnet-4-20250514
        temperature: 0.5
        top_p: 1.0
        top_k: 0
        parallel_tool_calls: false
        max_retries: 5
agents:
    trae_agent:
        model: lakeview_model
        max_steps: 5
        enable_lakeview: false
        tools: []
"""


def with_lakeview_model(name: str | None) -> str:
    block = "lakeview:\n    model:\n" if name is None else f"lakeview:\n    model: {name}\n"
    return VALID_LAKEVIEW_YAML + block


class TestConfigModelNotFound(unittest.TestCase):
    def test_known_lakeview_model_loads(self):
        config = Config.create(config_string=with_lakeview_model("lakeview_model"))
        self.assertIsNotNone(config.lakeview)
        self.assertEqual(config.lakeview.model.model, "claude-sonnet-4-20250514")

    def test_unknown_lakeview_model_raises_config_error(self):
        with self.assertRaises(ConfigError) as raised:
            Config.create(config_string=with_lakeview_model("missing_model"))
        self.assertIn("missing_model", str(raised.exception))

    def test_lakeview_without_model_raises_config_error(self):
        with self.assertRaises(ConfigError):
            Config.create(config_string=with_lakeview_model(None))


if __name__ == "__main__":
    unittest.main()
