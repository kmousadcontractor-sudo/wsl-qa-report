# Expanded DOB and date formatting scope: athlete flow and dashboard

21 October 2026. Existing report BUG-440a4a138d416e7e / ADD-64. Low/P3 remains the original classification; now tracked in [WSL-9745](https://wslproduct.atlassian.net/browse/WSL-9745).

All full calendar-date fields should follow the selected country throughout the athlete journey. Under United Kingdom, use day/month/year for numeric dates and a day-first equivalent for written ranges. This expansion adds the requested athlete-flow/dashboard coverage to the original DOB issue; it does not quote an additional meeting decision.

## What needs changing
- Initial DOB, parent/guardian DOB, child DOB and read-only teen DOB: apply country-aware formatting and parsing.
- All three membership offer expiry labels: 12/31/2026 must become 31/12/2026 for UK.
- Event start/end ranges on every dashboard card and the event-entry header: Dec 9–14 must use a UK day-first range, e.g. 9–14 Dec.

## Fields already displaying a UK day-first format
- Dashboard profile DOB: 20 October 1996.
- Dashboard closing deadline: 9 Nov 2026 · 17:00 EST.
These remain in the consistency/regression scope. They must not be described as the same observed month-first failure.

## Complete field/action inventory
- Initial DOB age gate | CHANGE - live confirmed | MM/DD/YYYY under UK | DD/MM/YYYY; update mask, parser and display | Source: src/features/athlete-registration/components/register/date-of-birth-step.tsx:179
- Parent/guardian DOB age gate | CHANGE - live confirmed | MM/DD/YYYY under UK | DD/MM/YYYY; same country-aware picker | Source: src/features/athlete-registration/components/register/date-of-birth-step.tsx:179
- For My Child DOB | CHANGE - live confirmed | MM/DD/YYYY under UK | DD/MM/YYYY on child athlete details | Source: src/features/athlete-registration/components/register/registering-someone-else.tsx:175
- Teenager read-only DOB | CHANGE - live confirmed | 04/05/2011 for saved 5 April 2011 | 05/04/2011 under UK; preserve ISO 2011-04-05 | Source: src/features/athlete-registration/components/register/registering-myself.tsx:230
- Membership offer: every plan expiry date | CHANGE - live confirmed | All three labels: Expires 12/31/2026 | Expires 31/12/2026 under UK | Source: src/features/athlete-registration/components/register/membership-step.tsx:171; src/lib/date.ts:214
- Athlete dashboard: event start/end ranges | CHANGE - live confirmed | Dec 9–14; unchanged after US-to-UK selection | UK day-first range, e.g. 9–14 Dec; apply to every event card | Source: wsl-django-bff/domain/athlete_events.py:149, date_span
- Event-entry screen: event start/end range | CHANGE - live confirmed | Dec 9–14 in Register: Mid-Atlantic Pro | Use the same country-aware range as the dashboard | Source: src/app/athlete-registration/events/[eventId]/register/page.tsx, PageHeader meta; BFF event metadata
- Athlete dashboard: personal-information DOB | ALREADY DAY-FIRST - live checked | 20 October 1996 | Keep valid UK long-date display; include in country-format regression coverage | Source: src/features/athlete-registration/lib/athlete-display.ts:52
- Athlete dashboard: entries-close deadline | ALREADY DAY-FIRST - live checked | 9 Nov 2026 · 17:00 EST | Keep UK day-first formatting and venue timezone; ensure locale consistency | Source: wsl-django-bff/domain/athlete_events.py; domain/formatting.py
- Membership payment confirmation: Active Until | SOURCE REVIEW - regression required | Uses formatLongDate, default en-GB | Include in shared country-format coverage; no fresh paid checkout executed here | Source: src/features/athlete-registration/components/register/payment-confirmed.tsx:74
- Event-entry confirmation / insurance validity dates | SCOPE CHECK - remaining | Date strings depend on entry/coverage data | Apply the same calendar-date policy wherever these dates are rendered; check when a suitable fixture is available | Source: src/app/athlete-registration/events/[eventId]/entry/[reference]/page.tsx; events/[eventId]/insurance/page.tsx
- Card expiry on payment forms | KEEP MONTH/YEAR | Provider card expiry uses MM/YY | Keep MM/YY: this is a card-expiry month/year, not a full calendar date | Source: Stripe fields in payment-step.tsx, register-form.tsx and insurance-checkout.tsx

## Highlighted screenshots
Red outlines identify confirmed month-first displays that need localization. Green outlines identify fields already day-first. Outlines were added temporarily to the actual page before capture; no DOB, date, country or server response was altered. Each screenshot has an unhighlighted original.
- DOB 1: initial age gate: highlighted/dob-age-gate-highlighted.png; original: highlighted/dob-age-gate-original.png
  UK selected; placeholder stays MM/DD/YYYY.
- DOB 2: parent/guardian age gate: highlighted/dob-parent-guardian-highlighted.png; original: highlighted/dob-parent-guardian-original.png
  Parent/Guardian DOB remains MM/DD/YYYY under UK.
- DOB 3: For My Child athlete details: highlighted/dob-child-highlighted.png; original: highlighted/dob-child-original.png
  Child DOB remains MM/DD/YYYY under UK.
- DOB 4: read-only teenager DOB: highlighted/dob-teen-highlighted.png; original: highlighted/dob-teen-original.png
  Saved 5 April 2011 displays 04/05/2011; UK should display 05/04/2011.
- Registration membership expiry dates: highlighted/membership-expiry-highlighted.png; original: highlighted/membership-expiry-original.png
  UK selected; membership offer still uses month/day/year expiry labels. Red outlines added in browser.
- Dashboard: event dates and registration deadline: highlighted/dashboard-event-dates-highlighted.png; original: highlighted/dashboard-event-dates-original.png
  All rendered event date ranges outlined red; all rendered closing-date labels outlined green. Screenshot shows first viewport. UK selected before navigation.
- Dashboard: saved personal-information DOB: highlighted/dashboard-dob-highlighted.png; original: highlighted/dashboard-dob-original.png
  Already uses a long day-first date. Highlighted green: include in consistency coverage, not the slash-format failure.
- Event-entry flow: event date and deadline text: highlighted/entry-event-dates-highlighted.png; original: highlighted/entry-event-dates-original.png
  Review event date metadata for country consistency; no entry submitted.

## How the dashboard was checked
The country picker is on registration. United Kingdom was applied there, then the dashboard was opened in the same browser context. The first event card text was identical between US and UK: Dec 9–14, with deadline 9 Nov 2026. Every rendered event range was outlined red and every rendered closing-date label green; the screenshot shows the first viewport. The profile tab and event-entry header were opened read-only. No event entry was submitted.

## Technical scope
Shared DatePicker and mask/parse/format helpers cover all DOB variants. MembershipStep independently calls the fixed month-first formatMaskedDate helper. Dashboard ranges are formatted by BFF domain/athlete_events.py:date_span, while the entry page consumes event meta from the API. Fix country/locale propagation and all date producers; changing the DOB placeholder alone will leave these other surfaces wrong. Source paths are from the inspected checkout; deployed revision was not verified.

## Acceptance criteria
1. Use one documented selected-country/date-format policy throughout registration, membership, dashboard and event entry.
2. UK numeric dates display/parse DD/MM/YYYY; US numeric dates display/parse MM/DD/YYYY.
3. Reformat existing values without changing ISO dates or swapping their meaning.
4. Localize membership expiry labels and event ranges as well as DOB inputs/read-only fields.
5. Keep venue timezones and actual deadline instants intact when changing date presentation.
6. Include profile DOB, closing deadlines, Active Until and entry/insurance confirmation dates in regression coverage; source-only/remaining checks above are not live passes.
7. Keep card expiry MM/YY, because it represents a month and year.

## Fixture and limits
Eight live screenshot groups were captured. Controlled QA athlete setup was used for the membership offer; an existing draft blocked the first attempt, so a fresh controlled account/athlete reached the offer. No membership purchase, payment, event-entry submission, application change or Jira action. The original six DOB recordings remain on the report. New capture recordings are retained locally; this expansion publishes highlighted screenshots and originals.


Jira bug created 21 October 2026: [WSL-9745](https://wslproduct.atlassian.net/browse/WSL-9745). [Full ticket description](jira-report.md).
