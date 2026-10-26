# WSL-9742: Payment retries: completed 24-hour slot is selected again and dispatches an extra execute at the exact boundary

https://wslproduct.atlassian.net/browse/WSL-9742
Priority: Medium

## Simple summary
After the first automatic retry is sent, a failure processed at exactly the 24-hour timestamp can select that same slot again. The next local worker tick emits a second execute command instead of waiting for the 72-hour slot.

Confirmed in local domain/application tests. An extra Stripe capture has not been demonstrated.

## Detailed report and evidence
- [Original detailed bug report](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/retry-consumed-offset/)
- [Latest rerun, UI observations and graphs](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/rerun-ui-impact-2026-10-21/#retry-slot)
- [Original domain test log](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/rerun-ui-impact-2026-10-21/retry-consumed-offset.txt)
- [Domain JUnit XML](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/rerun-ui-impact-2026-10-21/retry-consumed-offset.xml)
- [Worker impact log with failing exact-time and passing +1ms cases](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/rerun-ui-impact-2026-10-21/retry-worker-impact.txt)
- [Worker JUnit XML](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/rerun-ui-impact-2026-10-21/retry-worker-impact.xml)
- [Executable application probe](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/rerun-ui-impact-2026-10-21/worker-probe.py)
- [Original boundary test source](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/execution-2026-10-21/test_retry_matrix_boundaries.py)
- [Recorded domain rerun](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/rerun-ui-impact-2026-10-21/retry-consumed-offset.webm)
- [Recorded worker rerun](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/rerun-ui-impact-2026-10-21/retry-worker-impact.webm)
- [Failure screenshot](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/rerun-ui-impact-2026-10-21/retry-worker-impact.png)
- [Actual dev Payment rules screenshot](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/rerun-ui-impact-2026-10-21/payment-rules-panel.png)
- [Actual dev Settings recording, read-only](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/rerun-ui-impact-2026-10-21/ui-payment-rules.webm)

## Environment and scope
- Matrix RET-028; local report QA-RETRY-01.
- Executed 21 October 2026.
- Local checked-out competition service; Python 3.14 isolated test environment.
- Actual application scheduling functions with fake collaborators and explicitly injected clocks. This worker probe is not a real database/broker/provider integration.
- Policy values match dev version 16: retries 24/72h, grace 168h, notices 24/72/120/168h, short-notice cutoff 10 days.
- Deployed source revision was not verified. No dev database timestamps, rules or global clock were changed.

## Preconditions
A retryable failure at T0, one automatic retry already sent at T0+24h, retries_sent=1, and a deadline beyond the next retry. T0 is an artificial test clock, not a live execution timestamp.

## Steps to reproduce: domain
1. Supply the above policy and first_failed_at=T0.
2. Call next_retry_at with retries_sent=1 and now=T0+24h exactly.
3. Inspect the returned due timestamp.

Expected: T0+72h.
Actual: T0+24h, the already-consumed slot.

## Steps to reproduce: application worker impact
1. Create the isolated application world using explicit version-16 rules.
2. Record the first failure at T0.
3. Run the real scheduling tick at T0+24h; it emits the first execute.
4. Process that retry's failure with exactly the same injected timestamp.
5. Run the next scheduling tick at that timestamp.
6. Repeat using a failure timestamp 1ms later as a control.

Expected: no second execute at the completed 24-hour slot; next eligible slot is 72h.
Actual: exact-time variant emits a second execute. The +1ms control correctly avoids it.

## Captured backend output
```text
answer_delay_ms=0
next_due=2026-10-02 12:00:00+00:00
second_tick_retries=1
execute_commands=2
AssertionError: Completed 24h retry was dispatched again after its same-instant failure result
1 failed, 1 passed
```
The absolute date comes from the worker fixture. Original domain rerun also failed. Exit code 1 is an acceptance failure, not a setup failure.

## Flow graph
![Exact-time retry reuse versus +1ms control](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/rerun-ui-impact-2026-10-21/retry-slot-flow.svg)

[Open/download the flow graph](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/rerun-ui-impact-2026-10-21/retry-slot-flow.svg)

```text
First failure -> 24h retry sent
  -> failure processed at exactly 24h -> used 24h slot selected again -> extra execute
  -> failure processed at 24h + 1ms  -> 72h selected -> no extra execute now
```

## What the UI showed
Dev Payment rules & engine lists two attempts: 24 hours and 3 days. No clock-advance control was found in the inspected panel or row actions. A manual retry tests a different path; the exact automatic boundary was not reproduced through the UI.

## Technical investigation
competition/domain/payment_retries.py:80, next_retry_at:
- retries_sent only guards total schedule exhaustion.
- The loop starts at the first configured offset and accepts due >= now.
- That allows an already-consumed slot to be selected again at equality.
The application scheduling test confirms a second command under this controlled condition; it does not prove provider execution.

## Impact, limits and priority
Medium / P2 suggested: potential extra retry dispatch and retry-budget misuse. Exact-clock reachability with deployed timestamp precision, gateway attempts and customer impact still need investigation. No duplicate Stripe capture was established.

## Fix acceptance criteria
1. Never reuse a consumed retry slot, including exact-time outcomes and redeliveries.
2. Preserve the passing +1ms case and skip-past scheduling.
3. Cover consumed/skipped offsets, exhausted schedules, manual failures, late results, concurrency and idempotency.
4. Confirm one provider attempt per permitted execute in an isolated full integration.
5. Keep first-failure anchoring and pinned policy behavior intact.

No application fix, production money movement or refund was performed.
