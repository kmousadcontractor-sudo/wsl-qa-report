# WSL-9790 detailed QA execution report

QA verification for WSL-9678.

**Overall: further verification required; no QA sign-off.**

[Published report, screenshots, all recordings and API evidence](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/)

16 cases with dedicated verified API recordings: 14 PASS, 1 FAIL, 1 BLOCKED, 0 REVIEW. Dedicated recordings are live API execution evidence; product UI recordings/screenshots are separately labelled.

## Browser regression results

The Firefox browser-network run recorded 14 safe endpoint responses, one HTTP 500 (missing heatId on beta), and one staging timeout. Beta desktop/mobile popup opening was observed without horizontal overflow. Close/reopen and interactive tab switching remain unverified; staging exposed Replay links rather than a certified visible Details control.

## Latest dedicated API cases

| Environment | Test | Result | HTTP/error | Full recording | Screenshot | Request/response |
| --- | --- | --- | --- | --- | --- | --- |
| beta | populated-career | PASS | 200 | [A02](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A02/recording.mp4) | [Image](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A02/result.png) | [Metadata](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A02/request-response.json), [raw body](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A02/response.txt) |
| beta | populated-h2h | PASS | 200 | [A05](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A05/recording.mp4) | [Image](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A05/result.png) | [Metadata](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A05/request-response.json), [raw body](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A05/response.txt) |
| beta | populated-default | PASS | 200 | [A11](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A11/recording.mp4) | [Image](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A11/result.png) | [Metadata](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A11/request-response.json), [raw body](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A11/response.txt) |
| beta | populated-details | PASS | 200 | [A12](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A12/recording.mp4) | [Image](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A12/result.png) | [Metadata](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A12/request-response.json), [raw body](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A12/response.txt) |
| beta | empty-default | PASS | 200 | [A21](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A21/recording.mp4) | [Image](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A21/result.png) | [Metadata](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A21/request-response.json), [raw body](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A21/response.txt) |
| beta | empty-h2h | PASS | 200 | [A23](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A23/recording.mp4) | [Image](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A23/result.png) | [Metadata](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A23/request-response.json), [raw body](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A23/response.txt) |
| beta | empty-career | PASS | 200 | [A20](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A20/recording.mp4) | [Image](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A20/result.png) | [Metadata](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A20/request-response.json), [raw body](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A20/response.txt) |
| beta | empty-details | PASS | 200 | [A24](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A24/recording.mp4) | [Image](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A24/result.png) | [Metadata](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A24/request-response.json), [raw body](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A24/response.txt) |
| beta | empty-unknown-tab | PASS | 200 | [A26](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A26/recording.mp4) | [Image](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A26/result.png) | [Metadata](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A26/request-response.json), [raw body](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A26/response.txt) |
| beta | empty-refresh | PASS | 200 | [A25](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A25/recording.mp4) | [Image](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A25/result.png) | [Metadata](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A25/request-response.json), [raw body](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A25/response.txt) |
| beta | missing-heat | FAIL | 500 | [A27](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A27/recording.mp4) | [Image](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A27/result.png) | [Metadata](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A27/request-response.json), [raw body](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A27/response.txt) |
| staging | empty-default | BLOCKED | TimeoutError: The operation timed out. | [A06](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A06/recording.mp4) | [Image](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A06/result.png) | [Metadata](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A06/request-response.json), [raw body](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A06/response.txt) |
| staging | populated-default | PASS | 200 | [A17](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A17/recording.mp4) | [Image](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A17/result.png) | [Metadata](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A17/request-response.json), [raw body](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A17/response.txt) |
| staging | populated-details | PASS | 200 | [A18](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A18/recording.mp4) | [Image](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A18/result.png) | [Metadata](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A18/request-response.json), [raw body](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A18/response.txt) |
| staging | populated-career | PASS | 200 | [A16](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A16/recording.mp4) | [Image](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A16/result.png) | [Metadata](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A16/request-response.json), [raw body](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A16/response.txt) |
| staging | populated-h2h | PASS | 200 | [A19](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A19/recording.mp4) | [Image](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A19/result.png) | [Metadata](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A19/request-response.json), [raw body](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/tests/A19/response.txt) |

## Requests and technical details

- GET event results route with heatId 114944 (reported empty heat) or 114284 (verified populated control). Exact request URL including rnd is in each metadata file.
- Header Ajax-Request: postEventWatchHeatDetailsPopup; requestName query parameter matches. Tabs: details, career, h2h, qa-invalid-tab. Refresh uses postEventWatchHeatDetailsContentPopup in both header and query. Missing-ID case deliberately omits heatId. No request body. Authorization is omitted.
- Beta: https://www.beta.worldsurfleague.com. Staging: https://staging.worldsurfleague.com; www alias caused auth redirects. Canonical staging login succeeded.
- Beta build 11927ab6cb3a62e6ff3043e6a1b77566d3259a84-12142 appeared in successful responses. Per-test files contain actual staging versions when returned.
- [Fix PR #3936](https://github.com/worldsurfleague/wsl-web/pull/3936) merged into beta on 20 October 2026. Popup fallback excludes unsafe modules; H2H returns with <2 athletes; DA guard rejects set non-array/<2 athleteIds. Empty filter previously skipped both athlete and nested numAthletes restriction, potentially loading all heats and exhausting PHP memory. The latter cause is developer/Jira evidence, not re-measured here.
- Fix fa28f93af5c42baa86049bb41c6822a97e167e61; merge b40a64667f4810cda655dbefe65d162339d0e96b. Inspected master still had original code; production runtime was not tested.
- Separate Career guard, sly-cms error logging and optional Varnish limiting were outside PR scope. Null/omitted athleteIds and malformed arrays remain defensive-code review cases.

## Recordings and history

14 unique historical recordings and 27 valid dedicated-attempt recordings are linked in the report. Every published video/source was decoded to EOF, source/output duration compared, and checksummed; MP4 conversion has no trimming/cropping/speed change. Invalid/zero-byte files are excluded and documented. A historical session recording does not automatically prove every intended action completed. Dedicated API recordings display actual results with a five-second final hold and final-frame/screenshot evidence.

[Every earlier run and full videos](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/#history) · [Video validation](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/#integrity) · [All attempt metadata](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/per-test-manifest.json)

## Findings and limitations

- Staging empty-heat transport failures remain inconclusive; runtime logs/current fixture verification required.
- Beta missing heatId returned 500 in the browser run, zero-byte body; separate malformed-input finding. [Detailed report](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/missing-heat-id-bug.md).
- Dedicated reruns preserve later transport failures; inspect latest results instead of treating every historical PASS as current universal sign-off.
- No backend logs, SQL trace, memory readback, exact stat accuracy, production test or data changes. One-athlete, invalid IDs, Finals/CS/team layouts, tablet/keyboard and UI follow-ups remain as specified in the [full regression plan](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/regression-plan.md).

[Technical investigation](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/technical-investigation.md) · [PR evidence](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/pr3936.json) · [Machine-readable summary](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/summary.json)

No status transition is requested or performed.

## API request exports

[Postman collection](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/postman-collection.json) · [REST-client requests](https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/WSL-9790/api-requests.http). Credentials omitted.
