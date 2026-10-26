# QA-RETRY-01: Retry scheduler selects the completed 24-hour slot again at the exact boundary

Status: Reproduced. Tracked in WSL-9742. P2 suggested.
Environment: Local source / domain function. Matrix: RET-028.

## Summary
After one configured retry is marked sent, next_retry_at can return the already-used 24-hour timestamp instead of the next 72-hour timestamp.

## Evidence scope
No duplicate Stripe collection was reproduced. This page records an exact-boundary function failure, not an observed customer double charge.

## Impact
The scheduling calculation can reuse a completed slot. Whether this produces an extra provider attempt remains unproven; downstream claim and idempotency controls were not bypassed.

## Steps
1. Use version-16 rules: retries 24/72h, notices 24/72/120/168h, grace 168h, short-notice cutoff 10 days.
2. Set first_failed_at to 2026-10-20 12:00 UTC, failure_class to retryable, retries_sent to 1, and deadline to T0+168h.
3. Invoke the real next_retry_at function with now exactly T0+24h.
4. Compare the returned due timestamp with T0+72h.

## Expected
T0 + 72 hours: 2026-10-23 12:00 UTC.

## Actual
T0 + 24 hours: 2026-10-21 12:00 UTC, despite retries_sent=1.

## Technical investigation
F-01 — Completed retry offset can be selected again at exact boundary

- Matrix: RET-028. Suggested priority: P2, pending confirmation of impact through the complete result-consumer path.
- Source: `wsl-competition-service/src/competition/domain/payment_retries.py:80`, `next_retry_at`.
- Preconditions: version-16 policy, retryable failure, T0 = 20 October 2026 12:00 UTC, retry offsets 24 and 72 hours, grace 168 hours, `retries_sent=1`.
- Reproduction: call the real function with `now=T0+24h` after the first retry is recorded as sent.
- Expected: next due is 23 October 2026 12:00 UTC (T0+72h).
- Actual: next due is 21 October 2026 12:00 UTC (T0+24h), the already-used offset.
- Cause: the count only guards schedule exhaustion; the loop starts from the first configured offset and accepts `due >= now`.
- Evidence: `boundaries.xml`, `test_completed_retry_offset_is_not_rescheduled_at_same_instant`, failed assertion retained.
- Impact limit: this proves a scheduling calculation defect. A second provider charge was not demonstrated; worker claim/idempotency gates may reduce the end-to-end impact.
- Backend direction: track consumed schedule positions explicitly and preserve skip-past behavior. Test first-failure handling, delayed answers, manual failures, skipped offsets, and exact-time redeliveries before changing count semantics.


## Fix acceptance criteria
- At the exact consumed offset, select the next unconsumed slot.
- Verify minus/exact/plus 1ms, exhausted schedules, skipped offsets, delayed outcomes, manual failures and idempotent dispatch.

## Recording
Fresh backend test execution, not application UI. Started 2026-10-21T12:15:03.983Z. Captured output: recorded-output.txt; XML: rerun.xml; video: reproduction.webm.

Tracked in WSL-9742. No application fix created.

## Latest UI impact rerun
The scheduler can reuse the first retry time. In the exact-time local worker test it sent a second execute command. Moving the result just 1 millisecond later avoided that extra command.

See ../rerun-ui-impact-2026-10-21/report.md and the linked SVG flow graphs for fresh evidence and scope.

## Jira tracking

[WSL-9742](https://wslproduct.atlassian.net/browse/WSL-9742) · Priority Medium.

[Complete detailed ticket report with logs, backend validation and evidence](jira-report.md).
