# Tour Manager duplicate-event error omits conflicting field highlights

Status: Draft bug report; no Jira ticket created.
Suggested priority: Medium. Area: Tour Manager event creation; BFF error contract and frontend form errors.

## Summary
Duplicate event creation is correctly rejected with HTTP 409 and a descriptive message, but the error contains no field-level errors (`fields: {}`). The form cannot use that response to identify the conflicting inputs as required by AI-121 / ADD-78.

## Evidence
Recorded dev execution: 19 October 2026, 22:58:21–22:58:27 Africa/Cairo (19:58 UTC). This report inspects existing evidence; no fresh rerun was performed.
Source: artifacts/action-items-2026-10-19/checklist-results.json, group ADD-78.
Result: 3 passed checks, 1 failed check.

| Check | Expected | Actual | Result |
| --- | --- | --- | --- |
| Saving a duplicate event is refused | 409 | 409 | PASS |
| Duplicate error names the problem | true | true | PASS |
| Duplicate error identifies conflicting fields | true | false; fields: {} | FAIL |
| Missing-field validation identifies inputs | field errors | HTTP 422; name, startDate | PASS |

Recorded reason: `competition.event_duplicate`.
Recorded message: `"QA Checklist 20261019195026249-8ff84e 6" is already on this tour at 56th Street on overlapping dates (Fri 6 – Fri 6 Nov 2054). Change the location or the dates.`

The raw 409 response body was not retained in this artifact. The reason, message and empty field map above come from the recorded assertions, not a reconstructed full response.

## Preconditions and reproduction
1. Sign in to dev as a Tour Manager with event-creation access.
2. Create a valid event in an isolated QA season using valid tour, location, format and date references; confirm HTTP 201.
3. Submit the same event fields again to `POST https://api.dev.worldsurfleague.com/api/tour-manager/events`.
4. Inspect the HTTP 409 error, its message and its `fields` map.
5. For UI verification, submit the duplicate in New event and inspect the conflicting inputs. This visual step was not performed by the recorded ADD-78 handler.

## Expected
Reject the duplicate and explain the conflict. Return field-level errors using the event form's field names so the relevant location/date/tour inputs can be highlighted with actionable inline messages. Confirm the precise field set against the duplicate business rule; changing the event name alone does not resolve the collision.

## Actual
HTTP 409 and the descriptive duplicate message are present, but `fields` is empty. The test labels the outcome “banner only”; that wording is an assertion annotation, not a direct visual observation. Local frontend source is consistent with a banner-only outcome.

## Technical findings
- Automation: scripts/checklist-tests/action-items.mjs, ADD-78 (approximately lines 257–266). It creates a valid event, repeats the same payload, and checks the 409 response for a nonempty field map. It separately verifies ordinary HTTP 422 errors identify name/startDate.
- BFF: wsl-local/wsl-django-bff/interfaces/http/api/tour_manager_events.py, duplicate outcome branch (approximately lines 209–217). The branch builds the descriptive message and returns a 409 error with reason competition.event_duplicate without supplying field mappings.
- Frontend: wsl-local/wsl-frontend/src/features/tour-manager/components/event-editor.tsx, refusedFields (approximately lines 63–70). It immediately returns an empty object unless the error is an ApiError with status 422, then maps error.fields to draft keys. Duplicate HTTP 409 errors are excluded even if the BFF later supplies fields.
- Both sides need to agree on the error contract. Keep duplicate rejection as 409 and explicitly support its field errors, unless the API contract is intentionally changed.
- These are local-source findings; the deployed revision was not verified. No code fix was made.

## Impact
Managers get the reason for rejection but lack field-specific guidance on what to change. They must interpret the banner and find the relevant inputs themselves. Duplicate prevention still works; this evidence does not show duplicate records being saved or data loss.

## Acceptance criteria
- Duplicate HTTP 409 errors include actionable field entries for the actual conflicting inputs.
- The frontend maps duplicate errors to the corresponding inputs, highlights them and shows inline messages while retaining the explanatory banner.
- Fixing the conflicting input clears/recalculates the relevant error; a valid corrected event can be saved.
- Ordinary 422 field validation and duplicate prevention remain correct.
- Verify both New event and Edit event collision paths where supported.
- Add an API contract check and a UI assertion for the visible field errors; merely checking a nonempty field map is insufficient UI coverage.

## Evidence limits
The retained recording/screenshot show browser context after API assertions, not the duplicate form being submitted. They are supporting context only. Frontend inline highlighting must be verified directly on a follow-up UI run. No Jira issue was created for this report.
