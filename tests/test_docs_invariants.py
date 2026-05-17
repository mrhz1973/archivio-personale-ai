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
_README = (_REPO / "README.md").read_text(encoding="utf-8")


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


# ── ARCH-0161: COMMANDS.md mentions run_validations.py ───────────────────────

class TestCommandsMentionsRunner(unittest.TestCase):

    def test_run_validations_mentioned(self):
        self.assertIn("run_validations.py", _COMMANDS)

    def test_quick_flag_mentioned(self):
        self.assertIn("--quick", _COMMANDS)

    def test_list_flag_mentioned(self):
        self.assertIn("--list", _COMMANDS)


# ── ARCH-0162: COMMANDS.md does not present runner as modifying personal files ─

class TestCommandsRunnerSafety(unittest.TestCase):

    def _runner_section(self):
        match = re.search(
            r"## Local validation runner\b(.+?)(?=\n## |\Z)", _COMMANDS, re.DOTALL
        )
        self.assertIsNotNone(match, "Local validation runner section not found in COMMANDS.md")
        return match.group(1)

    def test_runner_section_has_no_personal_file_modification(self):
        section = self._runner_section()
        # The section must not suggest that the runner modifies/touches personal files.
        # Safety notes that *deny* this (e.g. "no personal files") are acceptable.
        for phrase in ("modifica file personali", "tocca file personali",
                       "move personal", "rename personal", "delete personal",
                       "modifies personal files", "touches personal files"):
            self.assertNotIn(phrase, section.lower())

    def test_runner_section_has_no_reports_modification(self):
        section = self._runner_section()
        self.assertNotIn("modif", section.lower())

    def test_runner_section_states_no_network(self):
        section = self._runner_section()
        self.assertIn("no network", section.lower())


# ── ARCH-0289/0290: demo_manifest.json documented; no auto-open suggestion ────

class TestCommandsMentionsManifest(unittest.TestCase):
    """ARCH-0289: COMMANDS.md mentions demo_manifest.json."""

    def test_commands_mentions_manifest_filename(self):
        self.assertIn("demo_manifest.json", _COMMANDS)

    def test_commands_states_manifest_is_temporary(self):
        self.assertIn("temporary", _COMMANDS.lower())

    def test_commands_states_manifest_not_in_reports(self):
        # The docs must clarify that the manifest is not written to reports/
        self.assertIn("not in `reports/`", _COMMANDS)

    def test_commands_does_not_suggest_auto_open_manifest(self):
        """ARCH-0290: COMMANDS.md does not suggest auto-opening manifest or reports."""
        # No Invoke-Item or start command near manifest references
        idx = _COMMANDS.find("demo_manifest.json")
        if idx == -1:
            return
        surrounding = _COMMANDS[max(0, idx - 200):idx + 200]
        self.assertNotIn("Invoke-Item", surrounding)
        self.assertNotRegex(surrounding, r"\bstart\s+\S")


# ── ARCH-0320..0323: README.md doc invariants ─────────────────────────────────

class TestReadmeDocInvariants(unittest.TestCase):

    def _code_blocks(self, text):
        return re.findall(r'```[^\n]*\n(.*?)```', text, re.DOTALL)

    def test_readme_mentions_run_synthetic_demo(self):
        """ARCH-0320: README.md mentions run_synthetic_demo.py."""
        self.assertIn("run_synthetic_demo.py", _README)

    def test_readme_mentions_run_validations(self):
        """ARCH-0321: README.md mentions run_validations.py."""
        self.assertIn("run_validations.py", _README)

    def test_readme_says_demo_uses_synthetic_data(self):
        """ARCH-0322: README.md clarifies the demo uses synthetic data."""
        lower = _README.lower()
        self.assertTrue(
            "synthetic" in lower,
            "README.md must state the demo uses synthetic data"
        )

    def test_readme_no_invoke_item_in_code_blocks(self):
        """ARCH-0323: README.md code blocks must not contain Invoke-Item."""
        for block in self._code_blocks(_README):
            self.assertNotIn("Invoke-Item", block,
                             "README.md code block must not use Invoke-Item")

    def test_readme_no_start_open_in_code_blocks(self):
        """ARCH-0323: README.md code blocks must not use 'start' to open files."""
        for block in self._code_blocks(_README):
            self.assertNotRegex(block, r"\bstart\s+\S.*\.(html|json|pdf)",
                                "README.md code block must not use 'start' to open files")


# ── ARCH-0324..0326: COMMANDS.md additional doc invariants ───────────────────

class TestCommandsAdditionalInvariants(unittest.TestCase):

    def test_commands_keep_temp_mentioned_as_manual_inspection(self):
        """ARCH-0325: COMMANDS.md mentions --keep-temp as manual inspection."""
        self.assertIn("--keep-temp", _COMMANDS)
        lower = _COMMANDS.lower()
        self.assertTrue(
            "manual inspection" in lower or "ispezione manuale" in lower,
            "COMMANDS.md must describe --keep-temp as manual inspection"
        )

    def test_commands_manifest_must_not_be_committed(self):
        """ARCH-0326: COMMANDS.md states demo_manifest.json must not be committed."""
        lower = _COMMANDS.lower()
        self.assertTrue(
            "must not be committed" in lower or "non va committato" in lower
            or "not be committed" in lower,
            "COMMANDS.md must state that demo_manifest.json must not be committed"
        )

    def test_commands_no_auto_open_in_demo_section(self):
        """ARCH-0324: COMMANDS.md demo sections do not suggest auto-opening."""
        match = re.search(
            r"## Synthetic end-to-end demo\b(.+?)(?=\n## |\Z)", _COMMANDS, re.DOTALL
        )
        if match:
            section = match.group(1)
            self.assertNotRegex(section, r"Invoke-Item\s+\S",
                                "demo section must not suggest Invoke-Item as a command")
            self.assertNotRegex(section, r"\bstart\s+\S.*\.(html|json)",
                                "demo section must not use 'start' to open files")


if __name__ == "__main__":
    unittest.main()
