# WSL-9678 — heat popup regression coverage

Run on staging and beta. Target area: public website heat popup, its tab selection, AJAX refresh, heat lookup and historical athlete-pair query. Firefox is the second browser; previous runs used Chromium. A responsive Firefox viewport is not a real mobile-device certification.

## Rules for interpreting results

- PASS requires an appropriate HTTP response and actual content assertions. Endpoint safety alone does not certify accuracy of statistics.
- Verify empty/populated athlete preconditions from returned markup. Two configured slots do not mean two assigned athletes.
- BLOCKED means credentials, connectivity, missing fixtures or unavailable backend evidence prevented verification.
- HTTP 500 is a failure. A connection reset or timeout is inconclusive about the original 500 and requires logs.
- Preserve raw responses, build version, timestamps, screenshot and browser recording. Never save authorization headers or credentials.
- Stop repeated empty-heat requests after a server/transport failure. Do not load-test this endpoint.

## HTTP and data matrix

| ID | Scenario | Expected | Execution requirement |
| --- | --- | --- | --- |
| E01 | Zero assigned athletes, default popup | Safe details/empty response or accepted 404; no 500 | Verify two TBD slots and zero athlete IDs |
| E02 | Zero athletes, explicit H2H | Safe response; no historical matchup query | HTTP plus backend query trace |
| E03 | Zero athletes, explicit Career | Safe empty statistics, no 500 | HTTP plus content review |
| E04 | Zero athletes, explicit details | Safe details response | HTTP plus content review |
| E05 | Zero athletes, unknown tab | No 500, no unbounded query | Negative robustness check |
| E06 | Zero athletes, content refresh endpoint | Safe response | Use content-refresh request name/header |
| E07 | Missing heat ID | Graceful empty/not-found response | Not an assigned-athlete fixture |
| E08 | Unknown positive heat ID | Graceful empty/not-found response | Verify ID is not real if response unexpectedly populated |
| E09 | Nonnumeric heat ID | Validation/not-found or safe empty response | No 500 |
| E10 | One assigned athlete | No H2H query; supported details/Career work | Dedicated fixture required |
| P01 | Upcoming populated heat, default | Correct heat and assigned athlete names | Discovered actual page link |
| P02 | Populated heat, Details | Correct heat scores/status where available | Not necessarily same default tab |
| P03 | Populated heat, Career | Correct athlete columns and event stats | Known expected statistics required |
| P04 | Populated heat, H2H | Correct pair; no unrelated heats | Known comparison results and SQL trace |
| P05 | Completed heat | Final scores, winners and stats unchanged | Verify completed status |
| P06 | Live heat refresh | Updates same heat without duplicate/empty content | Live fixture and observation period |
| P07 | Different event URL with heat ID | Defined event/heat consistency behavior | Product/API contract required |

## UI and layout matrix

| ID | Scenario | Expected |
| --- | --- | --- |
| U01 | Desktop existing Details link | Real popup opens and shows the requested heat |
| U02 | Popup close and reopen | Closes normally; reopening gives correct content |
| U03 | Career/H2H/Details tab switching | Correct tab active; content belongs to same heat; no console/server errors |
| U04 | Desktop responsive layout | No clipped content or unwanted horizontal scrolling |
| U05 | 390px responsive page and popup | Details remains reachable and readable; no overflow |
| U06 | Tablet 744px | Correct readable layout and usable controls |
| U07 | Keyboard | Link, tabs and close reachable; focus returns appropriately |
| U08 | TBD heat card | Existing intended non-clickable behavior preserved; direct endpoint remains safe |
| U09 | Refresh/Back/multiple popups | No stale athlete names or duplicate overlays |

## Special event matrix — fixture dependent

- Championship Tour men's and women's heat cards.
- Challenger Series upcoming fully drawn heat (different tab-availability rules).
- Finals multi-heat rounds where the module substitutes the first round heat.
- Wavepool/team, wavepool-hybrid and big-wave tow-team heats.
- Bracket, bracket-stage, current-heat, Finals-grid and standard heat-grid entry points.
- Joint-event heat identity and event-specific styling.

Do not mark these passed merely because one CT event passed. Record NOT RUN until a suitable fixture is identified.

## Backend checks — developer/runtime access required

1. Empty and one-item athleteIds arrays return no heat IDs without querying all heats.
2. Scalar athleteIds returns no IDs. Clarify null/omitted behavior separately: isset(null) does not activate the new guard.
3. A valid pair still constrains SQL to both athlete IDs and the two-athlete condition.
4. Check duplicate, sparse, nonnumeric and longer-than-two arrays against the intended method contract.
5. Singular athleteId and orAthleteIds callers still behave correctly; they are separate filters.
6. Check PHP memory, response time, SQL count/scope, request logs and errors for empty and populated fixtures.
7. Confirm runtime build contains the fix. Verify proposed exception logging separately because PR #3936 does not implement it.

## Sign-off

Use actual execution evidence for each case. This plan is deliberately broader than the currently available fixtures. Do not move the ticket based on a blanket “all regression passed” claim while special layouts, exact statistics or query tracing remain unverified.
