"""Regression tests for partial CSV imports.

Bug: row validation happened before the per-row try/except, in a list
comprehension. One invalid row anywhere in the file raised before any row
reached the database, so a single bad row rejected the entire file instead
of just itself.
"""
import tempfile
import unittest
from pathlib import Path
from ledger import storage, importing


MIXED_CSV = (
    'customer_id,invoice_number,amount,due_date\n'
    'HARBOR,INV-103,84.00,2026-09-12\n'
    'NORTH,INV-302,not-a-number,2026-09-12\n'
    'MAPLE,INV-203,100.00,2026-09-13\n'
)


class PartialImportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = storage.connect(Path(self.tmp.name) / 'test.sqlite3')
        storage.seed(self.db)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_one_bad_row_does_not_reject_the_whole_file(self):
        """Reproduces the reported bug. Fails before the fix, passes after."""
        before = self.db.execute('SELECT COUNT(*) FROM invoices').fetchone()[0]
        result = importing.import_csv(self.db, MIXED_CSV, 'invoices')
        after = self.db.execute('SELECT COUNT(*) FROM invoices').fetchone()[0]
        self.assertEqual(result['imported'], 2)
        self.assertEqual(result['rejected'], 1)
        self.assertEqual(after, before + 2)

    def test_error_points_at_the_correct_line(self):
        """My own case. The rejected row's line number must be accurate."""
        result = importing.import_csv(self.db, MIXED_CSV, 'invoices')
        self.assertEqual(len(result['errors']), 1)
        self.assertEqual(result['errors'][0]['line'], 3)

    def test_all_valid_rows_still_import_cleanly(self):
        """My own case. A fully valid file must not be affected by this fix."""
        valid_csv = (
            'customer_id,invoice_number,amount,due_date\n'
            'HARBOR,INV-104,50.00,2026-09-12\n'
            'MAPLE,INV-204,60.00,2026-09-13\n'
        )
        result = importing.import_csv(self.db, valid_csv, 'invoices')
        self.assertEqual(result, {'imported': 2, 'skipped': 0, 'rejected': 0, 'errors': []})

    def test_all_invalid_rows_rejects_all_without_crashing(self):
        """My own case. A file that's entirely bad must not crash the import."""
        bad_csv = (
            'customer_id,invoice_number,amount,due_date\n'
            'HARBOR,INV-105,not-a-number,2026-09-12\n'
        )
        result = importing.import_csv(self.db, bad_csv, 'invoices')
        self.assertEqual(result['imported'], 0)
        self.assertEqual(result['rejected'], 1)


if __name__ == '__main__':
    unittest.main()