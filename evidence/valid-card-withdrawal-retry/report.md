# Bug: backend accepts retry after withdrawal following a valid-card change

Draft bug report; no Jira ticket created. Suggested priority: High, subject to triage.

## Expected
Reject retries for withdrawn entries. Reconcile any attempt already started and clearly surface successful payments requiring Finance review.

## Actual
The direct manual retry endpoint returned HTTP 200 after withdrawal. History subsequently lists payment success above the withdrawal. The final roster shows Withdrawn with payment null. Card-change retry versus manual-retry attribution remains unresolved.

# Valid-card change before withdrawal and retry: live dev result

20 October 2026. Stripe test mode only. No live funds, database mutations or shared rule changes.

Event: https://app.dev.worldsurfleague.com/tour-manager/events/01a15ac0-27f5-7371-aa14-100478c529fa
Event ID: 01a15ac0-27f5-7371-aa14-100478c529fa
Entry ID: 01a15ac0-347a-73ba-8faf-89658f5fdbc9
Athlete ID: 01a15abf-090b-70da-89c7-a8b3c5895247
Test athlete: Checklist ExtValidCardRemovalf81b

## Sequence observed
- 2026-10-20T19:18:30.478Z — Initial Confirm and charge — HTTP 200
- 2026-10-20T19:18:33.897Z — Change entry to valid saved Visa — HTTP 202
- 2026-10-20T19:18:35.260Z — Remove athlete after valid-card change — HTTP 200
- 2026-10-20T19:18:35.762Z — Manual retry after removal with valid card selected — HTTP 200

Initial Confirm & charge genuinely declined with generic_decline. The athlete then selected a valid saved Visa using the entry-card endpoint, HTTP 202. The roster snapshot at 19:18:34.645Z still showed Declined/Pending and chargesInFlight=false. Withdrawal completed at 19:18:35.260Z. A direct manual retry request after withdrawal completed with HTTP 200 at 19:18:35.762Z.

Final history, newest first:
- Card payment succeeded — 20 Oct 19:18 UTC
- Entry withdrawn · was #1 · Athlete request — 20 Oct 19:18 UTC
- Card payment declined (generic_decline) — 20 Oct 19:18 UTC
- Card payment charge started — 20 Oct 19:18 UTC
- Seed · to #1 — 20 Oct 19:18 UTC

## Confirmed findings
- Backend accepted a manual retry for the withdrawn entry even with a valid card selected.
- The application recorded Card payment succeeded after Entry withdrawn in its reverse-chronological history.
- The athlete remained Withdrawn. The final roster suppressed the payment field (null), despite the success in history.
- The pre-removal snapshot did not show the ongoing payment as in flight.

## Attribution limits
Card replacement itself starts an immediate retry for NEEDS_NEW_METHOD/RETRYABLE charges in the inspected payment code. The test also sent a manual retry after removal. Without provider attempt IDs/timestamps or bus trace, this run cannot distinguish which dispatch produced the successful payment, or whether the provider initiated/completed it before the withdrawal while the success event arrived later. There is no evidence of a second successful charge. This is proof of post-withdrawal retry acceptance and late recorded success, not proof of the exact processor ordering.

No alternate was promoted. No automatic scheduled due-time test was performed. No refund was initiated by this investigation.

## Evidence
Full action responses, timestamped snapshots, final roster and history: artifacts/valid-card-removal-2026-10-20/checklist-results.json.
Screenshot and retained browser recording are in the adjacent screenshots/videos folders. They provide browser context; the actions in this run used the real dev APIs.

## Required next trace
Correlate this entry's payment deferred_charge, execute request IDs, release outcome and Stripe PaymentIntent timestamps. Confirm whether the success came from card update or manual retry, and reconcile/refund any successful payment after withdrawal according to policy. Preserve the fixture IDs; do not change UUIDs.


## Acceptance criteria
- Block retries for terminal entries at both API/application and atomic claim boundaries.
- Cancel remaining failed/scheduled retry eligibility on withdrawal.
- Handle release refusals and reconcile in-flight attempts, including late success.
- Make payment outcomes visible for withdrawn athletes when Finance action is required.
- Verify queued/in-flight withdrawal races and stale manual requests without producing duplicate charges.
