# Generic decline versus insufficient funds: actual card behavior

Executed on dev on 21 October 2026, approximately 17:19–17:21 Cairo (14:19–14:21 UTC). Stripe test mode only; no real funds moved.

## Result
Both card failures were reproduced through the actual athlete membership payment UI, with matching Stripe responses and application readback. A valid-card follow-up succeeded through a fresh checkout. The saved-card event-entry generic-decline path was also tested through Confirm and charge, a manager retry, and valid-card recovery.

The original account heavy-actually@btj5keea.mailosaur.net was preserved because its earlier setup remained stuck. A fresh controlled address in the same Mailosaur server was used: heavy-actually+card-compare-1792592171840@btj5keea.mailosaur.net. This is a different recipient address; this run does not claim new delivery to the exact original address.

## Side-by-side results

| Check | Generic decline | Insufficient funds |
| --- | --- | --- |
| Stripe UI test card | 4000 0000 0000 0002 | 4000 0000 0000 9995 |
| Expiry / CVC | 12/30 / 123 | 12/30 / 123 |
| Stripe result | HTTP 402, card_declined, generic_decline | HTTP 402, card_declined, insufficient_funds |
| Visible UI message | Your card has been declined. | Your card has insufficient funds. Try a different card. |
| Application failureClass | needs_new_method | retryable |
| Application message | This card cannot be used. Please use another card. | Your card was declined. Please try again or use another card. |
| Membership after failure | Not activated; fulfilment=declined | Not activated; fulfilment=declined |
| Automatic entry-fee retry behavior, isolated real scheduler | Zero execute commands | Two execute commands at 24h and 72h |
| Notification behavior, isolated real scheduler | Four reminder events, then flag at 168h | Four reminder events, then flag at 168h |
| Actual scheduled Stripe retries in this run | Not attempted | Not attempted |

Both declined membership responses retained status=attempt_ready while fulfilment=declined. The runner originally waited for status=failed and timed out; it was corrected to observe fulfilment. Raw results retain the preliminary generic-decline request and tooling diagnostics. The final three UI checks passed. Do not add the preliminary run as another successful payment.

## Actual UI sequence and backend evidence
1. Generic-decline card: a new checkout returned HTTP 201. Stripe PaymentIntent pi_3UT0MjHma49jszOG1fMOrwWE returned requires_payment_method with generic_decline. Application checkout 01a15ed5-04df-761b-81f8-fb20d0264abc reported fulfilment=declined, failureClass=needs_new_method.
2. Replace the number with insufficient-funds card and click Pay again. The app created a different checkout, 01a15ed5-33c0-7541-b0df-2b467cc11c75. Stripe pi_3UT0MvHma49jszOG1UXomQIJ returned insufficient_funds; application readback reported retryable.
3. Replace it with Visa 4242 4242 4242 4242 and click Pay. Another new checkout, 01a15ed5-61ae-719b-b9da-f43bd87c6e46, used pi_3UT0N7Hma49jszOG0qGTVSIS. Stripe returned succeeded, livemode=false; the real webhook completed fulfilment and activated membership.
4. All three final attempts used different checkout and PaymentIntent IDs. The earlier declined memberships did not become active. API setup created the account/athlete and signed fixture documents before recording the payment UI.

## Actual saved-card event-entry behavior
Stripe's ordinary issuer-decline cards cannot be saved through a normal SetupIntent. For the generic-decline deferred-charge test, a fresh SetupIntent used the supported decline-after-attaching test card 4000 0000 0000 0341 (tok_chargeCustomerFail). This is a separate test card from the direct-UI generic-decline card; the entry history confirmed generic_decline.

- Event: 01a15ed6-3b7f-738e-af7b-e3147e37f0ec; QA Card decline comparison 1792592457680.
- Entry: 01a15ed6-4761-74bc-874b-8eb83b7d9742.
- Confirm and charge returned HTTP 200; genuine history recorded “Card payment declined (generic_decline).” Manager row: Declined / Pending. The declined card was no longer offered as an active saved method.
- Manager Retry payment returned HTTP 200. The subsequent history explicitly said “Card payment not attempted (the saved payment method pinned to this charge is no longer active).” This is not another proven Stripe attempt.
- The history summary nevertheless showed “2 card attempts · 2 declined” including that not-attempted outcome. This may mislead a manager about actual provider attempts; it was observed, not corrected.
- Athlete selected the active saved 4242 Visa: HTTP 202. Without a separate manager retry, application history recorded success and the row became Collected / Confirmed.
- The final manager screenshot was captured after refresh. This run does not certify automatic roster refresh or resolve the existing stale-roster bug.
- Application history establishes the entry recovery; no independent Stripe API readback of that deferred-charge PaymentIntent was available. Card-change dispatch correlation and provider attempt count remain limited to the retained application evidence.

## Scheduler comparison and scope
Two targeted tests passed. They call the actual Stripe decline classifier and real competition scheduling functions with isolated stores and injected time, using version-16 policy: retries 24/72h, notices 24/72/120/168h, grace 168h, cutoff 10 days. The event is outside the short-notice window.

Generic decline: needs_new_method, 0 automatic execute commands, 4 notice events, manager flag at expiry.
Insufficient funds: retryable, 2 execute commands, 4 notice events, manager flag at expiry after both simulated retries fail.

This verifies classification and scheduling logic, not real provider attempts or email delivery. The saved insufficient-funds card could not be created through normal Stripe setup, as demonstrated in the preceding supplied-inbox report. Therefore a full live insufficient-funds entry-fee automatic-retry sequence remains unverified. Local collaborators simulate failure outcomes; these are not presented as real Stripe events.

## Evidence and limits
The page includes a genuine membership UI recording, an event-roster recording, five result screenshots, raw results.json and entry-results.json, and scheduler logs/JUnit XML/test source. Event fixture setup, confirm/charge, manager retry and card replacement were API-driven; the recording shows actual manager UI observations, not clicks for those API actions. Direct membership card submissions used real UI controls and Stripe Elements.

No shared rules, clocks, UUIDs or application code were changed. No refunds or new Jira tickets were created. No scheduled reminder email delivery is claimed for this comparison. The earlier short-notice cutoff defect remains a separate finding.

Stripe test-card reference: https://docs.stripe.com/testing#declined-payments.

