# BUG-440a4a138d416e7e: DOB fields keep US month/day format after selecting United Kingdom

Status: Reproduced on dev, 21 October 2026. Low / P3 carried from the original report. Not in Jira.
Original discovery: ADD-64, 19 October 2026. Requirement reference supplied with the issue: meeting action item Item 32 (09-03). The meeting text itself was not re-fetched; this report verifies the specified US-to-UK expectation.

## Summary
All four inspected production DOB picker contexts were reproduced with MM/DD/YYYY under United Kingdom. This affects editable age-gate/guardian/child fields and the read-only teenager field. The defect also affects input interpretation: UK day-first 25/12/1990 is rejected, and 04/05/1990 is sent as 1990-04-05 rather than UK-intended 1990-05-04.

## Expected
Selecting United Kingdom applies DD/MM/YYYY consistently, while preserving canonical ISO DOB and US month-first behavior when United States is selected.

## Observed coverage
- Initial athlete/account-holder age gate | LIVE FAIL | MM/DD/YYYY after UK selection; UK-style ambiguous value sent in US order. | features/athlete-registration/components/register/date-of-birth-step.tsx:179
- Parent/guardian age gate after under-13 handoff | LIVE FAIL | Parent or Guardian DOB remains MM/DD/YYYY after UK selection. | features/athlete-registration/components/register/date-of-birth-step.tsx:179
- For My Child athlete DOB | LIVE FAIL | MM/DD/YYYY after UK selection; also unchanged after residence becomes United Kingdom. | features/athlete-registration/components/register/registering-someone-else.tsx:175
- Teenager repeated DOB on Athlete Details | LIVE FAIL | Read-only saved 5 April 2011 remains 04/05/2011 instead of UK 05/04/2011. | features/athlete-registration/components/register/registering-myself.tsx:230
- Adult Myself Athlete Details | NO SEPARATE DOB INPUT (source review) | Uses the age-gate/account DOB. The adult branch does not add another editable date picker. | features/athlete-registration/components/register/registering-myself.tsx:221
- Saved athlete personal-information card | DISPLAY ONLY (source review) | Uses an explicit long en-GB date, e.g. 5 April 2011. Not the slash-format input bug; no fresh live card test in this run. | features/athlete-registration/lib/athlete-display.ts:52
- Guardian consent/contact and attending-guardian forms | NO DOB INPUT FOUND (source inventory) | Names/contact/consent fields do not add another DOB picker in the inspected source. | features/athlete-registration/components/register/guardian-contact.tsx; guardian-consent.tsx; components/events/attending-guardian.tsx
- UI component showcase | EXCLUDED | /ui/input is a development showcase, not a registration flow. It also uses the shared DatePicker. | app/ui/input/page.tsx:124

## Steps to reproduce
1. Open dev /athlete-registration/register with United States selected. Observe MM/DD/YYYY.
2. Open Country and language, search United Kingdom, select it and apply. Confirm the header actually shows United Kingdom.
3. Observe the DOB placeholder: it remains MM/DD/YYYY instead of DD/MM/YYYY.
4. Type 25/12/1990 and leave the field. Observe “Please enter a valid date.”
5. Replace the input with 04/05/1990 and click Continue. Inspect the actual POST /api/age-gate payload: dateOfBirth is 1990-04-05. UK day-first intent would be 1990-05-04.
6. For the guardian variant, enter an under-13 DOB and choose “I’m The Parent or Legal Guardian”; repeat the US-to-UK switch on the guardian DOB field.
7. For child details, use a fresh adult QA account, select For My Child, then switch header country to UK. Also select UK as Country of Residence and recheck the DOB.
8. For the read-only teen field, use a fresh QA account with saved DOB 2011-04-05. Switch header country to UK and observe 04/05/2011; expected day-first display is 05/04/2011.

## User impact
UK users see the wrong date convention, can be blocked when the intended day is greater than 12, or send a different birth date when both numbers are 12 or less. DOB is used for age routing, so the parsing risk warrants review beyond the original cosmetic Low/P3 classification. This run observed the age-gate request; it did not persist an incorrectly interpreted DOB into a completed athlete registration or prove a wrong age-band outcome.

## Technical detail
Local source findings (deployed revision not verified):
1. src/components/ui/date-picker.tsx:70 defaults placeholder to MM/DD/YYYY; line 78 defaults locale to en-US. Its change/blur/display logic calls non-localized mask/parse/format helpers. The locale prop is passed to Calendar, not to those helpers.
2. src/lib/date.ts:196 maskDateInput uses two/two/four digit groups. parseMaskedDate at line 203 reads the first pair as month and the second as day. formatMaskedDate at line 214 always prints month first.
3. DOB call sites above do not pass a country-specific order/format. A header-country change therefore cannot change their date interpretation through this code path.
4. The read-only teen field uses the same DatePicker and formatter. The saved ISO date is correct in the test fixture; its localized display is wrong for the selected UK country.
5. The saved athlete identity card has separate long-date formatting; it is not evidence that every DOB display uses the failing mask.

Implementation direction: derive an explicit country/date-order setting from the intended locale source; thread it through the shared picker mask, parse and format functions; preserve canonical ISO state. A locale prop or placeholder-only fix does not correct parsing. Confirm the intended precedence of country/language picker versus residence before implementing conflicting rules.

## Fix acceptance criteria
- US displays and accepts month/day/year; UK displays and accepts day/month/year in every DOB picker and read-only repetition.
- Apply the same country/date-order mapping to placeholder, mask, parsing, formatting and calendar-selected values. Changing the placeholder alone is insufficient.
- After selecting UK, 25/12/1990 is valid, and 04/05/1990 sends ISO 1990-05-04.
- Changing country with a populated field preserves the underlying ISO birth date and only changes its presentation; toggling UK/US must not swap the stored day/month.
- Read-only teen DOB 2011-04-05 displays 05/04/2011 in UK format and remains non-editable.
- Verify guardian age checks, under-13 handoff, 13/18 boundaries, leap days, invalid calendar dates, typing/paste/calendar input, refresh and mobile.
- Keep API/storage dates as ISO YYYY-MM-DD. Use a shared explicit date-order setting; confirm whether header country or residence is authoritative for the whole application.

## Execution evidence
Started 2026-10-21T12:35:56.609Z; finished 2026-10-21T12:40:14.363Z. Assertion counts: {"PASS":17,"FAIL":9}. Counts include country-selection controls and must not be interpreted as separate bugs. Six browser recordings in this report capture real dev UI interactions. API calls create two controlled QA accounts only, outside the visible browser flow. No membership purchase, payment, shared settings update, or application fix was performed.

Default browser locale was en-US; a separate en-GB browser run reproduced the UK failure. Australia was an additional day-first control. US defaults and switching back to US passed. One navigation timeout interrupted fixture setup; the remaining form checks were resumed successfully. Setup diagnostics remain in the raw evidence.

Recording files:
- Initial athlete/account-holder age gate: initial-age-gate.webm
- Australia and return-to-US control: initial-age-gate-other-countries.webm
- UK country with en-GB browser locale: initial-age-gate-browser-en-GB.webm
- Parent or guardian age gate: parent-guardian-age-gate.webm
- For My Child athlete DOB: child-athlete-details.webm
- Teenager repeated DOB (read-only): teen-athlete-details-readonly.webm

Raw structured observations: results.json. Source inventory covers the inspected frontend checkout; it is not a claim about other applications or uninspected administrative DOB surfaces. No Jira ticket was created.
