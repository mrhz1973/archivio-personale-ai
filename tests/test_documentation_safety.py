"""
ARCH-0725..ARCH-0759 — Documentation safety regression tests.

Verifies that README.md, docs/COMMANDS.md, docs/V1_READINESS.md and
docs/SAFETY_RULES.md (when present) do not introduce dangerous wording
or contradict the local-first / review-only / safety-first invariants.
"""

import re
import unittest
from pathlib import Path

_REPO = Path(__file__).parent.parent

# ── ARCH-0727: document set ───────────────────────────────────────────────────

_README_PATH        = _REPO / "README.md"
_COMMANDS_PATH      = _REPO / "docs" / "COMMANDS.md"
_V1_PATH            = _REPO / "docs" / "V1_READINESS.md"
_SAFETY_PATH        = _REPO / "docs" / "SAFETY_RULES.md"
_LLMS_PATH          = _REPO / "LLMS.md"

_README   = _README_PATH.read_text(encoding="utf-8")
_COMMANDS = _COMMANDS_PATH.read_text(encoding="utf-8")
_V1       = _V1_PATH.read_text(encoding="utf-8")
_SAFETY   = _SAFETY_PATH.read_text(encoding="utf-8") if _SAFETY_PATH.exists() else None

# Docs that must always pass every safety check
_ALWAYS_DOCS = {
    "README.md": _README,
    "docs/COMMANDS.md": _COMMANDS,
    "docs/V1_READINESS.md": _V1,
}
if _SAFETY is not None:
    _ALWAYS_DOCS["docs/SAFETY_RULES.md"] = _SAFETY

_ALL_DOCS = _ALWAYS_DOCS  # alias used by generic helpers


def _negated_context(text: str, match: re.Match, window: int = 600) -> bool:
    """Return True if the match appears inside a negating/forbidden context."""
    start = max(0, match.start() - window)
    ctx = text[start: match.end() + 100].lower()
    negators = (
        "forbidden", "vietato", "non usare", "not use", "do not",
        "never", "non ", "no ", "prohibit", "proibito",
        "non autorizzato", "non implementato", "not implemented",
        "not allowed", "non consentit", "assenza", "absent",
        "non devono", "must not", "nessun", "nessuna",
    )
    return any(n in ctx for n in negators)


# ── ARCH-0725: LLMS.md batch 29A closed with correct hash ────────────────────

class TestLLMSBatch29AClosed(unittest.TestCase):

    def test_batch_29a_closed_with_commit_hash(self):
        """ARCH-0725: ARCH-0690..ARCH-0724 must be closed with commit 4edda80."""
        llms = _LLMS_PATH.read_text(encoding="utf-8")
        self.assertIn("ARCH-0690..ARCH-0724", llms, "Batch 29A range not found in LLMS.md")
        self.assertIn("4edda80", llms, "Commit hash 4edda80 not found in LLMS.md")
        pattern = re.compile(
            r"ARCH-0690\.\.ARCH-0724.+?4edda80", re.DOTALL
        )
        self.assertRegex(llms, pattern,
                         "ARCH-0690..ARCH-0724 must be followed by commit hash 4edda80")


# ── ARCH-0728: required documents exist ──────────────────────────────────────

class TestRequiredDocumentsExist(unittest.TestCase):

    def test_readme_exists(self):
        self.assertTrue(_README_PATH.exists(), "README.md must exist")

    def test_commands_exists(self):
        self.assertTrue(_COMMANDS_PATH.exists(), "docs/COMMANDS.md must exist")

    def test_v1_readiness_exists(self):
        self.assertTrue(_V1_PATH.exists(), "docs/V1_READINESS.md must exist")


# ── ARCH-0729: README.md local-first / review-only / safety-first wording ────

class TestReadmeCorePrinciples(unittest.TestCase):

    def test_readme_local_first(self):
        """ARCH-0729"""
        self.assertIn("local-first", _README.lower())

    def test_readme_review_only(self):
        """ARCH-0729"""
        self.assertIn("review-only", _README.lower())

    def test_readme_safety_first(self):
        """ARCH-0729"""
        self.assertIn("safety-first", _README.lower())


# ── ARCH-0730: V1_READINESS.md core principles ───────────────────────────────

class TestV1ReadinessCorePrinciples(unittest.TestCase):

    def test_v1_local_first(self):
        """ARCH-0730"""
        self.assertIn("local-first", _V1.lower())

    def test_v1_review_only(self):
        """ARCH-0730"""
        self.assertIn("review-only", _V1.lower())

    def test_v1_safety_first(self):
        """ARCH-0730"""
        self.assertIn("safety-first", _V1.lower())


# ── ARCH-0731: COMMANDS.md states no report auto-open ────────────────────────

class TestCommandsNoAutoOpenNote(unittest.TestCase):

    def test_commands_states_no_auto_open(self):
        """ARCH-0731"""
        lower = _COMMANDS.lower()
        self.assertTrue(
            "nessun report viene aperto automaticamente" in lower
            or "never auto-open" in lower
            or "no report is opened automatically" in lower,
            "docs/COMMANDS.md must state that no report is opened automatically"
        )


# ── ARCH-0732: README.md HTML reports are for manual review ──────────────────

class TestReadmeHTMLReportsManualReview(unittest.TestCase):

    def test_readme_html_reports_manual_review(self):
        """ARCH-0732"""
        lower = _README.lower()
        self.assertTrue(
            "revisione manuale" in lower or "manual review" in lower,
            "README.md must state that HTML reports are for manual review"
        )


# ── ARCH-0733: V1_READINESS.md — no automatic action on personal files ───────

class TestV1NoAutoActionOnPersonalFiles(unittest.TestCase):

    def test_v1_no_automatic_action(self):
        """ARCH-0733"""
        lower = _V1.lower()
        self.assertTrue(
            "nessuna azione automatica" in lower
            or "no automatic action" in lower
            or "no action is performed automatically" in lower,
            "docs/V1_READINESS.md must state no automatic action on personal files"
        )


# ── ARCH-0734..0737: no dangerous git commands as positive instructions ───────

class TestNoDangerousGitCommands(unittest.TestCase):
    """ARCH-0734/0735/0736/0737"""

    def _assert_only_in_negated_context(self, pattern: str, label: str):
        regex = re.compile(re.escape(pattern))
        for name, text in _ALL_DOCS.items():
            for m in regex.finditer(text):
                self.assertTrue(
                    _negated_context(text, m),
                    f"{name}: '{label}' found outside a forbidden/negated context"
                )

    def test_no_git_add_dot_as_instruction(self):
        """ARCH-0734"""
        self._assert_only_in_negated_context("git add .", "git add .")

    def test_no_git_reset_hard_as_instruction(self):
        """ARCH-0735"""
        self._assert_only_in_negated_context("git reset --hard", "git reset --hard")

    def test_no_git_clean_as_instruction(self):
        """ARCH-0736"""
        self._assert_only_in_negated_context("git clean", "git clean")

    def test_no_git_push_force_as_instruction(self):
        """ARCH-0737"""
        self._assert_only_in_negated_context("git push --force", "git push --force")


# ── ARCH-0738: no `start` as operational open command ────────────────────────

class TestNoStartCommand(unittest.TestCase):

    def test_no_start_open_as_instruction(self):
        """ARCH-0738: 'start' must not appear as a positive instruction to open reports."""
        pattern = re.compile(r"\bstart\s+\S.*\.(html|json|pdf)", re.IGNORECASE)
        for name, text in _ALL_DOCS.items():
            for m in pattern.finditer(text):
                self.assertTrue(
                    _negated_context(text, m),
                    f"{name}: 'start <file>' found outside a negated context"
                )


# ── ARCH-0739: Invoke-Item only under explicit-user-request guard ─────────────

class TestInvokeItemGated(unittest.TestCase):

    def test_invoke_item_only_on_explicit_request(self):
        """ARCH-0739"""
        pattern = re.compile(r"Invoke-Item")
        for name, text in _ALL_DOCS.items():
            for m in pattern.finditer(text):
                start = max(0, m.start() - 500)
                ctx = text[start: m.end() + 200].lower()
                self.assertTrue(
                    "explicit" in ctx and ("request" in ctx or "richiesta" in ctx)
                    or _negated_context(text, m),
                    f"{name}: Invoke-Item found without 'explicit request' guard"
                )


# ── ARCH-0740: no os.startfile ───────────────────────────────────────────────

class TestNoOsStartfile(unittest.TestCase):

    def test_no_os_startfile(self):
        """ARCH-0740"""
        for name, text in _ALL_DOCS.items():
            self.assertNotIn(
                "os.startfile", text,
                f"{name}: must not reference os.startfile"
            )


# ── ARCH-0741: no cloud/API on personal file contents ────────────────────────

class TestNoCloudAPIOnPersonalFiles(unittest.TestCase):

    def _check_if_negated(self, pattern_str: str, label: str):
        regex = re.compile(pattern_str, re.IGNORECASE)
        for name, text in _ALL_DOCS.items():
            for m in regex.finditer(text):
                self.assertTrue(
                    _negated_context(text, m),
                    f"{name}: '{label}' found outside a negated/forbidden context"
                )

    def test_no_cloud_api_on_personal_contents(self):
        """ARCH-0741"""
        self._check_if_negated(
            r"cloud\s+(?:api|service|service).{0,60}(?:personal|personali)",
            "cloud API on personal files"
        )

    def test_no_external_api_on_personal_contents(self):
        """ARCH-0741"""
        # Check for "API esterne sui contenuti personali" type phrases
        self._check_if_negated(
            r"api\s+(?:esterne?|extern).{0,60}(?:personal|personali)",
            "API esterne on personal files"
        )


# ── ARCH-0742: no Google Drive API on personal files ─────────────────────────

class TestNoGoogleDriveAPIOnPersonalFiles(unittest.TestCase):

    def test_google_drive_api_only_in_negated_context(self):
        """ARCH-0742"""
        pattern = re.compile(r"Google Drive API", re.IGNORECASE)
        for name, text in _ALL_DOCS.items():
            for m in pattern.finditer(text):
                self.assertTrue(
                    _negated_context(text, m),
                    f"{name}: 'Google Drive API' found outside a forbidden/negated context"
                )


# ── ARCH-0743: no n8n runtime on personal files ──────────────────────────────

class TestNoN8nRuntimeOnPersonalFiles(unittest.TestCase):

    def test_n8n_only_in_negated_context(self):
        """ARCH-0743"""
        pattern = re.compile(r"\bn8n\b")
        for name, text in _ALL_DOCS.items():
            for m in pattern.finditer(text):
                self.assertTrue(
                    _negated_context(text, m),
                    f"{name}: 'n8n' found outside a forbidden/negated context"
                )


# ── ARCH-0744: no MCP/filesystem agent on personal files ─────────────────────

class TestNoMCPAgentOnPersonalFiles(unittest.TestCase):

    def test_mcp_agent_only_in_negated_context(self):
        """ARCH-0744"""
        pattern = re.compile(r"\bMCP\b.*?(?:agent|personal|personali)", re.DOTALL)
        for name, text in _ALL_DOCS.items():
            for m in pattern.finditer(text):
                self.assertTrue(
                    _negated_context(text, m),
                    f"{name}: MCP agent reference on personal files found outside negated context"
                )


# ── ARCH-0745..0747: no operative move/rename/delete instructions ─────────────

class TestNoOperativeDestructiveInstructions(unittest.TestCase):

    _DESTRUCTIVE_PATTERNS = [
        (r"\bmove\s+(?:reali?|file personali)", "operative move on personal files"),
        (r"\brename\s+(?:reali?|file personali)", "operative rename on personal files"),
        (r"\bdelete\s+(?:reali?|file personali)", "operative delete on personal files"),
        (r"\bspostamento\s+reale", "spostamento reale su file personali"),
        (r"\brinomina\s+reale", "rinomina reale su file personali"),
        (r"\bcancellazione\s+reale", "cancellazione reale su file personali"),
    ]

    def test_no_operative_move_rename_delete(self):
        """ARCH-0745/0746/0747"""
        for pat_str, label in self._DESTRUCTIVE_PATTERNS:
            regex = re.compile(pat_str, re.IGNORECASE)
            for name, text in _ALL_DOCS.items():
                for m in regex.finditer(text):
                    self.assertTrue(
                        _negated_context(text, m),
                        f"{name}: '{label}' found outside a negated/forbidden context"
                    )


# ── ARCH-0748: V1_READINESS.md — spazio recuperabile is theoretical ──────────

class TestV1ReclaimableSpaceIsTheoretical(unittest.TestCase):

    def test_v1_spazio_recuperabile_theoretical(self):
        """ARCH-0748"""
        lower = _V1.lower()
        self.assertTrue(
            "spazio recuperabile" in lower or "reclaimable" in lower,
            "docs/V1_READINESS.md must mention 'spazio recuperabile' or 'reclaimable'"
        )
        self.assertTrue(
            "teorico" in lower or "theoretical" in lower or "puramente teorico" in lower,
            "docs/V1_READINESS.md must state the reclaimable space is theoretical"
        )


# ── ARCH-0749: V1_READINESS.md — no deletion proposed ───────────────────────

class TestV1NoDeletionProposed(unittest.TestCase):

    def test_v1_no_deletion_proposed(self):
        """ARCH-0749"""
        lower = _V1.lower()
        self.assertTrue(
            "nessuna cancellazione" in lower
            or "no deletion" in lower
            or "no delete" in lower
            or "nessuna proposta di cancellazione" in lower,
            "docs/V1_READINESS.md must state no deletion is proposed"
        )


# ── ARCH-0750: README.md links/mentions V1_READINESS.md ─────────────────────

class TestReadmeMentionsV1Readiness(unittest.TestCase):

    def test_readme_mentions_v1_readiness(self):
        """ARCH-0750"""
        self.assertIn(
            "V1_READINESS.md", _README,
            "README.md must link or mention docs/V1_READINESS.md"
        )


# ── ARCH-0751: COMMANDS.md links/mentions V1_READINESS.md ───────────────────

class TestCommandsMentionsV1Readiness(unittest.TestCase):

    def test_commands_mentions_v1_readiness(self):
        """ARCH-0751"""
        self.assertIn(
            "V1_READINESS.md", _COMMANDS,
            "docs/COMMANDS.md must link or mention docs/V1_READINESS.md"
        )


# ── ARCH-0752: V1_READINESS.md has stop criteria section ────────────────────

class TestV1HasStopCriteriaSection(unittest.TestCase):

    def test_v1_stop_criteria_heading(self):
        """ARCH-0752"""
        lower = _V1.lower()
        self.assertTrue(
            "criteri di stop" in lower
            or "stop criteria" in lower
            or "stop condition" in lower,
            "docs/V1_READINESS.md must have a section on stop criteria"
        )


# ── ARCH-0753: V1_READINESS.md has intentional v1 limits section ─────────────

class TestV1HasIntentionalLimitsSection(unittest.TestCase):

    def test_v1_intentional_limits_heading(self):
        """ARCH-0753"""
        lower = _V1.lower()
        self.assertTrue(
            "limiti intenzionali" in lower
            or "intentional limits" in lower
            or "intended limits" in lower,
            "docs/V1_READINESS.md must have a section on intentional v1 limits"
        )


# ── ARCH-0754: V1_READINESS.md has v1 ready definition section ───────────────

class TestV1HasReadinessDefinitionSection(unittest.TestCase):

    def test_v1_ready_definition_heading(self):
        """ARCH-0754"""
        lower = _V1.lower()
        self.assertTrue(
            "definizione di v1 pronta" in lower
            or "definition of v1" in lower
            or "pronto per v1" in lower
            or "v1 ready" in lower,
            "docs/V1_READINESS.md must have a section defining when v1 is ready"
        )


# ── ARCH-0755: docs use PowerShell examples for Windows, not Bash paths ───────

class TestPowerShellExamplesForWindows(unittest.TestCase):

    def test_no_bash_style_windows_paths_in_code_blocks(self):
        """ARCH-0755: code blocks must not use bash-style paths for Windows scripts."""
        bash_windows_path = re.compile(
            r'```(?:bash|sh)\n.*?python\s+scripts/', re.DOTALL
        )
        for name, text in _ALL_DOCS.items():
            m = bash_windows_path.search(text)
            self.assertIsNone(
                m,
                f"{name}: found bash/sh code block with Windows-style Python script path"
            )

    def test_powershell_blocks_present_in_commands(self):
        """ARCH-0755: COMMANDS.md must use powershell code blocks."""
        self.assertIn("```powershell", _COMMANDS,
                      "docs/COMMANDS.md must contain powershell code blocks")

    def test_powershell_blocks_present_in_v1_readiness(self):
        """ARCH-0755: V1_READINESS.md must use powershell code blocks."""
        self.assertIn("```powershell", _V1,
                      "docs/V1_READINESS.md must contain powershell code blocks")


if __name__ == "__main__":
    unittest.main()
