# WSL-9745

Jira: https://wslproduct.atlassian.net/browse/WSL-9745
Priority: Low. Created 21 October 2026.

## Problem
Selecting United Kingdom leaves date-of-birth fields and several athlete-flow/dashboard dates in US month-first format. This affects input interpretation as well as display: UK-style 25/12/1990 is rejected, while 04/05/1990 produces dateOfBirth: "1990-04-05" in POST /api/age-gate instead of UK-intended "1990-05-04".

## Report and provenance
[Detailed report with highlighted screenshots and expanded field inventory](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/dob-country-format/#expanded-date-scope).
Original report BUG-440a4a138d416e7e; ADD-64; found on dev on 19 October 2026 and reproduced on 21 October 2026. Requirement reference supplied with the original issue: meeting action item Item 32 (09-03). The meeting text was not fetched again; expanded athlete/dashboard coverage is the requested investigation scope, not an additional quoted meeting decision.
Priority: Low, retaining the original Low/P3 classification. The demonstrated parsing impact warrants severity review.

## Affected fields: confirmed on dev
| Field | Actual with United Kingdom selected | Expected |
| --- | --- | --- |
| Initial athlete/account-holder DOB age gate | MM/DD/YYYY | DD/MM/YYYY with matching parsing |
| Parent/guardian DOB after under-13 handoff | MM/DD/YYYY | DD/MM/YYYY with matching parsing |
| For My Child athlete DOB | MM/DD/YYYY, also after UK residence selection | DD/MM/YYYY |
| Teenager repeated, read-only DOB | ISO 2011-04-05 displays 04/05/2011 | 05/04/2011; preserve the ISO date |
| Membership offer expiry, all three plans | Expires 12/31/2026 | Expires 31/12/2026 |
| Dashboard event start/end ranges | Dec 9–14, unchanged between US and UK | Day-first range, e.g. 9–14 Dec |
| Event-entry Register header | Mid-Atlantic Pro: Dec 9–14 | Matching UK day-first event range |

## Reproduction
1. Open dev /athlete-registration/register with United States selected.
2. Open Country and language, select United Kingdom and Apply. Verify the header shows United Kingdom.
3. Observe that DOB still shows MM/DD/YYYY. Enter 25/12/1990 and blur: "Please enter a valid date."
4. Enter 04/05/1990 and Continue. Captured POST /api/age-gate sends dateOfBirth: "1990-04-05". UK intent is 4 May, ISO "1990-05-04".
5. Repeat on the parent/guardian age gate after an under-13 handoff, child athlete details, and the read-only teen DOB using saved ISO 2011-04-05.
6. Reach membership offers using a controlled QA athlete and select UK. All three expiry labels remain 12/31/2026; no purchase is required.
7. Apply UK on registration and open /athlete-registration/events in the same browser context. Event ranges remain month-first. Open Register for Mid-Atlantic Pro: the entry header repeats the month-first range. Do not submit an entry.

The inspected dashboard has no country picker. UK was applied on registration before navigation in the same browser context.

## Highlighted screenshots
Red outlines mark confirmed month-first fields; green outlines identify already-correct controls. Outlines are temporary QA annotations; date values and server responses were not changed. Each screenshot has an unmarked original in the report.
- [Initial DOB](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/dob-country-format/highlighted/dob-age-gate-highlighted.png)
- [Parent/guardian DOB](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/dob-country-format/highlighted/dob-parent-guardian-highlighted.png)
- [Child DOB](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/dob-country-format/highlighted/dob-child-highlighted.png)
- [Read-only teenager DOB](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/dob-country-format/highlighted/dob-teen-highlighted.png)
- [Membership expiry](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/dob-country-format/highlighted/membership-expiry-highlighted.png) — viewport shows two plans; raw observations confirm all three.
- [Dashboard event ranges and closing deadlines](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/dob-country-format/highlighted/dashboard-event-dates-highlighted.png) — all 14 rendered event ranges were outlined; viewport shows the first five.
- [Dashboard profile DOB, already correct](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/dob-country-format/highlighted/dashboard-dob-highlighted.png)
- [Event-entry header dates](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/dob-country-format/highlighted/entry-event-dates-highlighted.png)

## Recordings and raw evidence
- [Initial age gate: UK validation and ambiguous input](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/dob-country-format/initial-age-gate.webm)
- [Parent/guardian age gate](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/dob-country-format/parent-guardian-age-gate.webm)
- [Child details](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/dob-country-format/child-athlete-details.webm)
- [Read-only teen DOB](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/dob-country-format/teen-athlete-details-readonly.webm)
- [Separate en-GB browser reproduction](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/dob-country-format/initial-age-gate-browser-en-GB.webm)
- [Australia and US controls](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/dob-country-format/initial-age-gate-other-countries.webm)
- [Original assertions and captured age-gate payload](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/dob-country-format/results.json)
- [Expanded screenshot observations and field inventory](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/dob-country-format/highlighted/results.json)
- [Complete date-field scope](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/dob-country-format/date-field-scope.md)

Original DOB execution: 26 assertions, 17 passed and 9 failed; these are not nine separate bugs. Browser recordings show genuine UI interaction; the request payload is in raw JSON, not a visible network panel in the recording. Controlled account setup was performed through APIs outside the recordings.

## Technical findings
Local source inspection; deployed revision was not verified:
- src/components/ui/date-picker.tsx:70 defaults to MM/DD/YYYY; line 78 defaults to en-US. Calendar locale does not localize the mask/parser/display helpers.
- src/lib/date.ts:196 maskDateInput; :203 parseMaskedDate reads the first pair as month; :214 formatMaskedDate prints month first.
- DOB call sites: date-of-birth-step.tsx:179, registering-someone-else.tsx:175, registering-myself.tsx:230 in src/features/athlete-registration/components/register/.
- membership-step.tsx:171 uses formatMaskedDate(plan.expiresOn).
- BFF domain/athlete_events.py:149 produces a month-first date_span consumed by the dashboard and entry header. This requires reviewing API-generated date ranges as well as the shared picker.
A placeholder-only change will leave parsing incorrect. Define the authoritative country/date-order setting and its precedence over residence, then apply it consistently while retaining ISO dates internally.

## Impact and limits
Users entering day-first dates can be blocked or submit a different birth date. The captured request proves age-gate interpretation, not persistence into a completed athlete record or an incorrect eligibility result.
Already correct: dashboard profile DOB "20 October 1996" and closing deadline "9 Nov 2026 · 17:00 EST". Preserve these.
Membership confirmation Active Until is source-reviewed only; confirmation/insurance-validity date fields remain regression scope, not confirmed live failures. Stripe card expiry remains MM/YY.
No membership purchase, payment, event submission, shared configuration change or application fix was performed. No backend test failure is claimed beyond the captured UI-generated request and inspected BFF formatter.

## Acceptance criteria
- UK numeric dates consistently display and accept DD/MM/YYYY; US retains MM/DD/YYYY across editable and read-only DOB fields.
- Placeholder, typing, paste, validation, parsing, calendar selection and display share the same country/date-order authority.
- UK 25/12/1990 is accepted; UK 04/05/1990 sends ISO 1990-05-04.
- Switching country reformats a populated field without changing its underlying ISO value.
- All membership offer expiry labels and dashboard/entry event ranges follow UK day-first conventions.
- Preserve venue timezone and deadline instant; retain already-correct long DOB/deadline displays.
- Regress confirmation/validity dates, age 13/18 boundaries, leap days, invalid dates, refresh and mobile. Keep card expiry MM/YY.

