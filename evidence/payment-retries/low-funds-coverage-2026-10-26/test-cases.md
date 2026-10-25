# Payment retry card coverage additions

Prepared 26 October 2026. All 13 cases are Not run. Import the CSV into the confirmed master check sheet; the master location has not yet been identified. Historical execution reports were not changed.

The deferred-charge runner uses saved 0341 for generic declines. Earlier 9995 testing failed at SetupIntent with insufficient_funds and did not reach deferred automatic retries. Stripe 9995 is an insufficient-funds simulator, not a card whose balance QA can top up. Stripe documents that issuer-decline cards cannot normally be attached to a Customer: https://docs.stripe.com/testing#declined-payments

A real saved insufficient-funds fixture needs a provider-supported route before downstream live cases can run. If it is unavailable, mark those cases BLOCKED; isolated backend retry tests must be reported separately. The existing reminder-only CloudShell script explicitly prevents automatic retries and cannot be reused as an automatic-payment retry driver.

## PAY-CARD-001 - Generic-decline baseline

**Priority:** P0 | **Status:** Not run

**Preconditions:** Dev or staging with Stripe test mode; dedicated QA athlete/event; baseline current payment-rule version and provider attempt count; use isolated fixtures only. Saved decline-after-attaching card 4000 0000 0000 0341.

**Steps:** Enter event; Confirm & charge; wait for settled provider result; inspect payment, entry History and permitted actions.

**Expected:** Actual generic_decline is recorded; failure classification follows rules; do not claim a scheduled insufficient-funds retry from this fixture.

## PAY-CARD-002 - Insufficient-funds card at setup

**Priority:** P0 | **Status:** Not run

**Preconditions:** Dev or staging with Stripe test mode; dedicated QA athlete/event; baseline current payment-rule version and provider attempt count; use isolated fixtures only. Use Stripe 4000 0000 0000 9995 (tok_chargeDeclinedInsufficientFunds), future expiry and valid test CVC.

**Steps:** Attempt saved-card setup; record SetupIntent status, HTTP response and Stripe decline_code; inspect whether an entry/deferred charge exists.

**Expected:** Record card_declined / insufficient_funds. If setup is rejected, no usable saved method or retryable entry fixture is claimed; downstream live retry cases remain blocked.

## PAY-LOW-001 - Insufficient funds on deferred Confirm & charge

**Priority:** P0 | **Status:** Not run

**Preconditions:** Dev or staging with Stripe test mode; dedicated QA athlete/event; baseline current payment-rule version and provider attempt count; use isolated fixtures only. A provider-supported saved-card fixture must first reach a real deferred-charge failure with decline_code=insufficient_funds. Card 9995 rejection during SetupIntent does not satisfy this prerequisite. If unavailable, mark the live retry case BLOCKED and keep isolated backend tests separately labelled.

**Steps:** Confirm & charge the dedicated event; correlate the provider outcome with app payment, entry state and History.

**Expected:** Settles to an appropriate failed payment state instead of indefinite Pending; insufficient_funds is retained and classified according to deployed retry policy; one initial attempt only.

## PAY-LOW-002 - First automatic retry on the same low-funds card

**Priority:** P0 | **Status:** Not run

**Preconditions:** Dev or staging with Stripe test mode; dedicated QA athlete/event; baseline current payment-rule version and provider attempt count; use isolated fixtures only. A provider-supported saved-card fixture must first reach a real deferred-charge failure with decline_code=insufficient_funds. Card 9995 rejection during SetupIntent does not satisfy this prerequisite. If unavailable, mark the live retry case BLOCKED and keep isolated backend tests separately labelled.

**Steps:** Record T0 and pinned rules; run a separately scoped retry-capable worker just before the first due offset, then at it; deliver real provider outcome and read attempts.

**Expected:** No early attempt; exactly one due automatic retry on the same saved method; provider and History agree. A persistent insufficient-funds outcome is recorded as failed, not collected.

## PAY-LOW-003 - Second automatic retry after another low-funds failure

**Priority:** P0 | **Status:** Not run

**Preconditions:** Dev or staging with Stripe test mode; dedicated QA athlete/event; baseline current payment-rule version and provider attempt count; use isolated fixtures only. A provider-supported saved-card fixture must first reach a real deferred-charge failure with decline_code=insufficient_funds. Card 9995 rejection during SetupIntent does not satisfy this prerequisite. If unavailable, mark the live retry case BLOCKED and keep isolated backend tests separately labelled.

**Steps:** After the first scheduled retry settles insufficient_funds, advance to the next configured offset and run the scoped worker.

**Expected:** One new attempt for that slot; first failure time and pinned rules remain unchanged; failure settles and no successful capture is invented.

## PAY-LOW-004 - Completed first retry slot cannot run twice

**Priority:** P0 | **Status:** Not run

**Preconditions:** Dev or staging with Stripe test mode; dedicated QA athlete/event; baseline current payment-rule version and provider attempt count; use isolated fixtures only. A provider-supported saved-card fixture must first reach a real deferred-charge failure with decline_code=insufficient_funds. Card 9995 rejection during SetupIntent does not satisfy this prerequisite. If unavailable, mark the live retry case BLOCKED and keep isolated backend tests separately labelled.

**Steps:** Settle the first retry; rerun its same due time and a later tick before the next slot; compare provider IDs, retry counters and History.

**Expected:** No additional provider attempt or second charge command for the completed slot; no duplicate attempt history or retry-count increment.

## PAY-LOW-005 - Concurrent worker or manual retry cannot duplicate a charge

**Priority:** P0 | **Status:** Not run

**Preconditions:** Dev or staging with Stripe test mode; dedicated QA athlete/event; baseline current payment-rule version and provider attempt count; use isolated fixtures only. A provider-supported saved-card fixture must first reach a real deferred-charge failure with decline_code=insufficient_funds. Card 9995 rejection during SetupIntent does not satisfy this prerequisite. If unavailable, mark the live retry case BLOCKED and keep isolated backend tests separately labelled.

**Steps:** On an isolated fixture, race two scoped ticks for the same due slot; separately race an allowed manual retry against a worker; settle all results.

**Expected:** At most one active charge claim/attempt per eligible action; stable idempotency correlation; no duplicate capture; losing requests do not leave stale Pending.

## PAY-LOW-006 - Short-notice cutoff starts during active grace

**Priority:** P0 | **Status:** Not run

**Preconditions:** Dev or staging with Stripe test mode; dedicated QA athlete/event; baseline current payment-rule version and provider attempt count; use isolated fixtures only. A provider-supported saved-card fixture must first reach a real deferred-charge failure with decline_code=insufficient_funds. Card 9995 rejection during SetupIntent does not satisfy this prerequisite. If unavailable, mark the live retry case BLOCKED and keep isolated backend tests separately labelled.

**Steps:** Use a fixture where first failure is 12 days before the event and cutoff is 10 days; grace remains active at T0+48h. Evaluate before, at, and after cutoff including an overdue first retry and the later retry.

**Expected:** Against the requested strict-cutoff acceptance rule: no automatic retry at or after cutoff even while grace is active; escalate/flag as required; no charge command leaks from an overdue slot. Confirm product decision before sign-off.

## PAY-LOW-007 - Retry due exactly at grace deadline

**Priority:** P0 | **Status:** Not run

**Preconditions:** Dev or staging with Stripe test mode; dedicated QA athlete/event; baseline current payment-rule version and provider attempt count; use isolated fixtures only. A provider-supported saved-card fixture must first reach a real deferred-charge failure with decline_code=insufficient_funds. Card 9995 rejection during SetupIntent does not satisfy this prerequisite. If unavailable, mark the live retry case BLOCKED and keep isolated backend tests separately labelled.

**Steps:** Use scoped fixtures with a retry offset at the effective deadline; evaluate immediately before, at and after the deadline.

**Expected:** No retry after the effective deadline; exact equality follows approved boundary rule and is explicitly recorded; expiry cannot both charge and escalate inconsistently.

## PAY-LOW-008 - Recover from low funds with a valid replacement card

**Priority:** P0 | **Status:** Not run

**Preconditions:** Dev or staging with Stripe test mode; dedicated QA athlete/event; baseline current payment-rule version and provider attempt count; use isolated fixtures only. A provider-supported saved-card fixture must first reach a real deferred-charge failure with decline_code=insufficient_funds. Card 9995 rejection during SetupIntent does not satisfy this prerequisite. If unavailable, mark the live retry case BLOCKED and keep isolated backend tests separately labelled.

**Steps:** After a real low-funds failure, replace the entry card with saved Stripe 4242; wait for provider processing; inspect payment, entry, History and capture IDs.

**Expected:** Exactly one successful recovery capture; payment Collected and entry Confirmed; no indefinite Pending or duplicate charge; later ticks send no payment reminders/retries for the settled charge.

## PAY-LOW-009 - Low-funds reminder delivery and replay deduplication

**Priority:** P1 | **Status:** Not run

**Preconditions:** Dev or staging with Stripe test mode; dedicated QA athlete/event; baseline current payment-rule version and provider attempt count; use isolated fixtures only. A provider-supported saved-card fixture must first reach a real deferred-charge failure with decline_code=insufficient_funds. Card 9995 rejection during SetupIntent does not satisfy this prerequisite. If unavailable, mark the live retry case BLOCKED and keep isolated backend tests separately labelled.

**Steps:** Run each configured notification threshold in order; verify actual messages in the QA inbox; replay each threshold and compare delivery IDs.

**Expected:** One delivered reminder per due notification slot; wording fits a retryable insufficient-funds failure and actual planned retry; no duplicate email on replay; no notices after recovery.

## PAY-LOW-010 - Grace expiry while funds remain insufficient

**Priority:** P0 | **Status:** Not run

**Preconditions:** Dev or staging with Stripe test mode; dedicated QA athlete/event; baseline current payment-rule version and provider attempt count; use isolated fixtures only. A provider-supported saved-card fixture must first reach a real deferred-charge failure with decline_code=insufficient_funds. Card 9995 rejection during SetupIntent does not satisfy this prerequisite. If unavailable, mark the live retry case BLOCKED and keep isolated backend tests separately labelled.

**Steps:** Keep the low-funds fixture unpaid through all approved offsets and expiry; run a later tick and repeat expiry.

**Expected:** Expiry status/escalation is persisted once; no further charge after effective deadline or cutoff; no duplicate escalation; manager sees the correct available actions.

## PAY-LOW-011 - Low-funds UI, History and provider result stay consistent

**Priority:** P0 | **Status:** Not run

**Preconditions:** Dev or staging with Stripe test mode; dedicated QA athlete/event; baseline current payment-rule version and provider attempt count; use isolated fixtures only. A provider-supported saved-card fixture must first reach a real deferred-charge failure with decline_code=insufficient_funds. Card 9995 rejection during SetupIntent does not satisfy this prerequisite. If unavailable, mark the live retry case BLOCKED and keep isolated backend tests separately labelled.

**Steps:** Keep manager roster open through a failed retry and a separate successful recovery; inspect auto-refresh, reload, History and provider attempt/capture records.

**Expected:** UI updates according to product refresh behavior; failed retry is recorded once; successful payment is Collected/Confirmed; missing UI refresh is distinguished from missing backend settlement.
