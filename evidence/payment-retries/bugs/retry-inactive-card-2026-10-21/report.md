# Manager "Retry payment" after a generic decline returns success but attempts no payment, and is counted as a declined attempt

QA-RETRY-05 · Suggested priority: Medium (P2) · Dev, Stripe test mode · Rerun 21 October 2026, 15:31–15:36 UTC

Evidence page: https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/bugs/retry-inactive-card-2026-10-21/
First observed: https://kmousadcontractor-sudo.github.io/wsl-qa-report/evidence/payment-retries/card-decline-comparison-2026-10-21/ (Codex run, API-driven). This rerun drives the manager steps through the real Tour Manager UI.

## Summary
After an entry fee is declined with a generic decline, the saved card becomes inactive. The Tour Manager can still open Actions → Retry payment and press Proceed. The request returns HTTP 200 and the UI shows no error, but no payment is attempted: history records "Card payment not attempted (the saved payment method pinned to this charge is no longer active)". The history header then reads "2 card attempts · 2 declined", although Stripe was only called once. Retry payment stays available, so the manager can repeat a retry that can never charge.

## Environment and data
- Dev (app.dev.worldsurfleague.com), Stripe test mode (publishable key pk_test_ confirmed in the athlete page).
- Event: Turtle Bay Women's Pro (QS · Women, Hawaii/Tahiti Nui), event id 01a15f16-eb7b-7092-bf40-f010885443cc, entry fee USD 150.
- Athlete: Leilani Kanoho (fictional), fresh Mailosaur inbox; entry id 01a15f17-f898-75ad-8d75-4daeb3fcbc9b, reference QS-2026-W-060-001.
- Card: Stripe test card 4000 0000 0000 0341 (attaches to the customer, declines when charged: generic_decline).

## Steps to reproduce
1. Athlete registers (Regional membership paid with 4242) and enters the event with card 4000 0000 0000 0341.
2. Tour Manager closes entries, opens Athletes, clicks Confirm field & charge, ticks the review box and confirms.
3. Wait for the row to show Payment: Declined, Entry: Pending.
4. Click Actions for the athlete → Retry payment → Proceed.
5. Open the athlete's payment & communication history (click the athlete row).

## Expected
- Retry payment is not offered (or is disabled with a reason) while the pinned card is inactive, or the dialog explains that the athlete must update the card first.
- If a retry is requested anyway, the response and the UI say that no charge was attempted.
- The history count only counts real provider attempts: "1 card attempt · 1 declined" plus a separate "not attempted" line.

## Actual (rerun)
| Time UTC | Step | Result |
| --- | --- | --- |
| 15:33:04 | Confirm field & charge | POST /charge → HTTP 200, charged: 1 |
| 15:33:08 | Charge result | Payment Declined, Entry Pending; history "Card payment declined (generic_decline)"; actions include retry |
| 15:33:19 | Retry payment → Proceed | POST /entries/{id}/actions {code: retry} → HTTP 200, no error shown |
| 15:33:35 | After retry | Still Declined / Pending; history adds "Card payment not attempted (the saved payment method pinned to this charge is no longer active)"; header "2 card attempts · 2 declined"; Retry payment still offered |
| 15:36:21 | Athlete changes card to test Visa 4242 (card-change endpoint, HTTP 202) | Entry re-charged automatically |
| 15:36:29 | Final | Collected / Confirmed |

## Impact
- The manager believes a retry was made; nothing happened and the UI does not say so.
- Attempt counts in the history overstate provider attempts, which matters for retry limits, audits and support.
- The manager can keep pressing Retry with no effect, while the real fix (a new card) is with the athlete.

## Related finding (separate ticket): no email at the first decline
Within 3 minutes of the decline the athlete received no email (Mailosaur inbox checked from 15:33:04 to 15:36:07 UTC: 0 messages). Dev payment rules send the first notice 24 hours after the failure (24 h · 3 days · 5 days · 7 days). The earlier full-recovery run shows the same gap: decline at 14:37 UTC, first "could not be taken" email only when the 24-hour check ran.

## Evidence
- Recording of the Tour Manager UI: video/manager-ui.webm
- Screenshots (highlighted): 01-declined-after-confirm.png, 02-retry-menu.png, 03-retry-dialog.png, 04-history-not-attempted.png, 05-collected-after-card-change.png
- Timestamped log with API responses, entry states, history and inbox check: results.json
- Script: scripts/bugs/rerun-retry-inactive-card.mjs (wsl-qa-automation)

## Technical notes
- Payment classifies a generic decline as needs_new_method; only retryable declines are retried automatically. A needs_new_method charge needs a new card first (wsl-competition-service domain/payment_retries.py).
- The pinned saved payment method becomes inactive after the generic decline, so the retry is refused inside payment with "not attempted", but the BFF still answers 200 with the refreshed seed list.
- Changing the card from RETRYABLE or NEEDS_NEW_METHOD triggers an immediate retry (RETRY_IMMEDIATELY_AFTER_PAYMENT_METHOD_UPDATE in wsl-payment-service), which is why recovery happened without a manager retry.

## Acceptance criteria
1. For a charge whose pinned card is inactive, Retry payment is hidden or disabled with the reason "the athlete needs to update the card".
2. A retry that results in "not attempted" returns a response the UI shows to the manager (not a silent 200 refresh).
3. The history summary counts only real card attempts; "not attempted" is shown but not counted as an attempt or a decline.
4. Once the athlete updates the card, the existing automatic re-charge continues to work (covered by this rerun).
