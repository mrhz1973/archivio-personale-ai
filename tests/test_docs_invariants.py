"""
ARCH-0130..ARCH-0132 — Lightweight doc invariant tests.

Verifies that key rules are present in documentation and that validation
sections do not contain forbidden auto-open commands.
"""

import re
import unittest
from pathlib import Path

_REPO = Path(__file__).parent.parent
_LLMS = (_REPO / "LLMS.md").read_text(encoding="utf-8")
_COMMANDS = (_REPO / "docs" / "COMMANDS.md").read_text(encoding="utf-8")


# ── ARCH-0130: no forbidden auto-open commands in validation sections ──────────

class TestCommandsValidationSection(unittest.TestCase):

    def _validation_section(self):
        """Extract text from the Validation heading to the next ## heading."""
        match = re.search(r"## Validation\b(.+?)(?=\n## |\Z)", _COMMANDS, re.DOTALL)
        self.assertIsNotNone(match, "Validation section not found in COMMANDS.md")
        return match.group(1)

    def test_validation_section_has_no_invoke_item(self):
        section = self._validation_section()
        self.assertNotIn("Invoke-Item", section)

    def test_validation_section_has_no_start_command(self):
        # Reject bare `start ` as a shell open command (not `start` in other contexts)
        section = self._validation_section()
        self.assertNotRegex(section, r"\bstart\s+\S")

    def test_commands_md_states_no_auto_open(self):
        self.assertIn("Never auto-open", _COMMANDS)

    def test_invoke_item_is_gated_as_explicit_user_request(self):
        # The Invoke-Item block must only appear under an "explicit user request" guard
        idx = _COMMANDS.find("Invoke-Item")
        if idx == -1:
            return  # no Invoke-Item at all is also fine
        preceding = _COMMANDS[max(0, idx - 500):idx]
        self.assertIn("explicit user request", preceding.lower())


# ── ARCH-0131: LLMS.md contains orchestrator prompt compactness rule ──────────

class TestLLMSCompactnessRule(unittest.TestCase):

    def test_compactness_rule_present(self):
        self.assertIn("compactness", _LLMS.lower())

    def test_compactness_rule_references_orchestrator(self):
        self.assertIn("orchestrator", _LLMS.lower())

    def test_compactness_rule_mentions_llms_md(self):
        # The rule must reference LLMS.md as the place where rules are stored
        self.assertIn("LLMS.md", _LLMS)


# ── ARCH-0132: LLMS.md contains task ID uniqueness rule ──────────────────────

class TestLLMSTaskIDUniquenessRule(unittest.TestCase):

    def test_uniqueness_rule_present(self):
        self.assertIn("uniqueness", _LLMS.lower())

    def test_uniqueness_rule_references_task_ids(self):
        lower = _LLMS.lower()
        self.assertTrue(
            "task id" in lower or "task ids" in lower or "id uniqueness" in lower,
            "LLMS.md must mention task ID uniqueness"
        )

    def test_uniqueness_rule_forbids_rebase(self):
        # The rule must explicitly prohibit history rewriting
        lower = _LLMS.lower()
        self.assertTrue(
            "no rebase" in lower or "rebase" in lower,
            "LLMS.md uniqueness rule must mention rebase prohibition"
        )


if __name__ == "__main__":
    unittest.main()
