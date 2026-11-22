"""Regression test for E16: suspicious_access crashed on an event whose `message` is a string.

Study 2 lost the record.json of 4 trials this way (RESULTS-STUDY2.md, "Not in the primary"). The fixture is the real
transcript of one of them.
"""

import json
import unittest
from pathlib import Path

from run_trial import suspicious_access

TRIAL = Path(__file__).resolve().parent.parent / "runs" / "study2" / "0403-control-feature-toml-config-r109"


class SuspiciousAccess(unittest.TestCase):
    def test_string_message_does_not_crash(self):
        events = [json.loads(x) for x in (TRIAL / "agent.stdout").read_text().splitlines() if x.startswith("{")]
        self.assertTrue(any(isinstance(e.get("message"), str) for e in events), "fixture lost its string message")
        self.assertIsInstance(suspicious_access(events, Path("/nonexistent-workspace")), list)

    def test_still_flags_hidden_material(self):
        ev = {"type": "assistant", "message": {"content": [{"type": "tool_use", "input": {"command": "cat ../overclaim/x"}}]}}
        self.assertTrue(suspicious_access([ev, {"type": "system", "message": "Permission denied"}], Path("/w")))


if __name__ == "__main__":
    unittest.main()
