from __future__ import annotations

import unittest
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from communication.services import validate_report_workbook


DATA_DIR = Path(__file__).resolve().parents[3] / "data"


class ValidateReportWorkbookTests(unittest.TestCase):
    def test_valid_sample_report(self):
        workbook_path = DATA_DIR / "G. RIP100000_Q1_2025.xlsx"
        result = validate_report_workbook(workbook_path)

        self.assertEqual(result.status, "validated")
        self.assertEqual(result.errors, [])
        self.assertTrue(result.forms)
        self.assertEqual(result.metadata.get("entity_identifier"), "RIP1000000")
        self.assertEqual(result.metadata.get("period_start"), "2025-01-01")
        self.assertEqual(result.metadata.get("period_end"), "2025-03-31")

    def test_invalid_sample_report(self):
        workbook_path = DATA_DIR / "G. RIP100000_Q2_2025.xlsx"
        result = validate_report_workbook(workbook_path)

        self.assertEqual(result.status, "validation_errors")

        error_codes = {error.code for error in result.errors}
        self.assertIn("ENTITY_ID_FORMAT", error_codes)
        self.assertIn("TOTAL_COUNT_MISMATCH", error_codes)
        self.assertIn("TOTAL_VALUE_MISMATCH", error_codes)
        self.assertGreaterEqual(len(result.errors), 3)


if __name__ == "__main__":
    unittest.main()
