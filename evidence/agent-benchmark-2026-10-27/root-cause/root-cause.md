# Beach Marshal Events navigation: corrected root cause

The assistant resolves the correct page. The Events screen is blocked by unavailable backend data and missing page-level error handling. The previous test incorrectly required the legacy /athlete-registration/events URL.

## Observed flow

Ask Events -> open_page(athlete_events) -> /athlete-registration/athletes (correct canonical route) -> session athletesUnavailable=true + registration/draft 503 -> blank content instead of a useful error.

## Controlled comparison

Original: real backend requests, blank screen. Separate labelled control tab: only GET /registration/draft is replaced with 200 {draft:null,resume:null}; setup content renders. No database or backend configuration changed. The control does not prove that real athletes exist or that Events eligibility works.

## Source

Dev source commit 69734f04898ea46ff3aeca10b1b270de5f0da6ac. Exact deployed SHA unverified.

- src/lib/assistant/navigation.ts
- src/lib/assistant/navigation.test.ts
- src/components/assistant/assistant-root.tsx
- src/hooks/use-assistant.ts
- src/app/(site)/athlete-registration/athletes/page.tsx
- src/features/athlete-registration/hooks/use-athlete-account.ts
- src/features/athlete-registration/hooks/use-registration-progress.ts
- src/lib/query-client.ts
- next.config.ts

AthletesEntryPage gates rendering on !account.progress.isLoading, while its rendered AthleteShell mounts another useAthleteAccount/useRegistrationProgress observer. The draft query has staleTime:0 and the page handles session.error but not progress.error. Repeated 503 requests and blank/loading content are consistent with a retry/remount feedback loop; exact lifecycle sequence was not independently instrumented.

## Classification

BLOCKED for end-to-end Events view; navigation resolution PASS. Previous hardcoded /athlete-registration/events assertion was obsolete.

Prior WSL-9990 investigation found NATS publish permission denial to svc.competition.year_on_sale.get. This run confirms dependency failure but does not capture new AWS logs proving that underlying permission fault is still the cause.

Browser remains open on the original reproduction tab.
