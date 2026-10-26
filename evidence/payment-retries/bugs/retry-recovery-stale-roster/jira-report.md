# WSL-9744: Tour Manager: roster stays Declined/Pending after successful card recovery until page refresh

https://wslproduct.atlassian.net/browse/WSL-9744
Priority: Low

## Simple summary
Payment recovery succeeds, but the manager's already-open roster remains Declined/Pending for the 90-second observation. Refreshing shows the correct Collected/Confirmed state.

Confirmed on dev using independent athlete and manager sessions. The backend readback was correct.

## Detailed report, recordings and logs
- [Detailed bug report](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/retry-recovery-stale-roster/)
- [Actual browser recording](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/execution-2026-10-21/recovery-recording.webm)
- [Before refresh: stale Declined/Pending](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/execution-2026-10-21/recovery-before-refresh.png)
- [After refresh: recovered payment](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/execution-2026-10-21/recovery-after-refresh.png)
- [Timestamped API/UI assertions, card-change responses, roster snapshots and history](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/execution-2026-10-21/recovery-results.json)
- [Complete execution report](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/execution-2026-10-21/)
- [Native test names, timings and results](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/execution-2026-10-21/native-tests.json)
- [Payment unit-test XML](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/execution-2026-10-21/payment-unit.xml)
- [Payment Postgres integration-test XML](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/execution-2026-10-21/payment-integration.xml)

## Environment and fixture
- Dev: https://app.dev.worldsurfleague.com
- Executed 21 October 2026; Stripe test mode.
- Matrix RET-105; local report QA-RETRY-04.
- Independent athlete request/browser context and authenticated manager browser context. The manager's cookies were not switched during observation.
- Event: 01a15d6d-df77-76f9-99fa-5cff13be3f99
- Entry: 01a15d6d-eb6b-762c-bf81-59240b572ff4
- [Open dev event](https://app.dev.worldsurfleague.com/tour-manager/events/01a15d6d-df77-76f9-99fa-5cff13be3f99)
- Deployed source revision and intended refresh SLA were not verified.

## Preconditions
The athlete is entered with a saved declining Stripe test card. Confirm and charge has genuinely declined, leaving Declined/Pending. A valid saved Visa is available. The manager keeps the Athletes tab open.

## Steps to reproduce
1. Open the declined entry in the manager Athletes tab.
2. In a separate authenticated athlete session, change the entry's saved card to the valid Visa.
3. Replay the same card-change idempotency key as a safety control.
4. Keep the manager tab open without refresh for 90 seconds.
5. Poll the real roster API independently and compare with the screen.
6. Inspect history and attempt a paid-entry retry as a guard control.
7. Refresh the manager page and reopen Athletes.

## Expected
Successful asynchronous recovery updates the open roster's payment status, entry status and summary counters within an agreed bounded refresh window. Unsaved seed edits must be preserved.

## Actual
- Valid-card change and replay returned HTTP 202.
- API payment reached collected and entry confirmed.
- The open roster stayed Declined/Pending throughout the 90-second observation.
- Exactly one successful history outcome was recorded.
- A subsequent paid-entry retry was rejected with HTTP 409.
- Reloading showed Collected and the corrected entry state.

## Timestamped execution log
21 October 2026, Africa/Cairo; raw JSON retains UTC:
```text
10:47:28.973 (07:47:28.973 UTC) Confirm and charge: 200
10:47:31.670 (07:47:31.670 UTC) Initial payment: declined
10:47:41.236 (07:47:41.236 UTC) Valid-card change: 202
10:47:41.535 (07:47:41.535 UTC) Same-key replay: 202
10:49:28.328 (07:49:28.328 UTC) API payment: collected
10:49:28.329 (07:49:28.329 UTC) API entry: confirmed
10:49:28.331 (07:49:28.331 UTC) Open UI showed Collected: false [FAIL]
10:49:28.333 (07:49:28.333 UTC) Successful history outcomes: 1
10:49:28.783 (07:49:28.783 UTC) Paid retry: 409
10:49:32.290 (07:49:32.290 UTC) After refresh shows Collected: true [PASS]
```
These are observation times, not an independently queried Stripe capture timeline.

## Flow
```text
Declined/Pending -> athlete selects valid card -> payment recovery succeeds
  -> API: Collected/Confirmed
  -> open manager UI: still Declined/Pending
  -> manager refreshes -> UI shows Collected/Confirmed
```

## Backend test evidence and interpretation
The 13-assertion live recovery run recorded 12 passes and one failure: RET-105 open-roster update. Backend collection, confirmation, same-key replay/history count and paid retry rejection all passed their live checks.

Related native backend controls also passed in the retained execution:
- payment-unit: test_happy_path_charges_the_pinned_saved_payment_method.
- payment-unit: test_charge_already_charging_is_rejected_without_a_second_gateway_call.
- payment-integration (Postgres): test_charge_lifecycle_ready_charging_paid.

These support payment behavior locally. There is NO failing backend regression claimed for this UI-refresh bug, and they do not prove the deployed revision matches the checkout. Full details and original XML are linked above.

## Technical investigation
Local source: src/features/tour-manager/hooks/use-tour-manager.ts:401, useSeedList, defines a query key/fetch function without an explicit polling interval. This is consistent with the stale screen, but deployed revision and all global invalidation/event mechanisms were not verified.
Investigate cache invalidation/refetch when recovery originates outside the current manager tab; refresh seed-list, summaries and relevant history while preserving unsaved edits.

## Impact and priority
Low / P3: the manager may believe a paid entry remains unresolved and take unnecessary follow-up actions. No duplicate capture was demonstrated. The backend's HTTP 409 guard refused a paid retry.

## Acceptance criteria
1. Refresh open roster payment/entry status and counters after recovery from another session.
2. Agree and verify a bounded refresh SLA; cover decline, in-flight and success transitions.
3. Preserve unsaved seed-order edits during background refresh.
4. Cover reconnect/focus and reopened history behavior.
5. Keep idempotent recovery and paid-entry retry rejection intact.
6. Verify in separate authenticated sessions without cookie swapping.

No shared policy/database clock change, application fix or refund was performed.
