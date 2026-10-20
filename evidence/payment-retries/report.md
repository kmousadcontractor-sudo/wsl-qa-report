# Payment retries: live dev and accelerated clock checks

Date: 20 October 2026. Stripe test-mode QA fixtures only. No database UUIDs, timestamps, service statuses, shared payment rules or system clocks changed.

## Results
Live dev: 12 checks passed. Advanced-clock source-function tests: 12 checks passed. These are separate scopes; local clock checks do not prove a dev CronJob executed.

## Live dev checks
- Current retry rules are readable and offsets increase within the grace period.
- The retained isolated entry is still Declined.
- Two successive manual retries were accepted; neither produced a successful payment.
- Replaying an identical idempotency key produced at most one additional payment outcome.
- Parallel requests with distinct keys accepted only one retry claim.
- The previously withdrawn failed entry now rejects retries.
- The previously paid and withdrawn entry rejects retries.
- No successful collection was recorded on the inactive-card fixture.

The declined fixture's card was invalidated by its original generic decline. Subsequent outcomes are therefore expected to include “not attempted”; acceptance of a command does not mean Stripe attempted the card again.

## Overcoming the retry waits
The deployed job has no public test-clock endpoint and the configured database URLs point to local services, not an accessible dev competition database. The actual scheduler function accepts a now argument, so it was executed with an advanced clock and in-memory stores using current dev rule values: retries at 24 and 72 hours, grace 168 hours, short-notice cutoff 10 days.

Verified without real waiting:
- At hour 23: no dispatch.
- At hour 24: first retry dispatched.
- Repeated tick while requested: no duplicate dispatch.
- After retryable failure: next attempt scheduled for hour 72.
- At hour 71: no second dispatch.
- At hour 72: second retry dispatched with a distinct attempt key.
- At hour 73 after withdrawal: due retry cancelled, no command.
- Non-retryable failure: no automatic retry scheduled.
- Long-overdue run at hour 200: no late retry dispatched.

This bypasses waiting for code-level scheduler verification only. A live dev automatic retry remains unexecuted; it requires a genuine retryable fixture plus controlled dev database/job access. No claim is made that the generic-decline fixture is scheduled automatically.

## Earlier withdrawal result remains relevant
The earlier immediate post-withdrawal request returned HTTP 200, and the valid-card scenario recorded payment success above withdrawal in history. This later run's settled fixtures return an error. That demonstrates different observed behavior at different points in the lifecycle; it does not establish that the earlier race/gap was fixed. Provider/message attribution is still unresolved.

## Evidence
- Live checks and full request responses: artifacts/payment-retries-2026-10-20/results.json.
- Advanced-clock checks: artifacts/payment-retries-2026-10-20/clock-results.json.
- Live script: scripts/demo/test-payment-retries.mjs.
- Actual-source scheduler probe: scripts/test-retry-clock.py.
- Earlier valid-card evidence: https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/valid-card-withdrawal-retry/.

No alternate was promoted, refund initiated or Jira issue created.
