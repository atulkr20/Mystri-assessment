"""Regression tests for CSV export money formatting.

Bug: export_csv formatted money with int(x * 100) / 100, which truncates
instead of rounding. Combined with float representation error (e.g. 19.99
stored as 19.989999999999998), this silently shaved a cent off values,
making the exported report disagree with what the screen showed for the
exact same record.
"""
import tempfile
import unittest
from pathlib import Path
from ledger import storage, reporting


class ExportRoundingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = storage.connect(Path(self.tmp.name) / 'test.sqlite3')
        storage.seed(self.db)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_export_matches_the_screen_value(self):
        """Reproduces the reported bug. Fails before the fix, passes after."""
        on_screen = next(r for r in reporting.invoices(self.db) if r['invoice_number'] == 'INV-300')
        csv_text = reporting.export_csv(self.db)
        line = next(l for l in csv_text.splitlines() if 'INV-300' in l)
        exported_amount, exported_balance = line.split(',')[2], line.split(',')[4]
        self.assertEqual(exported_amount, f"{on_screen['amount']:.2f}")
        self.assertEqual(exported_balance, f"{on_screen['balance']:.2f}")

    def test_export_rounds_rather_than_truncates(self):
        """My own case. A value just under a cent boundary must round up, not down."""
        row = {'customer_id': 'x', 'invoice_number': 'y', 'amount': 9.989999999999998,
               'paid': 0, 'balance': 9.989999999999998, 'status': 'open'}
        formatted = f"{row['amount']:.2f}"
        self.assertEqual(formatted, '9.99')

    def test_export_still_has_two_decimal_places_for_whole_numbers(self):
        """My own case. Whole-number amounts must still show as X.00, not just X."""
        csv_text = reporting.export_csv(self.db)
        line = next(l for l in csv_text.splitlines() if 'INV-100' in l)
        self.assertIn('1250.00', line)


if __name__ == '__main__':
    unittest.main()