# Handover

- Name: Atul Jha
- Email used for this application: atuljha21542@gmail.com
- Chosen track: A — Product engineering
- Why this track: I'd rather fix and improve real, working software than do open-ended research. Repairing a live app on real data felt closer to actual day-to-day engineering work. And i am not into Rresearch thing that much
- Approximate total time, including setup and handover: 2 - 3 hrs

## Run and verify

```
python app.py
```
Opens on `http://127.0.0.1:8787`. No dependencies to install, just Python 3.10+.

To load the owner's real data before testing:
```
python restore_fixture.py --replace
```

To run all tests:
```
python -m unittest discover -s tests -v
```
Expected: 21 tests, all passing.

## What I delivered

I found and fixed six bugs, spread across import, matching, reporting, and the browser UI:

1. **Status filter was backwards** (`ledger/reporting.py`) — asking for "open" invoices returned paid ones instead, because of a lookup table where both statuses pointed to `'paid'`. Test: `tests/test_status_filter.py`.
2. **Re-importing the same invoices created duplicates** (`ledger/storage.py`) — nothing checked if an invoice already existed before inserting it, so retrying an import doubled up records and inflated totals. Test: `tests/test_duplicate_invoice.py`.
3. **Payments could attach to the wrong customer's invoice** (`ledger/matching.py`) — the code matched payments by amount first, across all customers, instead of only by customer ID and invoice number. Fixed by matching on identity only.
4. **One bad row in a CSV killed the whole import** (`ledger/importing.py`) — validation ran on all rows before any of them were saved, so a single invalid row threw everything out, good rows included. Test: `tests/test_partial_import.py`.
5. **The browser showed "Import complete" even when it wasn't** (`web/app.js`) — the UI never checked whether the import actually succeeded before showing a success message. Checked by hand with a deliberately broken file.
6. **The exported CSV didn't match the screen** (`ledger/reporting.py`) — money was being rounded with a manual trick that cuts off decimals instead of rounding them properly, so values like 19.99 could show up as 19.98 in the export. Test: `tests/test_export_rounding.py`.

**Improvement:** money now gets rounded in exactly one place, where invoices are first put together, instead of each part of the app (screen, export, API) doing its own rounding. Bug 6 happened because two different parts of the code rounded money differently. Fixing it once at the source means that can't happen again. Test: `tests/test_clean_money_values.py`.

## Evidence and limits

Every bug above has its own test file. Each one includes a test that fails on the old code and passes after the fix, plus a couple of extra cases I added myself. I checked this both ways for every single fix, by putting the old buggy code back temporarily and confirming the test actually failed, then reapplying the fix and confirming it passed again.

I also restored the owner's real data, confirmed the starting numbers matched the spec (9 invoices, 7 open, ₹3,698.19 outstanding), imported new valid records, restarted the server, and confirmed both the old and new records were still there afterward.

**What I didn't do:** money is still stored as a plain float in the database, which is the root cause behind bug 6. A more complete fix would store it as whole cents instead of a float, but that touches several files and felt too risky to attempt properly in this time box. I'd flag that as the next thing worth doing.

## Tools and judgment

I used Claude to help me investigate the codebase, since I was new to it and wanted to move efficiently. For each bug, I had it explain what was actually wrong and why in plain terms before I touched any code, and I only accepted a fix once I'd seen proof it actually worked, meaning a test that failed on the broken code and passed once it was fixed. I ran every test myself and checked the results before moving to the next bug.

A couple of times I caught things going wrong on my own and flagged them rather than assuming success: once when a code paste broke the indentation, and once when a test file I'd saved wasn't actually being picked up by the test runner. Both times I described exactly what I was seeing rather than guessing at a fix.

For the improvement, I pushed for something realistic in the time I had rather than a bigger rewrite, and settled on fixing the rounding at its actual source instead of a full change to how money is stored.