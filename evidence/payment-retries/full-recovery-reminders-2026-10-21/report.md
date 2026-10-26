# Real payment recovery and scheduled reminder delivery
21 October 2026 · Dev · Recipient: heavy-actually@btj5keea.mailosaur.net

## Outcome
Actual payment recovery and all requested reminder thresholds were exercised using isolated QA fixture clocks. Seven payment notifications were sent through the deployed pipeline and received in the exact supplied Mailosaur inbox. Stripe independently confirms the recovered $150.00 payment succeeded in test mode. The manager row is Confirmed / Collected.

One user-interface gap remains: the received Update your card link opens the athlete dashboard successfully, but no card-update control was found on the inspected destination. Card replacement used the authenticated athlete card-change API. Therefore this is a passed backend/provider recovery and notification integration, with a failed browser-only card-update step; it is not an unqualified full browser-journey pass.

## Coverage results
14 PASS, 1 FAIL across 15 evidence checks. These counts describe this focused run, not the earlier 110-case matrix.

| ID | Check | Result |
| --- | --- | --- |
| FR-01 | Two genuinely declined entry fixtures | PASS |
| FR-02 | Every payment email reached the exact supplied inbox | PASS |
| FR-03 | Recovery fixture received two scheduled reminders | PASS |
| FR-04 | Expiry fixture received four scheduled reminders | PASS |
| FR-05 | Expiry escalation delivered | PASS |
| FR-06 | All seven notifications persisted as sent with SES IDs | PASS |
| FR-07 | Stripe independently confirms test-mode full recovery | PASS |
| FR-08 | Manager recovery row is Confirmed/Collected | PASS |
| FR-09 | No notices after recovery at 120h/168h | PASS |
| FR-10 | Expiry row reaches four notices and a flag | PASS |
| FR-11 | Repeated 24h and 168h ticks produce no new notices | PASS |
| FR-12 | Expiry fixture remains unpaid in Stripe | PASS |
| FR-13 | Shared payment-rule version remains 16 | PASS |
| FR-14 | Received recovery link opens athlete dashboard | PASS |
| FR-15 | Card-update control available on the inspected recovery destination | FAIL |

## Real email delivery ledger
All times below are Cairo, UTC+3. Raw evidence retains UTC received and worker timestamps. Two separate entry-submitted emails also arrived; they are excluded from the seven payment-notification count.

| Fixture | Triggered threshold | Actual received time, Cairo | Subject |
| --- | --- | --- | --- |
| recovery | 24h reminder | 21 Oct 2026, 17:40:59 | Your entry fee for QA Full recovery reminders 1792593431785 could not be taken |
| recovery | 72h reminder | 21 Oct 2026, 17:42:14 | Your entry fee for QA Full recovery reminders 1792593431785 could not be taken |
| expiry | 24h reminder | 21 Oct 2026, 17:41:04 | Your entry fee for QA Full expiry reminders 1792593451679 could not be taken |
| expiry | 72h reminder | 21 Oct 2026, 17:42:19 | Your entry fee for QA Full expiry reminders 1792593451679 could not be taken |
| expiry | 120h reminder | 21 Oct 2026, 17:44:29 | Your entry fee for QA Full expiry reminders 1792593451679 could not be taken |
| expiry | 168h reminder | 21 Oct 2026, 17:44:34 | Your entry fee for QA Full expiry reminders 1792593451679 could not be taken |
| expiry | 168h escalation | 21 Oct 2026, 17:44:39 | Action needed: your place at QA Full expiry reminders 1792593451679 is at risk |

The reminder messages named Retry HeavyQA, the specific event, $150.00, a pay-by date, and an Update your card link to app.dev.worldsurfleague.com/events. Because these were generic declines, the emails correctly said that this card cannot be tried again and needs updating. The expiration email said the place is at risk and needs a Tour Manager decision. We verified delivery, recipient, event/amount/deadline wording and link routing; guardian recipients, localization and spam placement were not part of this focused run.

## Recovery fixture: complete backend/provider sequence
- Event: QA Full recovery reminders 1792593431785.
- Event ID: 01a15ee5-17d8-7267-b401-217b22864acc.
- Entry ID: 01a15ee5-22f2-71c3-82c7-62abb84e0d79.
- First failure: 21 October 2026 17:37:21 Cairo. Real Confirm and charge with saved Stripe decline-after-attaching card 0341 produced generic_decline and Pending / Declined.
- Real scheduler logic at fixture hours 24 and 72 published two notice events. Both reached the exact inbox.
- Replaying hour 24 produced zero new notices; no extra copy appeared in the delivery audit.
- Received email link returned HTTP 200 and redirected to /athlete-registration/events. It did not expose an observed card-update control for the declined selected entry.
- Athlete card replacement: POST /api/entries/01a15ee5-22f2-71c3-82c7-62abb84e0d79/card, HTTP 202, selecting the account's active saved Visa 4242.
- This card change initiated recovery; no separate manager retry was issued.
- Stripe PaymentIntent: pi_3UT0kDHma49jszOG0ArqOn20. Status succeeded, livemode=false, amount_received=15000 USD cents.
- Stripe charge: ch_3UT0kDHma49jszOG0grpW5GC. Payment service deferred charge status paid; attempt_count=2 (initial decline plus recovery).
- Competition charge status succeeded. Application history records Card payment succeeded. Manager roster after refresh shows Confirmed / Collected.
- Fixture-clock checks at 120h and 168h emitted zero reminders, zero executes and zero new flags for this paid entry. notices_sent remained 2.
- The normal open-roster refresh bug was not retested here; final screenshots use a refreshed manager page.

## Expiry fixture: every reminder and escalation
- Event: QA Full expiry reminders 1792593451679.
- Event ID: 01a15ee5-6548-76b6-bfea-4df397213040.
- Entry ID: 01a15ee5-6fe7-753a-acef-1b72f9ea0c0f.
- A separate saved 0341 test card genuinely declined. Keeping it unpaid allowed all four thresholds to be checked independently of successful recovery.
- Hours 24, 72, 120 and 168 each advanced notices_sent by one and staged exactly one reminder.
- At 168h the scheduler additionally flagged the charge and staged the grace-ended escalation. All five emails arrived.
- Repeating 168h staged no new notices or escalation.
- Final manager row: Needs a decision / Pending. Stripe still shows requires_payment_method, amount_received=0, test mode. No payment was collected for this fixture.
- It remains an explicitly named QA expiry fixture; its flag prevents routine retry-job chasing.

## How time was accelerated
The normal dev CronJob runs python -m competition.payment_retry every ten minutes. We did not run its unrestricted all-organisation pass or change the shared schedule.

A temporary test script inside the existing competition-api pod called the deployed run_tick function with now=first_failed_at+24/72/120/168 hours. A scoped repository adapter returned only the two exact QA entry IDs. Real SQL repositories, pinned version-16 rules, outbox publisher, relays, bus consumers, notification rendering and SES were used. No notification events or Stripe outcomes were fabricated.

Guard checks verified dev environment, organisation, athlete, exact entry set, QA event-name prefix, one charge per entry and generic failure class. Actual row-level security remained bound to the fixture organisation. Every worker result asserted zero failed charges and zero automatic execute commands. Generic declines are not automatically retryable; the successful Stripe recovery came from real card replacement.

Before/after charge snapshots retain actual execution time separately from fixture-clock time. The fixture first_failed_at, deadline and UUIDs were not rewritten. Notice counters and the expiry flag were changed by the actual worker logic. The expiry flag consequently carries the advanced fixture time; this is expected test-clock state, not seven elapsed real days.

The original account's stuck BFF card-setup row 01a15ec2-beb4-754e-a50a-11bb254dae05 was explicitly expired after verifying its athlete contact, account holder, organisation and empty saved-card result. That QA-only fixture repair allowed fresh successful SetupIntents. It is not an application fix and does not prove normal recovery from the earlier stuck-setup bug.

AWS access used the user's signed-in dev session and existing documented cluster role. No IAM policy, deployment, global rule, UUID or shared service clock was changed. Rule version and values remained unchanged at 16, retries 24/72h, notices 24/72/120/168h, grace 168h and cutoff 10 days.

## Remaining UI bug record
Title: Payment reminder opens athlete events without an observed way to update the declined entry's card.
Precondition: confirmed-payment-pending entry, genuine generic decline, actual reminder received.
Steps: open Update your card from the received email while signed in; inspect the matching selected event and available controls.
Expected: a visible route to replace the card for the affected entry and complete recovery.
Observed: /events correctly redirects to the athlete dashboard, but the inspected page offers event Register controls and shows the declined fixture as Selected / Coverage Confirmed / Entries are closed. No Update card, Change card or payment-method button was found there.
Technical contrast: the actual athlete card-change API returns 202 and immediately recovers the payment. Backend recovery works while the inspected email-to-card-update UI path remains incomplete.
Evidence: received-link-destination.png, athlete-expiry-card.png, recovery.json and final-state.json. This observation is limited to the inspected dashboard; it does not claim every possible application route was exhaustively searched. No Jira ticket or application fix was created.

## Evidence and practical limits
notification-readback.json contains seven sent delivery rows, unique email/request IDs and SES message IDs. emails.json contains actual received subjects, recipients, text, timestamps and link origins/paths. These are stronger than treating event publication as proof of delivery.

provider-readback.json contains the scoped payment-service rows and independent live Stripe test-mode API readback. runtime-ledger.json contains twelve per-entry worker results across six passes: 24h, replay 24h, 72h, 120h, 168h and replay 168h. checks.json ties assertions to these results.

Recordings show actual received messages and live manager/athlete pages. Email screenshots are a presentation of messages retrieved from Mailosaur, with URLs removed from the display; they are not a simulation of email delivery. Fixture setup and card change were API-driven and are labelled accordingly. Secrets, authentication cookies and client secrets are excluded.

This run proves accelerated scheduler logic plus the real downstream pipeline, not seven days of natural CronJob timing. Automatic insufficient-funds Stripe retries, provider-in-flight cancellation races, guardian routing, notifications for insurance/recurring memberships and the earlier short-notice cutoff defect are separate coverage. No refunds or real funds movement occurred.
