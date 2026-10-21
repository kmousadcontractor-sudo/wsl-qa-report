# WSL-9743: Payment reconciliation: competition charge-result method ignores late success after cancellation

https://wslproduct.atlassian.net/browse/WSL-9743
Priority: Medium

## Simple summary
The competition repository ignores a successful result once its charge is CANCELLED: it returns None and leaves the charge cancelled. A real-Postgres regression reproduces this component behavior.

Important UI result: a separate live withdrawal/card-recovery run DID record success in history. That UI run does not prove the ignored-result condition or payment loss across all services.

## Detailed report and evidence
- [Original detailed bug report](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/retry-late-success/)
- [Latest rerun with separate backend/UI findings](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/rerun-ui-impact-2026-10-21/#late-success)
- [Exact backend failure log](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/rerun-ui-impact-2026-10-21/retry-late-success.txt)
- [Postgres JUnit XML](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/rerun-ui-impact-2026-10-21/retry-late-success.xml)
- [Backend test source](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/execution-2026-10-21/test_retry_matrix_regressions.py)
- [Recorded Postgres regression rerun](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/rerun-ui-impact-2026-10-21/retry-late-success.webm)
- [Backend failure screenshot](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/rerun-ui-impact-2026-10-21/retry-late-success.png)
- [Actual UI withdrawal recording](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/rerun-ui-impact-2026-10-21/actual-ui-withdrawal.webm)
- [Read-only final-history review recording](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/rerun-ui-impact-2026-10-21/ui-history-review.webm)
- [Final UI history screenshot](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/rerun-ui-impact-2026-10-21/focused-history-review.png)
- [Timestamped API/UI observations and final history](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/rerun-ui-impact-2026-10-21/ui-results.json)

## Environment and scope
- Matrix RET-087; local report QA-RETRY-03.
- Backend: local competition repository with disposable Postgres 16.
- Test: test_late_success_is_not_lost_after_withdrawal_cancels_requested_charge.
- Live comparison: dev, Stripe test mode, 21 October 2026.
- Deployed source revision and full provider/broker correlation were not verified.
- No live outcome, broker event, shared rule, UUID or database timestamp was fabricated or changed.

## Preconditions and backend reproduction
1. Create an entry with a REQUESTED competition charge in disposable Postgres.
2. Withdraw through the repository so that the charge becomes CANCELLED.
3. Deliver succeeded=True and failure_code=None to the real record_charge_result repository method.
4. Inspect the return value and persisted competition charge.

Expected: preserve the withdrawn entrant and record or route late successful financial information for reconciliation, idempotently.
Actual: method returns None; the competition charge remains CANCELLED.

This deliberately invokes the repository boundary. It is not a full consumer-to-provider integration and does not demonstrate that another Finance record is absent.

## Captured backend output
```text
test_late_success_is_not_lost_after_withdrawal_cancels_requested_charge
AssertionError: Late successful payment ignored; local charge still cancelled; needs reconciliation
assert None is not None
1 failed, 1 warning in 36.96s
```
Exit code 1 is the reproduced acceptance failure.

## Backend flow graph
![Local repository late-success failure](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/rerun-ui-impact-2026-10-21/late-success-backend-flow.svg)

[Open/download backend flow graph](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/rerun-ui-impact-2026-10-21/late-success-backend-flow.svg)

```text
REQUESTED charge -> withdrawal -> CANCELLED
 -> succeeded=True delivered later
 -> method excludes CANCELLED -> returns None
 -> competition charge remains CANCELLED
```

## Actual dev UI attempt and result
Fresh event: 01a15e8d-00c4-732a-9f7a-a8293edfba1a
Entry: 01a15e8d-0b9f-747f-a902-cbcba6135ae6
[Open dev event](https://app.dev.worldsurfleague.com/tour-manager/events/01a15e8d-00c4-732a-9f7a-a8293edfba1a)

1. Genuine declining test card left the entrant Declined/Pending.
2. The athlete changed to a valid saved Visa through the real entry-card API.
3. The manager selected Withdraw entry, chose a reason and clicked Proceed in the actual UI.
4. Final row was Withdrawn, with payment null/dash and no actions.
5. Expanded history contained ONE Card payment succeeded line above Entry withdrawn, newest first.

Observed responses on 21 October 2026:
- 16:02:58.247 Africa/Cairo (13:02:58.247 UTC): valid-card update, HTTP 202.
- 16:02:59.654 Africa/Cairo (13:02:59.654 UTC): UI withdrawal response, HTTP 200.
- 16:03:00.578 Africa/Cairo (13:03:00.578 UTC): final roster/history readback.

These are response-observation times, not processor timestamps. Card replacement can itself initiate a retry. No manual retry was sent after withdrawal in this run.

## UI observation flow graph
![Actual UI sequence, success visible in history](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/rerun-ui-impact-2026-10-21/late-success-ui-flow.svg)

[Open/download actual UI flow graph](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/rerun-ui-impact-2026-10-21/late-success-ui-flow.svg)

```text
Decline -> valid card update (202) -> UI withdrawal (200)
 -> roster Withdrawn / payment dash
 -> expanded history shows success
 -> ignored-result condition not established by this UI run
```

## Technical investigation
competition/infrastructure/persistence/repositories/events/entries.py:379, record_charge_result:
- UPDATE accepts OPEN_CHARGE_STATUSES and FAILED.
- CANCELLED is excluded.
- Zero updated rows returns None before entry/result reconciliation.

The tested gap is local to this method. Trace the actual consumer, payment ledger and Finance outcome before attributing a missing live payment to it.

## Impact and relation to existing ticket
Medium / P2 suggested: potential competition-side reconciliation gap for a successful financial outcome after cancellation. Refund obligations, customer impact and provider ordering were not established.
Related: [WSL-9740](https://wslproduct.atlassian.net/browse/WSL-9740) tracks post-withdrawal MANUAL retry acceptance, a distinct entry-eligibility finding.

## Required trace and acceptance criteria
1. Correlate deferred-charge state, execute/release IDs, outcome delivery and Stripe PaymentIntent timestamps.
2. Preserve an immutable outcome or route late success into reconciliation without restoring the withdrawn entry.
3. Verify duplicate/out-of-order outcomes idempotently.
4. Add full consumer/broker/provider coverage proving visibility after cancellation.
5. Agree Finance/refund policy before introducing automatic financial action.
6. Keep normal withdrawal cancellation and alternate promotion behavior intact.

No application fix, refund or real-money transaction was performed.
