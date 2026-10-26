# WSL-9760: No immediate email after the first entry-fee decline

Jira: [WSL-9760](https://wslproduct.atlassian.net/browse/WSL-9760) · Medium · To Do · Created 21 October 2026.

## Summary
An athlete receives no immediate email when their first event-entry fee payment declines. The submitted-entry email is the only message around that time. The first actionable failure email is produced by the 24-hour reminder schedule.

This is a requested first-failure notification gap. Current dev version-16 rules explicitly configure notices at 24, 72, 120 and 168 hours, so the observed behavior follows the present configuration. It is not evidence that the reminder worker or SES failed, and no prior approved requirement for an immediate email is asserted. QA/user requested this behavior be raised as a bug on 21 October 2026; Product should confirm the immediate-notice contract and delivery SLA.

## Evidence
- [Focused bug record and timeline](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/missing-initial-decline-email/)
- [Complete real recovery/reminder execution](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/full-recovery-reminders-2026-10-21/)
- [Retrospective all-subject inbox audit before the first advanced-clock run](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/missing-initial-decline-email/initial-observation-inbox.json)
- [Actual received email metadata/text/screenshots](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/full-recovery-reminders-2026-10-21/emails.json)
- [All seven notification delivery rows and SES message IDs](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/full-recovery-reminders-2026-10-21/notification-readback.json)
- [Worker before/after state and actual versus fixture clocks](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/full-recovery-reminders-2026-10-21/runtime-ledger.json)
- [Initial genuine declines, histories and version-16 rules](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/full-recovery-reminders-2026-10-21/fixtures.json)
- [Actual submitted-entry email screenshot](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/missing-initial-decline-email/entry-submitted.png)
- [First decline reminder screenshot](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/missing-initial-decline-email/first-decline-reminder.png)
- [Recorded received-email review](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/full-recovery-reminders-2026-10-21/received-emails-stage-1.webm)
- [Actual dev payment-rules screenshot](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/missing-initial-decline-email/payment-rules.png)
- [Flow diagram](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/missing-initial-decline-email/flow.svg)

Recording scope: actual messages retrieved from Mailosaur and displayed with URLs removed; it is not a recording of the initial Confirm and charge clicks. Those actions were API-driven and are supported by saved histories.

## Environment / fixtures
Dev, 21 October 2026; Stripe test mode; recipient heavy-actually@btj5keea.mailosaur.net.
Athlete: 01a15ec1-e5d0-74a6-b63f-536f85f9567f.
Recovery entry: 01a15ee5-22f2-71c3-82c7-62abb84e0d79; event 01a15ee5-17d8-7267-b401-217b22864acc.
Expiry entry: 01a15ee5-6fe7-753a-acef-1b72f9ea0c0f; event 01a15ee5-6548-76b6-bfea-4df397213040.
Both genuine failures were generic_decline / needs_new_method on saved Stripe decline-after-attaching cards. Both events were outside the 10-day short-notice window.

## Steps to reproduce
1. Create an eligible athlete entry with a saved Stripe test card that attaches successfully but declines when charged (0341).
2. Close entries, seed the athlete, and Confirm and charge.
3. Verify the genuine payment decline and Pending/Declined state.
4. Inspect all email subjects for the exact account-holder recipient immediately after the failure, before any scheduled reminder threshold.
5. Observe only the submitted-entry message; no actionable payment-failure email.
6. Advance only the isolated QA fixture clock to first_failed_at + 24 hours and run the deployed scheduler logic using real repositories/outbox.
7. Observe the first “Your entry fee … could not be taken” email in the inbox.
8. Replay that threshold: no duplicate reminder. Later thresholds and actual delivery also work.

## Observed timeline
21 October 2026; Cairo is UTC+3.

| Event | UTC | Cairo |
| --- | --- | --- |
| Recovery entry submitted email | 14:37:19.828 | 17:37:19.828 |
| Recovery entry first_failed_at | 14:37:21.227 | 17:37:21.227 |
| Expiry entry submitted email | 14:37:39.630 | 17:37:39.630 |
| Expiry entry first_failed_at | 14:37:40.744 | 17:37:40.744 |
| First fixture-clock 24h worker pass | 14:40:55.503 | 17:40:55.503 |
| Recovery first decline email received | 14:40:59.514 | 17:40:59.514 |
| Expiry first decline email received | 14:41:04.572 | 17:41:04.572 |

The historical Mailosaur query, across all subjects for the exact recipient from 14:36:46.760 until before 14:40:55.503 UTC, returned exactly the two submitted-entry emails and zero decline emails. This is bounded absence during a roughly three-minute post-failure observation, corroborated by source and delivery records. We did not wait 24 real hours: the next notice was triggered with a scoped advanced fixture clock.

## Expected / impact
Persisting the first actual entry-fee payment failure should promptly enqueue an actionable transactional email, independently of the first scheduled reminder. It should identify the athlete, event, amount, failure/recovery guidance and deadline. A needs_new_method failure should request a new card; retryable failures should explain the next eligible retry where applicable.

Without that initial notice, athletes may believe their entry is proceeding normally and may not learn that action is required until the 24-hour reminder. This reduces recovery time. No customer financial loss is established.

## Current policy and technical findings
Local source inspection; deployed commit/image revision was not verified. Actual scoped dev scheduling and delivery results are recorded separately above.
- Rules version 16: notifications [24,72,120,168]h; retries [24,72]h; grace 168h; short-notice cutoff 10 days.
- competition/application/payment_retries.py:93, schedule_after_failure, pins first failure/rules/deadline and records retry eligibility; this path does not publish an initial athlete notice.
- competition/domain/payment_retries.py:107, latest_notice_due, only selects configured elapsed offsets; there is no T0 notice in this policy.
- Worker publishes scheduled notice at payment_retries.py:259 and grace-ended escalation at :269.
- All seven later payment notifications were sent with SES IDs and received. This is not an SES authorization or deliverability defect.
- Suggested direction: a distinct idempotent first-failure notice, separate from reminder counters; retain first-failure anchoring and existing reminder offsets. Extend the event/template contract if necessary rather than merely changing a placeholder or resetting the failure clock.

Short-notice nuance: when failure is inside the last 10 days, the effective deadline is already reached; retry-worker processing can flag/escalate without granting a fresh seven-day grace. That is not proof of a synchronous initial-decline email at the failure callback. This exception was source-reviewed, not reproduced live in these two fixtures.

## Acceptance criteria
1. First persisted payment failure promptly enqueues one actionable account-holder email within an agreed delivery SLA, without waiting for the 24-hour reminder job.
2. Redelivered failure events or repeated scheduler passes do not duplicate the initial email.
3. Preserve pinned T0, deadline, retry rules and 24/72/120/168h reminder accounting.
4. Match guidance to needs_new_method versus retryable/action-required outcomes; do not invent an automatic retry for a non-retryable card.
5. No further reminders after successful recovery or another valid stop condition.
6. Define/coalesce initial failure and short-notice escalation to avoid contradictory or duplicate messages.
7. Verify actual test-inbox receipt, account-holder/guardian routing, event/amount/deadline/link correctness and notification audit IDs.

Priority: Medium, suggested for triage. No application fix, new policy change, refund or real-money movement was performed for this bug record.
