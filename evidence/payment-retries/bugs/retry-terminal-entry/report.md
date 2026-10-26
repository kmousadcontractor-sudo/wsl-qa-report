# QA-RETRY-02: Manual retry preparation can accept terminal entries that retain FAILED charge eligibility

Status: Reproduced. Not in Jira. P2 suggested.
Environment: Local application + disposable Postgres. Matrix: RET-067, RET-078.

## Summary
retry_payment_prepare does not independently reject Withdrawn, Removed, Not selected or Expired entries when the charge store still exposes a retryable FAILED charge.

## Evidence scope
The DB reproduction intentionally bypasses application withdrawal orchestration. Normal application withdrawal + alternate promotion stopped the old scheduled retry in a separate passing test; existing withdrawn dev fixtures returned HTTP 409. Do not interpret this finding as every ordinary withdrawal continuing to charge.

## Impact
A stale or inconsistently exposed FAILED charge can bypass entry lifecycle expectations at the manual-retry gate. Production reachability and provider collection are not established by these tests.

## Steps
1. Local application probe: expose a FAILED charge on a terminal entry. Repeat with Withdrawn, Removed, Not selected and Expired.
2. Call retry_payment_prepare with Tour Manager authorization and a new request ID.
3. Assert chargeable=False and that no execute is staged. Observe the failing status variants.
4. Database probe: create an entry with a declined charge in disposable Postgres, then withdraw through the repository directly.
5. Call real retry_payment_prepare in that transaction; observe chargeable=True and execute staging.
6. Compare with the complete application withdrawal + alternate promotion safe-path test, which cancels the charge and emits no old-entry scheduled execute.

## Expected
chargeable=False; no execute command staged for a terminal entry.

## Actual
chargeable=True in four terminal-status unit variants; repository-only withdrawal also allowed a new retry in Postgres.

## Technical investigation
F-02 — Manual retry preparation lacks an entry lifecycle guard

- Matrix: RET-067 and RET-078. Suggested priority: P2 for a defensive payment gate, with production reachability investigation required.
- Source: `wsl-competition-service/src/competition/application/entries.py:660`, `retry_payment_prepare`.
- Preconditions: a terminal entry still has an exposed FAILED charge eligible for manual retry.
- Reproduction A: parameterized application tests expose such a charge on Withdrawn, Removed, Not selected, and Expired entries; call manual retry preparation as Tour Manager.
- Reproduction B: in disposable Postgres, create and decline a charge, call the withdrawal repository directly, then call real manual retry preparation in the transaction.
- Expected: refuse the retry and stage no execute command for a terminal entry.
- Actual: preparation returned `chargeable=True`; execute was staged. Four unit variants and one real-DB acceptance assertion failed.
- Cause: preparation checks the exposed charge ID and claims the charge, without checking the current entry lifecycle.
- Critical scope distinction: reproduction B deliberately bypasses the application withdrawal orchestration. The complete application withdrawal path cancels charge eligibility and emits a release. A separate real-DB test running application withdrawal, alternate promotion, and the retry worker **passed**, with the old charge CANCELLED and no new scheduled execute. Fresh retries against the existing withdrawn dev fixtures also returned HTTP 409. This is not evidence that every ordinary withdrawal continues charging.
- Evidence: `lifecycle.xml`, `regressions-db.xml`; supporting safe-path evidence in `alternate-db.xml` and live retry JSON.
- Backend direction: enforce lifecycle eligibility at the transactional retry claim, then recheck at execution where practical. Preserve idempotent release and reconcile in-flight payment outcomes. A stale FAILED row must not be enough to charge a removed entrant.


## Fix acceptance criteria
- Reject manual retry for all terminal entry states even when a stale FAILED charge remains.
- Keep eligibility checks and retry claim in the appropriate transaction/lock scope.
- Verify ordinary withdrawal cancellation, alternate promotion, concurrent execute/release, and paid-entry refusal.

## Recording
Fresh backend test execution, not application UI. Started 2026-10-21T12:15:19.451Z. Captured output: recorded-output.txt; XML: rerun.xml; video: reproduction.webm.

No Jira ticket or application fix created.
