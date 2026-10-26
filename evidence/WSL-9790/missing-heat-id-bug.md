# Related regression finding: popup request without heatId returns HTTP 500

Status: observed on beta; not submitted as a new Jira ticket. This is separate from WSL-9678's zero-athlete heat scenario.

## QA summary

When a direct heat-details popup request omits the heat ID, beta returns HTTP 500 instead of a graceful missing-heat response. No athlete or event data was modified.

Environment: https://www.beta.worldsurfleague.com

Browser: Firefox 157.0, Playwright-compatible Firefox build 1555, headless with recording.

## Steps

1. Authenticate to the beta public website.
2. Open the MEO Rip Curl Pro Portugal results page.
3. Send a same-origin browser GET to `/events/2026/ct/445/meo-rip-curl-pro-portugal/results?requestName=postEventWatchHeatDetailsPopup`, deliberately omitting `heatId`.
4. Include header `Ajax-Request: postEventWatchHeatDetailsPopup`.
5. Inspect the response status. The test adds a unique `rnd` parameter.

Expected: missing/invalid input is handled with an appropriate validation/not-found or safe empty response; no HTTP 500.

Actual: HTTP 500. The initial Firefox fetch returned an empty body, so the response build version could not be read from this specific failure. Adjacent successful beta popup responses reported `11927ab6cb3a62e6ff3043e6a1b77566d3259a84-12142`.

## Evidence and impact

- Initial request URL, timestamp, status, duration and zero-byte response metadata: `artifacts/WSL-9678-firefox-stable-regression-2026-10-22/beta/results.json`, check `missing-heat`.
- Browser session recording: the same folder's `recording.webm`. The request is made in a separate same-origin browser page; the recording of the event page does not visually expose that background request.
- A focused browser follow-up separately checks tab switching, delayed close/reopen and the missing-ID request; its evidence is under `beta/ui-followup` when completed.
- Impact is a malformed direct request causing a server error. No ordinary user click without heatId has been demonstrated.
- Backend stack trace and root cause have not been obtained. Do not assume this is the original broad-query/memory-exhaustion failure.

## Remaining original issue

The original empty heat 114944 passed on beta. Staging's corresponding empty-heat request timed out in Firefox and reset its connection in the earlier Chromium attempt, while populated controls returned 200. Staging needs runtime logs and a verified fixture before signing off WSL-9678.
