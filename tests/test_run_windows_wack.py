import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import run_windows_wack as module


class RunWindowsWackTests(unittest.TestCase):
    def test_expected_msix_path_uses_store_config_override(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            expected = (root / "custom" / "SoftwareCenter-store.msix").resolve()
            config = {"app_name": "SoftwareCenter", "msix_path": "custom/SoftwareCenter-store.msix"}

            self.assertEqual(module.expected_msix_path(root, config), expected)

    def test_resolve_report_path_uses_windowsstore_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            report_path = module.resolve_report_path(root)

            self.assertEqual(report_path.parent, (module.DEFAULT_REPORT_DIR).resolve())
            self.assertTrue(report_path.name.startswith(module.WACK_REPORT_PREFIX))
            self.assertEqual(report_path.suffix, ".xml")

    def test_parse_wack_report_counts_requirement_results(self):
        report_xml = """<?xml version="1.0" encoding="utf-8"?>
<REPORT>
  <OVERALL_RESULT>PASS</OVERALL_RESULT>
  <REQUIREMENT>
    <OVERALL_RESULT>PASS</OVERALL_RESULT>
  </REQUIREMENT>
  <REQUIREMENT>
    <OVERALL_RESULT>WARNING</OVERALL_RESULT>
  </REQUIREMENT>
  <REQUIREMENT>
    <OVERALL_RESULT>FAIL</OVERALL_RESULT>
  </REQUIREMENT>
</REPORT>
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "wack.xml"
            report_path.write_text(report_xml, encoding="utf-8")

            summary = module.parse_wack_report(report_path)

            self.assertEqual(summary.overall_result, "PASS")
            self.assertEqual(summary.requirement_count, 3)
            self.assertEqual(summary.pass_count, 1)
            self.assertEqual(summary.warning_count, 1)
            self.assertEqual(summary.fail_count, 1)

    def test_parse_wack_report_falls_back_to_test_nodes(self):
        report_xml = """<?xml version="1.0" encoding="utf-8"?>
<REPORT>
  <RESULT>FAIL</RESULT>
  <TEST Result="PASS" />
  <TEST Result="WARNING" />
</REPORT>
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "wack.xml"
            report_path.write_text(report_xml, encoding="utf-8")

            summary = module.parse_wack_report(report_path)

            self.assertEqual(summary.overall_result, "FAIL")
            self.assertEqual(summary.requirement_count, 2)
            self.assertEqual(summary.pass_count, 1)
            self.assertEqual(summary.warning_count, 1)
            self.assertEqual(summary.fail_count, 0)

    def test_write_summary_creates_utf8_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            summary = module.WackSummary(
                report="C:/temp/wack.xml",
                overall_result="PASS",
                requirement_count=4,
                pass_count=4,
                fail_count=0,
                warning_count=0,
            )
            summary_path = Path(tmpdir) / "wack.json"

            written_path = module.write_summary(summary, summary_path, exit_code=0)

            payload = json.loads(written_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["report"], "C:/temp/wack.xml")
            self.assertEqual(payload["overall_result"], "PASS")
            self.assertEqual(payload["exit_code"], 0)

    def test_run_command_returns_winerror_instead_of_traceback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "wack.log"
            error = OSError("Der angeforderte Vorgang erfordert erhöhte Rechte")
            error.winerror = 740

            with mock.patch.object(module.subprocess, "run", side_effect=error):
                exit_code = module.run_command(["appcert.exe", "reset"], log_path)

            self.assertEqual(exit_code, 740)
            self.assertIn("Befehl konnte nicht gestartet werden", log_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
