# QA-RETRY-04: Manager roster stays Declined and Pending after valid-card recovery succeeds until page refresh

Status: Reproduced. Tracked in WSL-9744. P3 suggested.
Environment: Live dev / independent athlete and manager browser sessions. Matrix: RET-105.

## Summary
A successful entry-fee recovery updates the API to Collected and Confirmed, but an already-open manager roster retains Declined/Pending and stale counters throughout the 90-second observation.

## Evidence scope
The deployed source revision and intended refresh SLA were not verified. The local useSeedList hook has no polling interval, which is consistent with the observation but is not a proven deployed root cause.

## Impact
Tour Managers can see an incorrect unresolved decline and take unnecessary follow-up actions until they refresh. This run recorded one successful history outcome and rejected paid retry with HTTP 409; no duplicate capture was shown.

## Steps
1. On dev, enter a controlled QA event with the saved declining Stripe test card and use Confirm and charge.
2. Verify the entry is Declined/Pending. Keep the manager Athletes tab open.
3. Using a separately authenticated athlete session, change that entry to the valid saved Visa.
4. Replay the same card-change idempotency key and confirm safe HTTP 202 responses.
5. Poll the API independently while observing the untouched manager tab for 90 seconds.
6. Verify API payment is Collected and entry is Confirmed while the manager row remains Declined/Pending.
7. Reload the manager page and reopen Athletes; observe Collected and corrected entry status.

## Expected
The open roster reflects successful asynchronous recovery: Collected payment, Confirmed entry, updated counters.

## Actual
API: Collected/Confirmed. Open roster: Declined/Pending after 90 seconds. Reload: Collected.

## Technical investigation
F-04 — Open manager roster remains stale after successful card recovery

- Matrix: RET-105. Suggested priority: P3 for stale operational status; confirm intended live-update behavior with the product owner.
- Environment: live dev, 21 October 2026, separate authenticated athlete and manager browser contexts.
- Event: `01a15d6d-df77-76f9-99fa-5cff13be3f99`; entry: `01a15d6d-eb6b-762c-bf81-59240b572ff4`.
- Reproduction: confirm and charge the declining Stripe test card; leave the Tour Manager Athletes tab open; change the athlete's entry to a valid saved Visa from a separate session; observe the existing manager tab for 90 seconds; reload.
- Expected: the open roster reflects successful asynchronous recovery, with Collected payment, Confirmed entry, and updated counters.
- Actual: card change returned HTTP 202 at 07:47:41 UTC. API readback reached Collected/Confirmed, while the open roster remained Declined/Pending through the observation period. After refresh at 07:49:32 UTC, it displayed Collected. Exactly one successful history outcome was recorded; paid retry was rejected with HTTP 409.
- Evidence: `recovery-before-refresh.png`, `recovery-after-refresh.png`, `recovery-recording.webm`, and `recovery-results.json` in the published execution folder. Original shared-cookie observation was retested independently and is not used as sole proof.
- Code observation: `wsl-frontend/src/features/tour-manager/hooks/use-tour-manager.ts:401`, `useSeedList`, defines a query key and fetch function without a polling interval. This is consistent with the stale view, but the deployed revision and all global invalidation mechanisms were not verified, so it is a likely explanation rather than a proven production root cause.
- Frontend direction: invalidate or refresh relevant seed-list, summary and history queries on asynchronous payment updates, with bounded polling or a suitable event channel. Avoid relying only on mutations initiated in that manager tab. Preserve unsaved seed edits during refresh.


## Fix acceptance criteria
- Verify open roster, counters and entry history refresh after payment from another browser/session.
- Preserve unsaved seed-order edits during refresh.
- Verify declined, pending and collected transitions, reconnect/focus behavior and bounded refresh timing.

## Recording
Actual live dev UI: ../../execution-2026-10-21/recovery-recording.webm; timestamped API/UI evidence in recovery-results.json.

Tracked in WSL-9744. No application fix created.

## Jira tracking

[WSL-9744](https://wslproduct.atlassian.net/browse/WSL-9744) · Priority Low.

[Complete detailed ticket report with logs, backend validation and evidence](jira-report.md).
