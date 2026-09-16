"""Regression tests for the invoice register status filter.

Bug: asking for 'open' invoices returned paid invoices instead, because the
status lookup mapped both 'open' and 'paid' to 'paid' in reporting.invoices().
"""
import tempfile
import unittest
from pathlib import Path
from ledger import storage, reporting


class StatusFilterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = storage.connect(Path(self.tmp.name) / 'test.sqlite3')
        storage.seed(self.db)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_open_filter_returns_only_open_invoices(self):
        """Reproduces the reported bug. Fails before the fix, passes after."""
        rows = reporting.invoices(self.db, status='open')
        self.assertGreater(len(rows), 0, 'seed data should contain open invoices')
        for row in rows:
            self.assertEqual(row['status'], 'open')

    def test_paid_filter_returns_only_paid_invoices(self):
        """My own case. The fix must not break the paid filter."""
        rows = reporting.invoices(self.db, status='paid')
        for row in rows:
            self.assertEqual(row['status'], 'paid')

    def test_open_filter_count_matches_overview(self):
        """My own case. The table and the overview must agree."""
        open_rows = reporting.invoices(self.db, status='open')
        summary = reporting.overview(self.db)['summary']
        self.assertEqual(len(open_rows), summary['open_count'])

    def test_filters_add_up_to_all(self):
        """My own case. Every invoice is either open or paid, never both."""
        all_rows = reporting.invoices(self.db, status='all')
        open_rows = reporting.invoices(self.db, status='open')
        paid_rows = reporting.invoices(self.db, status='paid')
        self.assertEqual(len(open_rows) + len(paid_rows), len(all_rows))


if __name__ == '__main__':
    unittest.main()