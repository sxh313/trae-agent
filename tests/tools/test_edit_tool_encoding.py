# Copyright (c) 2025 ByteDance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

"""Tests for reading and writing user files as UTF-8, whatever the OS locale is."""

import ast
import asyncio
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from trae_agent.tools.edit_tool import TextEditorTool

REPO_ROOT = Path(__file__).resolve().parents[2]

# Modules that read and write the user's own files on the agent's behalf.
USER_FILE_MODULES = (
    "trae_agent/cli.py",
    "trae_agent/tools/edit_tool.py",
    "trae_agent/tools/edit_tool_cli.py",
)

TEXT_IO_FUNCTIONS = {"open", "read_text", "write_text"}

ORIGINAL_TEXT = '# 中文注释 🎉\nvalue = "数据"\n'
EDITED_TEXT = '# 中文注释 🎉\nvalue = "结果"\n'


def _calls_without_encoding(source_file: str) -> list[int]:
    """Collect the lines of text-mode file IO that leave `encoding` to the locale."""
    tree = ast.parse((REPO_ROOT / source_file).read_text(encoding="utf-8"))
    locale_dependent: list[int] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
        if name not in TEXT_IO_FUNCTIONS:
            continue
        if any(keyword.arg == "encoding" for keyword in node.keywords):
            continue
        if name == "open" and _opens_binary(node):
            continue
        locale_dependent.append(node.lineno)

    return sorted(locale_dependent)


def _opens_binary(node: ast.Call) -> bool:
    mode = node.args[1] if len(node.args) > 1 else None
    if mode is None:
        mode = next((k.value for k in node.keywords if k.arg == "mode"), None)
    return isinstance(mode, ast.Constant) and isinstance(mode.value, str) and "b" in mode.value


_CHILD = f"""
import asyncio, json, locale, tempfile
from pathlib import Path

from trae_agent.tools.edit_tool import TextEditorTool


async def run():
    path = Path(tempfile.mkdtemp()) / "snippet.py"
    path.write_bytes({ORIGINAL_TEXT!r}.encode("utf-8"))
    result = await TextEditorTool().execute({{
        "command": "str_replace",
        "path": str(path),
        "old_str": '"数据"',
        "new_str": '"结果"',
    }})
    print(json.dumps({{
        "locale_encoding": locale.getpreferredencoding(False),
        "error": result.error,
        # Line terminators are normalised away here: this is about encoding only.
        "content": path.read_bytes().decode("utf-8").replace("\\r\\n", "\\n"),
    }}))


asyncio.run(run())
"""


async def _str_replace(path: Path, old_str: str, new_str: str):
    return await TextEditorTool().execute(
        {
            "command": "str_replace",
            "path": str(path),
            "old_str": old_str,
            "new_str": new_str,
        }
    )


class TestUserFileEncodingIsNotLocaleDependent(unittest.TestCase):
    def test_every_user_file_read_and_write_names_its_encoding(self):
        missing = {}
        for module in USER_FILE_MODULES:
            lines = _calls_without_encoding(module)
            if lines:
                missing[module] = lines

        self.assertEqual(
            missing,
            {},
            "These text-mode file reads/writes fall back to locale.getpreferredencoding(), which "
            "is not UTF-8 on hosts running an ANSI code page (cp936 on a Simplified Chinese "
            "Windows install). Pass encoding='utf-8' like json_edit_tool already does.",
        )

    def test_str_replace_edits_a_file_holding_non_ascii_text(self):
        async def edit():
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "snippet.py"
                path.write_bytes(ORIGINAL_TEXT.encode("utf-8"))

                result = await _str_replace(path, '"数据"', '"结果"')

                self.assertIsNone(result.error, result.error)
                self.assertEqual(path.read_text(encoding="utf-8"), EDITED_TEXT)

        asyncio.run(edit())

    def test_str_replace_survives_a_non_utf8_locale(self):
        env = dict(
            os.environ,
            LC_ALL="C",
            LANG="C",
            PYTHONCOERCECLOCALE="0",
            PYTHONUTF8="0",
            PYTHONPATH=str(REPO_ROOT),
        )
        completed = subprocess.run(
            [sys.executable, "-c", _CHILD],
            capture_output=True,
            cwd=str(REPO_ROOT),
            env=env,
            timeout=120,
        )
        stdout = completed.stdout.decode("utf-8", errors="replace")
        stderr = completed.stderr.decode("utf-8", errors="replace")
        self.assertEqual(
            completed.returncode, 0, f"child exited with {completed.returncode}\n{stderr}"
        )

        report = json.loads(stdout.strip().splitlines()[-1])
        if report["locale_encoding"].lower().replace("-", "").replace("_", "") == "utf8":
            self.skipTest(f"interpreter ignores the requested locale ({report['locale_encoding']})")

        self.assertIsNone(report["error"], f"locale {report['locale_encoding']}: {report['error']}")
        self.assertEqual(report["content"], EDITED_TEXT)


if __name__ == "__main__":
    unittest.main()
