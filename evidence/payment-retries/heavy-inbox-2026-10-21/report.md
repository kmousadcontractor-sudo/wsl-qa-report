# Payment retries: supplied inbox and Stripe test cards

21 October 2026. Dev plus isolated local tests. Recipient: heavy-actually@btj5keea.mailosaur.net.

## Result: partial end-to-end coverage
A real Stripe test-mode membership payment succeeded, its webhook activated the QA membership, and two emails arrived at the requested inbox. The strict short-notice cutoff failed locally. Entry-fee recovery and scheduled reminder delivery remain blocked by saved-card setup; they have not passed.

## Live execution
- QA athlete: 01a15ec1-e5d0-74a6-b63f-536f85f9567f.
- Membership: 01a15ec1-efdc-71a6-b9ee-d87caeae4299.
- PaymentIntent pi_3UT02ZHma49jszOG1TgWQMR5 succeeded with livemode=false, using tok_visa. $250.00 test amount; no real funds moved. Application readback confirmed membershipStatus=active and fulfilment=complete. No synthetic webhook was injected.
- Payment receipt arrived at 16:59:12 Cairo (13:59:12.748489 UTC), 21 October.
- Membership activation email arrived at 16:59:12 Cairo (13:59:12.85212 UTC). Both were delivered to the supplied inbox. These are membership messages, not payment reminders.
- Insufficient-funds test token returned HTTP 402, card_declined / insufficient_funds during SetupIntent confirmation. It was not saved, so it did not create a retryable entry-fee fixture.
- Stripe documents that issuer-decline cards cannot normally be attached: https://docs.stripe.com/testing#declined-payments.
- Reconfirming that SetupIntent using tok_chargeCustomerFail succeeded in Stripe test mode, but the application did not expose the saved card. Another confirmation returned setup_intent_unexpected_state because the SetupIntent had already succeeded.
- Billing portal showed Visa 0341. A separate real portal interaction added another 0341 test card, expiry 12/2030. The app still listed only Visa 4242 afterward. Portal presence does not establish whether this app is designed to import portal-added cards; that fallback did not resolve the setup blocker.
- Final setup 01a15ec2-beb4-754e-a50a-11bb254dae05 remained attempt_ready, savedPaymentMethodId=null. Local source expires an open attempt after 60 minutes; the expiry/restart was not awaited or verified.
- No event entry, Confirm and charge, scheduled Stripe retry, or recovered entry-fee payment was reached for this new account. Earlier recovery evidence remains a separate run.

## New finding: retries can cross the short-notice cutoff
Eight acceptance cases explicitly used version-16 rules: retry offsets 24/72h, notices 24/72/120/168h, grace 168h, cutoff 10 days.

An event starts at T0+12 days, so the short-notice cutoff is T0+48h while grace ends at T0+168h. Leave the 24h retry pending, then run the real worker with an injected clock:
- At 48h: one execute command; not flagged. FAIL against strict stop-at-cutoff.
- At 48h + 1ms: one execute command. FAIL.
- At 49h: one execute command. FAIL.
- At 71.999h: one execute command. FAIL.
- At 72h, exactly cutoff+24h: no retry and entry flagged. PASS.
- Normal control: execute at 24h, receive failure at 24.001h, then tick at 48h/72h. No 72h retry is scheduled past cutoff and entry is flagged at 48h. PASS.
- Separate cutoff=24h and cutoff=72h variants dispatch a retry exactly on the cutoff. Two FAIL results.

Focused result: 6 failed, 2 passed. These eight cases are already included in retry-suite.xml, not additional tests.

Technical cause: competition/application/payment_retries.py dispatches when next_attempt_at <= now < deadline + 24h, before flagging. domain/payment_retries.py permits a due time equal to the deadline. This lateness tolerance conflicts with the requested strict short-notice stop. Deployed source revision was not verified. Tests use real application functions with fake collaborators and injected clocks; commands were captured, not published to Stripe. No actual post-cutoff charge is claimed.

## Local suites rerun
- Retry domain/application and boundary suites: 114 tests, 103 passed, 11 failed.
- Notification email templates/content: 65 tests, all passed.
- Payment decline classification/deferred-charge application: 133 tests, all passed.
- Payment execute/card-change/webhook handlers: 25 tests, all passed.
- Total for these four distinct suites: 337 tests, 326 passed, 11 failed. This is not a count of end-to-end scenarios.

Retry failures comprise six new strict-cutoff variants, one previously reported completed retry-slot case, and four previously reported terminal-entry manual-retry variants. Notification tests verify rendering/content, not actual scheduled delivery. Payment suites use isolated collaborators, not 158 new Stripe attempts. Initial template collection needed the notification source path and Jinja2 in the isolated environment; the final suite completed with no collection errors.

## Actual email evidence
The page embeds screenshots and a recording made from the real retrieved Mailosaur messages. URLs were removed from the display. This is a presentation of received messages, not the Mailosaur website interface. Recipient, subject, received timestamps and sanitized message text are retained in received-emails.json.

## What remains unverified
1. Real 24/72/120/168-hour reminder emails, escalation email, recovery link and duplicate suppression.
2. A usable retryable saved-card fixture and actual scheduled Stripe attempts.
3. Real entry-fee decline followed by valid-card recovery, roster/history update and stopping after success.
4. Live crossing into the 10-day window during active grace, including exact cutoff, overdue job and an already-in-flight attempt.
5. Live guardian-recipient variants, withdrawal, alternate replacement, override, webhook redelivery and notification outage for this account.

No accessible dev database or scoped dev clock control was established. Injected local time does not advance dev time. Shared payment rules, UUIDs and clocks were not changed. No database repair, application fix, refund or new Jira ticket was created. Do not mark these remaining cases passed.

## Required next step
A supported way to restart the stuck card setup (or observe its expiry), plus an attachable retryable provider fixture and scoped scheduler clock access, is needed for the remaining accelerated dev checks. Preserve the QA account and fixture IDs for diagnosis. Do not change a generic decline into a fake retryable outcome.

