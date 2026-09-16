"""Regression tests for payment-to-invoice matching.

Bug: find_invoice() matched a payment to any invoice with the same amount,
across all customers, before even checking customer_id and invoice_number.
The business rules are explicit: "A new payment may be attached only to an
invoice with both the same customer ID and invoice number. An amount alone
does not establish identity." A payment could silently attach to a totally
different customer's invoice just because the amounts happened to match.
"""
import tempfile
import unittest
from pathlib import Path
from ledger import storage, matching


class PaymentMatchingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = storage.connect(Path(self.tmp.name) / 'test.sqlite3')
        storage.seed(self.db)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_payment_does_not_attach_to_a_different_customers_invoice(self):
        """Reproduces the reported bug. HARBOR/INV-100 and MAPLE/INV-200 both
        have amount 1250.00 in the seed data. A payment explicitly addressed
        to MAPLE/INV-200 must never resolve to HARBOR/INV-100."""
        payment = {'customer_id': 'MAPLE', 'invoice_number': 'INV-200', 'amount': 1250.00}
        invoice_id = matching.find_invoice(self.db, payment)
        correct_invoice = storage.invoice_by_key(self.db, 'MAPLE', 'INV-200')
        wrong_invoice = storage.invoice_by_key(self.db, 'HARBOR', 'INV-100')
        self.assertEqual(invoice_id, correct_invoice['id'])
        self.assertNotEqual(invoice_id, wrong_invoice['id'])

    def test_matching_amount_with_wrong_identity_finds_nothing(self):
        """My own case. If the amount matches an invoice but the customer or
        invoice number doesn't, there must be no match at all, not a fallback
        to whichever invoice happens to share the amount."""
        payment = {'customer_id': 'MAPLE', 'invoice_number': 'DOES-NOT-EXIST', 'amount': 1250.00}
        invoice_id = matching.find_invoice(self.db, payment)
        self.assertIsNone(invoice_id)

    def test_correct_identity_still_matches_normally(self):
        """My own case. A normal, correctly addressed payment must still work."""
        payment = {'customer_id': 'HARBOR', 'invoice_number': 'INV-101', 'amount': 300.00}
        invoice_id = matching.find_invoice(self.db, payment)
        expected = storage.invoice_by_key(self.db, 'HARBOR', 'INV-101')
        self.assertEqual(invoice_id, expected['id'])


if __name__ == '__main__':
    unittest.main()