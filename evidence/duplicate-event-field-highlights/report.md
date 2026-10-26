# Tour Manager: duplicate event error shows a banner but does not highlight conflicting fields

Status: Draft bug report. No Jira ticket created. Suggested priority: Medium.
Requirement: AI-121 / ADD-78. Area: Tour Manager event creation/editing, duplicate conflict errors.

## Summary
When a Tour Manager changes an event's dates to overlap an existing event on the same tour at the same location, Save changes is correctly rejected. However, the page only displays a duplicate banner; Location, Start date and End date keep their normal appearance and show no inline explanation. The API returns HTTP 409 with an empty fields map, and the local frontend error mapper handles field errors only for HTTP 422.

## Fresh verification
Recorded on dev: 2026-10-20T18:42:21.127Z. Frontend: https://app.dev.worldsurfleague.com.
This is a real Edit event UI reproduction. Two isolated QA Drafts were created via API for setup; no production or imported events were edited.
Existing event: 01a15a9e-b59b-7432-b8f7-fc3453b11250, 2082-11-06–2082-11-06.
Candidate event: 01a15a9e-b7ac-70e0-8514-3a9aa6564dab, originally 2082-11-07–2082-11-07.
Tour: International Qualifying Series (QS), Men. Location: 56th Street. Season: 2082.

## Reproduction
1. Create two valid Draft events in the same QA season, tour and location, on November 6 and November 7 respectively.
2. Open the November 7 event in Edit event.
3. Change both Start date and End date to November 6, matching the existing event.
4. Click Save changes.
5. Observe the duplicate banner. Inspect Location, Start date and End date: no red error state or inline duplicate message appears.

## Expected
Reject the duplicate and keep the explanatory banner. Identify the relevant conflicting inputs in the API fields map and display corresponding field highlights and inline guidance. Managers should immediately see which values need changing.

## Actual
HTTP 409; reason competition.event_duplicate; fields {}.
Banner: "QA duplicate field evidence 1792521712169" is already on International Qualifying Series (QS) · Men at 56th Street on overlapping dates (Fri 6 – Fri 6 Nov 2082). Change the location or the dates.
The screenshot shows the red page-level banner but normal field borders and no inline duplicate messages. Captured form controls have no aria-invalid markers or described-by errors. The rejected edit was not persisted: readback retained 2082-11-07–2082-11-07.

## Impact
The manager has to interpret the banner and locate the relevant inputs without field-level guidance. Duplicate prevention remains effective; no duplicate was saved and no data loss was observed.

## Technical findings
- BFF: wsl-local/wsl-django-bff/interfaces/http/api/tour_manager_events.py, _written duplicate branch around lines 209–218. It builds a 409 competition.event_duplicate response and conflict reference without providing field mappings.
- Frontend: wsl-local/wsl-frontend/src/features/tour-manager/components/event-editor.tsx, refusedFields around lines 63–70. It returns no field errors unless status is 422. Adding fields to the 409 response alone will not enable highlights.
- Fix both sides of the contract: keep duplicate rejection behavior and map supported 409 duplicate field errors to form inputs.
- These are inspected local-source findings; deployed revision was not verified. No application fix was made.

## Acceptance criteria
- Duplicate rejection carries actionable errors for the fields responsible for the collision.
- The form highlights those fields and shows inline guidance while retaining the banner.
- Correcting the collision clears the relevant errors and permits a valid save.
- Existing HTTP 422 validation remains correct; duplicate rejection remains effective.
- Verify both New event and Edit event paths, including a visible UI assertion.

## Evidence
recording-captioned.mp4: direct UI action recording with captions; setup is outside the recorded steps.
before.png / after.png: full-page before/after screenshots.
results.json: actual PUT request, full HTTP 409 body, displayed text, form-control error attributes, and readback dates.
response.json: exact captured duplicate response.
The earlier 19 October ADD-78 run separately confirmed the create path returns 409 with fields {} (3 checks passed; 1 failed). The fresh recording verifies the Edit event path visually.
