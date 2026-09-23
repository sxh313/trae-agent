# Copyright (c) 2025 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

"""Guards the configuration examples users copy from, against drift from the loader."""

import re
import unittest
from pathlib import Path

from trae_agent.utils.config import Config

REPO_ROOT = Path(__file__).resolve().parents[2]
README_PATH = REPO_ROOT / "README.md"
EXAMPLE_CONFIG_PATH = REPO_ROOT / "trae_config.yaml.example"


def get_readme_config_example() -> str:
    """Return the full ``trae_config.yaml`` example documented in README.md."""
    yaml_blocks = re.findall(
        r"```yaml\n(.*?)```", README_PATH.read_text(encoding="utf-8"), flags=re.DOTALL
    )
    examples = [block for block in yaml_blocks if "model_providers:" in block]
    if len(examples) != 1:
        raise AssertionError(
            "Expected exactly one full configuration example in README.md, "
            f"found {len(examples)}. Keep it in sync with Config.create()."
        )
    return examples[0]


class TestDocumentedConfigs(unittest.TestCase):
    def test_readme_config_example_loads(self):
        config = Config.create(config_string=get_readme_config_example())

        assert config.trae_agent is not None
        self.assertEqual(config.trae_agent.model.model, "claude-sonnet-4-20250514")
        self.assertEqual(config.trae_agent.model.model_provider.provider, "anthropic")

    def test_readme_config_example_enables_lakeview(self):
        config = Config.create(config_string=get_readme_config_example())

        assert config.trae_agent is not None
        assert config.lakeview is not None
        self.assertTrue(config.trae_agent.enable_lakeview)
        self.assertEqual(config.lakeview.model.model, config.trae_agent.model.model)

    def test_shipped_example_config_loads(self):
        config = Config.create(config_file=str(EXAMPLE_CONFIG_PATH))

        assert config.trae_agent is not None
        self.assertEqual(config.trae_agent.max_steps, 200)
        self.assertIn("bash", config.trae_agent.tools)


if __name__ == "__main__":
    unittest.main()
