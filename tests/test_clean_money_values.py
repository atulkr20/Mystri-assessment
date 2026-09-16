"""Tests for the improvement: money is rounded once, at the source.

Rationale: the export rounding bug happened because export_csv had its own,
separate rounding logic instead of trusting clean values from invoices().
Rounding at the source means every consumer, the screen, the export, the raw
JSON API, or anything built later, automatically gets correct 2-decimal
values without having to remember to round correctly on its own.
"""
import tempfile
import unittest
from pathlib import Path
from ledger import storage, reporting


class CleanMoneyValuesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = storage.connect(Path(self.tmp.name) / 'test.sqlite3')
        storage.seed(self.db)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_invoices_returns_already_rounded_values(self):
        """The raw API-level values must be clean, not just the CSV export."""
        row = next(r for r in reporting.invoices(self.db) if r['invoice_number'] == 'INV-300')
        self.assertEqual(row['amount'], 19.99)
        self.assertEqual(row['balance'], 9.99)

    def test_overview_outstanding_still_matches_the_sum_of_balances(self):
        """My own case. The improvement must not change the overview's total."""
        rows = reporting.invoices(self.db)
        summary = reporting.overview(self.db)['summary']
        expected = round(sum(max(0, r['balance']) for r in rows), 2)
        self.assertEqual(summary['outstanding'], expected)


if __name__ == '__main__':
    unittest.main()