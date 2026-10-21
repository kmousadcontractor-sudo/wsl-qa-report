# QA-RETRY-03: Competition ignores a successful payment result after withdrawal cancels the charge

Status: Reproduced. Not in Jira. P2 suggested.
Environment: Local repository / disposable Postgres. Matrix: RET-087.

## Summary
record_charge_result returns None for a late successful result when the competition charge has already become CANCELLED, leaving no reconciliation update from this repository method.

## Evidence scope
This test injects a successful result at a repository boundary. It does not hold a live Stripe request, replay the entire webhook/broker chain, prove absence of all Finance records, or authorize a refund.

## Impact
The competition component can lose visibility of a late successful financial outcome. Provider capture, Finance visibility elsewhere, and refund eligibility were not established.

## Steps
1. Create a REQUESTED competition charge in disposable Postgres using the real test fixtures.
2. Withdraw the entry through the repository so its REQUESTED charge becomes CANCELLED.
3. Call the real record_charge_result with succeeded=True and failure_code=None, simulating a late success.
4. Read the returned detail and charge state.
5. Observe None and CANCELLED instead of a reconciliation outcome; inspect the retained failing acceptance assertion.

## Expected
Keep the entrant withdrawn and record or route the late successful financial outcome for reconciliation.

## Actual
record_charge_result returned None; the competition charge remained CANCELLED.

## Technical investigation
F-03 — Late success is ignored after competition charge cancellation

- Matrix: RET-087. Suggested priority: P2 for reconciliation visibility; financial impact requires provider/Finance correlation.
- Source: `wsl-competition-service/src/competition/infrastructure/persistence/repositories/events/entries.py:379`, `record_charge_result`.
- Preconditions: a REQUESTED competition charge is cancelled by withdrawal while an external attempt may already have started.
- Reproduction: create REQUESTED charge in disposable Postgres, withdraw through the repository, then deliver `succeeded=True` to the real charge-result repository method.
- Expected: preserve the terminal entry and record or route the late financial success for reconciliation.
- Actual: method returned `None`; the competition charge remained CANCELLED. The acceptance assertion failed.
- Cause: update permits OPEN and FAILED charge statuses; CANCELLED is excluded and produces an early return.
- Impact limit: the probe targets this component. It did not hold an actual provider request in flight, replay a complete live webhook/broker chain, prove a missing Finance record elsewhere, or establish a refund obligation.
- Evidence: `regressions-db.xml`, `test_late_success_is_not_lost_after_withdrawal_cancels_requested_charge`.
- Backend direction: maintain an immutable payment outcome or reconciliation record for late success without restoring the withdrawn entrant. Decide refund/manual review policy with Finance and make processing idempotent.


## Fix acceptance criteria
- Late success must be idempotently visible for reconciliation without restoring a withdrawn entrant.
- Verify duplicate and out-of-order outcomes, success after release, and provider/Finance correlation.
- Agree refund versus manual-review behavior before making that financial decision automatic.

## Recording
Fresh backend test execution, not application UI. Started 2026-10-21T12:15:33.828Z. Captured output: recorded-output.txt; XML: rerun.xml; video: reproduction.webm.

No Jira ticket or application fix created.

## Latest UI impact rerun
The local charge-result method ignores success after its charge is cancelled. In the separate real UI run, however, payment success appeared in history after withdrawal. That UI run did not reproduce a missing success record.

See ../rerun-ui-impact-2026-10-21/report.md and the linked SVG flow graphs for fresh evidence and scope.
