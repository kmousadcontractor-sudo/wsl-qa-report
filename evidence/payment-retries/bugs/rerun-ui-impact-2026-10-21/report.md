# Retry rerun: simple results, UI effects and flow graphs

21 October 2026. No application fix or Jira change. Stripe test mode only.

## 1. Completed retry slot selected again
The scheduler can reuse the first retry time. In the exact-time local worker test it sent a second execute command. Moving the result just 1 millisecond later avoided that extra command.

- Original domain test: still fails.
- New isolated worker sequence: exact timestamp fails with two execute commands; +1ms control passes with one execute command. These use actual application scheduling functions with fake collaborators and injected time, not a deployed worker or real provider.
- UI check: Payment rules & engine shows two retries, at 24 hours and 3 days. No clock-advance control was found in the inspected panel/row actions; no policy was edited. A manual retry button is not a reproduction of the exact automatic boundary.
- No duplicate Stripe charge was proved. Practical reachability with real timestamp precision remains unverified.
- Flow graph: retry-slot-flow.svg. Backend recordings: retry-consumed-offset.webm and retry-worker-impact.webm. Actual settings recording: ui-payment-rules.webm.

## 2. Late payment success ignored after cancellation
The local charge-result method ignores success after its charge is cancelled. In the separate real UI run, however, payment success appeared in history after withdrawal. That UI run did not reproduce a missing success record.

- Real-Postgres repository regression: still fails; result returns None and charge stays CANCELLED. This is a direct repository injection, not the full broker/provider/UI path.
- Fresh live fixture: event 01a15e8d-00c4-732a-9f7a-a8293edfba1a; entry 01a15e8d-0b9f-747f-a902-cbcba6135ae6.
- Genuine decline, then valid-card change via athlete API and withdrawal through the actual manager menu, reason selection and Proceed button.
- Final UI/API row: Withdrawn, payment null/dash, no actions. Expanded history contains one successful payment above the withdrawal, newest first.
- The UI therefore demonstrates payment visibility/reconciliation concerns for a withdrawn entrant, not that the tested method lost this live success. The broader event chain and deployed revision were not correlated.
- The card update itself can initiate an immediate retry. No manual retry was sent after withdrawal in this run. No duplicate success, provider timing attribution or automatic refund was established.
- Flow graphs: late-success-backend-flow.svg (local failure) and late-success-ui-flow.svg (actual UI observation).
- Actual action recording: actual-ui-withdrawal.webm. Separate read-only review after the run: ui-history-review.webm.

## Observed response timeline (UTC, not processor timestamps)
- 2026-10-21T13:02:58.247Z | Athlete changes to valid saved Visa through real API | 202
- 2026-10-21T13:02:59.654Z | Manager clicked Proceed in real withdrawal dialog | 200
- 2026-10-21T13:03:00.578Z | Captured final API roster and history | readback

## Recordings and limits
The original UI attempt paused at a styled-radio automation selector; it was resumed on the same declined fixture by clicking the visible reason label. This was a script issue, not an application defect. Raw data retains the diagnostic; the final actual UI recording is the resumed sequence. No shared dev rules, database timestamps, UUIDs, clock or broker messages were changed. No funds outside Stripe test mode. No refund or Jira action.

No time acceleration was performed in dev. Local test clocks are explicitly separate from live UI evidence. The old withdrawn fixture was reviewed as a comparison only; it is not the fresh race fixture and is not proof of the ignored-outcome component.
