"""Regression tests for re-importing invoices.

Bug: insert_invoice() never checked whether an invoice with the same
(customer_id, invoice_number) already existed, so retrying an import created
duplicate rows and inflated totals instead of skipping already-known invoices.
"""
import tempfile
import unittest
from pathlib import Path
from ledger import storage, importing


NEW_INVOICES_CSV = (
    'customer_id,invoice_number,amount,due_date\n'
    'HARBOR,INV-102,80.00,2026-09-10\n'
    'MAPLE,INV-202,200.00,2026-09-11\n'
)


class DuplicateInvoiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = storage.connect(Path(self.tmp.name) / 'test.sqlite3')
        storage.seed(self.db)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_reimporting_identical_invoices_does_not_duplicate(self):
        """Reproduces the reported bug. Fails before the fix, passes after."""
        importing.import_csv(self.db, NEW_INVOICES_CSV, 'invoices')
        count_after_first = self.db.execute('SELECT COUNT(*) FROM invoices').fetchone()[0]
        result = importing.import_csv(self.db, NEW_INVOICES_CSV, 'invoices')
        count_after_second = self.db.execute('SELECT COUNT(*) FROM invoices').fetchone()[0]
        self.assertEqual(result['imported'], 0)
        self.assertEqual(result['skipped'], 2)
        self.assertEqual(count_after_second, count_after_first)

    def test_reusing_identity_with_different_amount_is_rejected(self):
        """My own case. A conflicting reuse of the same identity must not overwrite the original."""
        importing.import_csv(self.db, NEW_INVOICES_CSV, 'invoices')
        conflicting = 'customer_id,invoice_number,amount,due_date\nHARBOR,INV-102,999.00,2026-09-10\n'
        result = importing.import_csv(self.db, conflicting, 'invoices')
        self.assertEqual(result['rejected'], 1)
        row = self.db.execute(
            "SELECT amount FROM invoices WHERE customer_id='HARBOR' AND invoice_number='INV-102'"
        ).fetchone()
        self.assertEqual(row['amount'], 80.00)

    def test_first_time_import_still_works(self):
        """My own case. The fix must not block genuinely new invoices."""
        result = importing.import_csv(self.db, NEW_INVOICES_CSV, 'invoices')
        self.assertEqual(result['imported'], 2)
        self.assertEqual(result['skipped'], 0)


if __name__ == '__main__':
    unittest.main()