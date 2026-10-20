# Payment retry test cases and edge-case matrix

Prepared 20 October 2026. **110 designed cases; all Not run.** Earlier 12 live assertions and 12 clock probes are separate executions and do not mark this larger matrix passed.

## Baseline and test data
- Policy: version 16; automatic retry offsets 24/72 hours; grace 168 hours; notices 24/72/120/168 hours; short-notice window 10 days.
- T0: first actual failure timestamp, baseline 2026-10-20 12:00:00 UTC. Offsets always start from T0.
- Baseline event: 2026-11-20; UTC-based cutoff C=2026-11-10 00:00 UTC; effective deadline D=min(T0+168h,C)=2026-10-27 12:00 UTC. Override C explicitly in short-notice cases.
- Isolate fixtures by organisation/event/entry; parameterise boundary cases at minus 1ms, exact instant and plus 1ms. Use UTC-aware times, then verify presentation separately.
- Required cards/failures: active successful card, genuine retryable failure, needs-new-method, authentication-required, unknown class, no-card refusal. A generic-decline inactive card does not prove automatic retries.
- Required roster: full field with a declined athlete and at least one genuine eligible alternate; separate already-paid, waived, overridden, withdrawn and terminal entries.

## Execution layers and evidence
- Domain/advanced-clock: precise timing arithmetic and classifications; no waiting or provider calls.
- Database/integration: real Postgres locks, row-level security, transactions, outbox and duplicate delivery.
- Dev end-to-end: real UI/API, provider test-mode attempts, actual webhooks and test-inbox notification evidence.
- Use controlled test clocks for boundaries. For dev timer acceleration, require a scoped fixture and DB/job access; preserve UUIDs and idempotency identity, record before/after values, never shorten shared rules. Changing next_attempt_at alone does not make a non-retryable failure valid.
- Capture entry/charge/org IDs, pinned policy and deadline, request/message IDs, execute/release/outcome times, provider PaymentIntent/attempt ID, before/after DB rows, API responses and actual UI/history/inbox results.
- Assert request accepted, command dispatched, provider attempted and funds collected as distinct facts.

## Priorities and expected-result authority
P0: charge correctness, stop conditions, security, concurrency or financial reconciliation. P1: timing/configuration, recovery, notifications and observability. Requirement cases state intended acceptance criteria and may expose known defects; Current code cases document implementation behavior, not product approval. Product decision cases require the decision below before a pass/fail verdict. No source-code inference is a live-test result.

## Product decisions to resolve
- **DEC-01: Strict event cutoff versus late tolerance.** Should a scheduled retry be allowed after event-minus-10-days when it was due before cutoff? Current _work permits bounded late dispatch.
- **DEC-02: Retry exactly at effective deadline.** Current due<=deadline logic can dispatch at deadline before flagging. Confirm intended policy.
- **DEC-03: Business timezone.** Current event_starts_at uses UTC midnight. Confirm venue-local versus UTC cutoff interpretation.
- **DEC-04: Queued reminder after settlement.** Confirm suppression or rewording rules for already queued reminders.
- **DEC-05: Archived/cancelled events.** Confirm retry stop and financial reconciliation policy for these event states.

## Configuration and rule pinning

### RET-001 — Read current rules

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Authenticated manager; baseline version 16.
- Steps: GET payment-rules and compare all values.
- Expected: Retry offsets 24/72h; grace 168h; notices 24/72/120/168h; cutoff 10d.
- Actual/evidence: pending execution.

### RET-002 — Pin rules on first failure

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Fresh retryable charge; version 16 active.
- Steps: Record first failure at T0; inspect charge row.
- Expected: first_failed_at=T0; version 16 and effective deadline pinned once.
- Actual/evidence: pending execution.

### RET-003 — Rule change cannot reschedule existing charge

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Charge already pinned to version 16.
- Steps: Change isolated test organisation to version 17; process another failure.
- Expected: Original charge retains version 16, T0 and deadline; no revised promise.
- Actual/evidence: pending execution.

### RET-004 — New charge uses new rule version

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Isolated organisation has version 17.
- Steps: Fail a new independent charge.
- Expected: New charge uses version 17; older charge unchanged.
- Actual/evidence: pending execution.

### RET-005 — Repeated failure preserves first-failure clock

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Failure at T0 already recorded.
- Steps: Record failures at T0+25h and T0+73h.
- Expected: T0 never moves; grace is not restarted.
- Actual/evidence: pending execution.

### RET-006 — Rule version zero defaults

- Priority: P1; status: Not run; oracle: Current code.
- Preconditions: Isolated organisation has no saved settings.
- Steps: Create first failure; read pinned version and defaults.
- Expected: Version 0 uses code defaults; do not substitute dev version-16 values.
- Actual/evidence: pending execution.

### RET-007 — Reject invalid configuration

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Isolated settings tenant.
- Steps: Try duplicate/descending/negative/fractional offsets; retry beyond grace; invalid types and bounds.
- Expected: Invalid input rejected with actionable errors and no partial save; exact numeric limits follow schema.
- Actual/evidence: pending execution.

### RET-008 — Zero automatic retries

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Isolated policy retry list empty.
- Steps: Fail a charge and advance all notice boundaries.
- Expected: No automatic execute; notices and grace decision follow policy.
- Actual/evidence: pending execution.

### RET-009 — Concurrent settings edits

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Two managers read same settings version.
- Steps: Submit different updates using same expected version.
- Expected: One wins; stale write rejected; no lost update.
- Actual/evidence: pending execution.

### RET-010 — Settings access control

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Athlete and unauthorised manager sessions.
- Steps: Read/edit payment rules.
- Expected: Unauthorised operations rejected; no change to shared configuration.
- Actual/evidence: pending execution.

## Failure classification and first attempt

### RET-011 — Retryable initial decline

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Eligible field entry; retryable provider failure.
- Steps: Confirm and charge; consume failure at T0.
- Expected: Payment pending; first retry scheduled at T0+24h; correct amount/card/reference.
- Actual/evidence: pending execution.

### RET-012 — Needs-new-method decline

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Provider returns needs_new_method.
- Steps: Consume failure; advance past 24h and 72h.
- Expected: No automatic charge on the invalid card; recovery guidance/notices remain.
- Actual/evidence: pending execution.

### RET-013 — Authentication-required decline

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Provider returns action_required.
- Steps: Consume failure; tick at all retry boundaries.
- Expected: No blind off-session retry; athlete is offered appropriate authentication recovery.
- Actual/evidence: pending execution.

### RET-014 — Unknown failure class

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Failure class null or unrecognised.
- Steps: Consume failure; run due ticks.
- Expected: No automatic retry based on an assumed classification.
- Actual/evidence: pending execution.

### RET-015 — First payment refusal without attempt

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: No usable saved card; no prior failure class.
- Steps: Consume attempted=false result.
- Expected: Clock starts for notices/escalation; no provider attempt falsely recorded; no auto retry.
- Actual/evidence: pending execution.

### RET-016 — Refused retry preserves earlier classification

- Priority: P1; status: Not run; oracle: Current code.
- Preconditions: Prior retryable decline then attempted=false.
- Steps: Consume refusal and inspect retry state.
- Expected: Earlier genuine failure class preserved; counters distinguish refusal from attempted decline.
- Actual/evidence: pending execution.

### RET-017 — Successful initial payment

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Valid saved test card.
- Steps: Confirm and charge; consume success twice.
- Expected: One successful charge; eligible entry confirmed; no recovery schedule.
- Actual/evidence: pending execution.

### RET-018 — Failure with missing competition charge

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Unknown entry/reference or unrelated organisation.
- Steps: Deliver failure fact.
- Expected: No unrelated state changed; diagnostic behavior recorded; no invented charge.
- Actual/evidence: pending execution.

### RET-019 — Duplicate first-failure event

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Same event delivered twice.
- Steps: Consume duplicate with identical event identity.
- Expected: T0/policy/deadline unchanged; no duplicate notice/execute/audit effects.
- Actual/evidence: pending execution.

### RET-020 — Failure after success

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Charge already paid.
- Steps: Deliver older failure fact.
- Expected: Paid state does not regress; retry not restarted.
- Actual/evidence: pending execution.

## Retry schedule and exact boundaries

### RET-021 — First due boundary

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Retryable charge scheduled for T0+24h.
- Steps: Tick at due minus 1ms, exactly due, due plus 1ms on separate fixtures.
- Expected: No early dispatch; one dispatch at due; later duplicate tick cannot repeat it.
- Actual/evidence: pending execution.

### RET-022 — Second due boundary

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: First retry failed; second scheduled at T0+72h.
- Steps: Tick at due minus 1ms, due, due plus 1ms.
- Expected: No early second attempt; one at due; first-failure anchor retained.
- Actual/evidence: pending execution.

### RET-023 — 72 hours is not relative to first retry

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: First attempt ran late at T0+25h.
- Steps: Process its failure and inspect next due.
- Expected: Second due stays T0+72h, not T0+97h.
- Actual/evidence: pending execution.

### RET-024 — Retry attempts exhausted

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Two configured automatic attempts sent and failed.
- Steps: Advance beyond 72h while before grace end.
- Expected: No third automatic attempt; no implied retry at 168h.
- Actual/evidence: pending execution.

### RET-025 — Manual retry does not consume automatic index incorrectly

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Manual retry before 24h fails.
- Steps: Inspect retries_sent and next due.
- Expected: Manual and automatic attempts distinguished; configured automatic count not silently consumed.
- Actual/evidence: pending execution.

### RET-026 — Late manual decline skips old due times

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Manual retry fails at T0+50h.
- Steps: Calculate next due.
- Expected: Next retry 72h; no immediate replay of missed 24h attempt.
- Actual/evidence: pending execution.

### RET-027 — Failure after final offset

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Manual failure at T0+100h.
- Steps: Recalculate automatic due.
- Expected: No remaining automatic due; no burst of backdated attempts.
- Actual/evidence: pending execution.

### RET-028 — Exact-due rescheduling cannot create duplicate attempt

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Failure/replay lands exactly on configured offset.
- Steps: Recalculate due and tick repeatedly.
- Expected: At most one logical attempt for that offset; no loop at the same timestamp.
- Actual/evidence: pending execution.

### RET-029 — Different attempt keys, same charge reference

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Two legitimate scheduled attempts.
- Steps: Inspect execute commands.
- Expected: Keys retry-{chargeId}-1 and retry-{chargeId}-2; same original entry reference.
- Actual/evidence: pending execution.

### RET-030 — Fresh missing timer fields

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Legacy/incomplete charge lacks first_failed_at or due.
- Steps: Run retry worker.
- Expected: No accidental charge; explicit skip/recovery behavior; no whole-pass crash.
- Actual/evidence: pending execution.

### RET-031 — Event start unavailable

- Priority: P1; status: Not run; oracle: Current code.
- Preconditions: Retryable charge with no event start.
- Steps: Pin deadline.
- Expected: Deadline=T0+168h; graceful fallback recorded.
- Actual/evidence: pending execution.

### RET-032 — Amount and currency cannot drift

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Entry amount/card agreement established.
- Steps: Change unrelated prices; run retries.
- Expected: Charge uses agreed stored amount/currency; no new tax/fee calculation without explicit re-agreement.
- Actual/evidence: pending execution.

## Grace period and event cutoff

### RET-033 — Seven-day deadline

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Event sufficiently far away.
- Steps: Tick at T0+168h minus 1ms, exactly 168h, plus 1ms.
- Expected: Before deadline no premature expiry; at deadline escalate if no in-flight attempt; do not auto-withdraw.
- Actual/evidence: pending execution.

### RET-034 — Event cutoff wins

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Event cutoff=T0+48h.
- Steps: Fail at T0 and tick at 24h/48h/72h.
- Expected: 24h retry eligible; 72h retry not scheduled; escalate at 48h.
- Actual/evidence: pending execution.

### RET-035 — Grace deadline wins

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Event cutoff later than T0+168h.
- Steps: Pin deadline.
- Expected: Use seven-day grace, not later event cutoff.
- Actual/evidence: pending execution.

### RET-036 — Cutoff and grace equal

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Event cutoff exactly T0+168h.
- Steps: Pin deadline and tick boundary.
- Expected: One effective deadline; no duplicate escalation.
- Actual/evidence: pending execution.

### RET-037 — Failure inside short-notice window

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: T0 is later than event minus 10 days.
- Steps: Record failure then worker tick.
- Expected: No automatic retry; escalate on processing without granting fresh seven days.
- Actual/evidence: pending execution.

### RET-038 — Failure exactly at event cutoff

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: T0 equals event minus 10 days.
- Steps: Record failure then tick at same instant.
- Expected: No future retry; escalation is due immediately.
- Actual/evidence: pending execution.

### RET-039 — Failure one instant before cutoff

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Cutoff=T0+1ms.
- Steps: Record failure; tick before/at/after cutoff.
- Expected: No retry that cannot fit; exact escalation boundary respected.
- Actual/evidence: pending execution.

### RET-040 — Event today or already started

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Failure after cutoff and event-start boundary.
- Steps: Record decline and run worker.
- Expected: No automatic recovery chase extending into event; TM action required.
- Actual/evidence: pending execution.

### RET-041 — Retry exactly at cutoff

- Priority: P0; status: Not run; oracle: Product decision.
- Preconditions: Isolated policy permits due==effective deadline.
- Steps: Tick at that instant.
- Expected: Current code permits due retry before flag; confirm whether Product accepts this against strict cutoff wording.
- Actual/evidence: pending execution.

### RET-042 — Late tick versus strict cutoff

- Priority: P0; status: Not run; oracle: Product decision.
- Preconditions: Due retry before deadline; worker wakes after cutoff but within 24h tolerance.
- Steps: Tick and inspect dispatch.
- Expected: Code can dispatch a previously scheduled retry after deadline; decide strict stop requirement before sign-off.
- Actual/evidence: pending execution.

### RET-043 — UTC midnight versus venue midnight

- Priority: P1; status: Not run; oracle: Product decision.
- Preconditions: Same date at UTC-10 and UTC+14 venues.
- Steps: Compare event cutoff timestamps.
- Expected: Current code uses UTC date midnight; confirm business timezone requirement and any hour-level discrepancy.
- Actual/evidence: pending execution.

### RET-044 — DST/leap-day/year rollover

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: T0 near DST change, Feb 29 or Dec 31.
- Steps: Advance elapsed 24/72/168 hours.
- Expected: No duplicated/skipped offsets from local clock changes; exact UTC elapsed durations.
- Actual/evidence: pending execution.

## Notifications and escalation

### RET-045 — All four notice boundaries

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Unpaid eligible entry; no prior notices.
- Steps: Parameterise N=24/72/120/168h; tick N-1ms/N/N+1ms.
- Expected: Each due notice once; none early; repeated tick does not duplicate.
- Actual/evidence: pending execution.

### RET-046 — Non-retryable card still notified

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Needs-new-method or action-required failure.
- Steps: Advance notice boundaries before deadline.
- Expected: Actionable recovery notices sent without automatic off-session attempts.
- Actual/evidence: pending execution.

### RET-047 — Latest overdue notice only

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Worker down from T0 until hour 130.
- Steps: Resume before deadline.
- Expected: Send latest due notice, not a burst of day-1/day-3/day-5 messages.
- Actual/evidence: pending execution.

### RET-048 — Notice after shortened deadline

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Effective deadline 48h.
- Steps: Tick at hours 72/120/168.
- Expected: No notice whose scheduled offset is beyond deadline; escalation handled once.
- Actual/evidence: pending execution.

### RET-049 — Success suppresses later notices

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Payment succeeds before next notice.
- Steps: Advance all later boundaries.
- Expected: No further retry/reminder/escalation for settled charge.
- Actual/evidence: pending execution.

### RET-050 — Withdrawal suppresses recovery notices

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Entry withdrawn before next notice.
- Steps: Advance due boundaries.
- Expected: Removed athlete no longer chased for entry payment.
- Actual/evidence: pending execution.

### RET-051 — Flag is idempotent

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Expired unpaid entry already flagged.
- Steps: Repeat worker ticks/replayed failure.
- Expected: No duplicate TM action-required escalation; no new automatic schedule.
- Actual/evidence: pending execution.

### RET-052 — Grace expiry does not auto-promote

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Unpaid entry reaches deadline.
- Steps: Run worker and inspect roster/alternates.
- Expected: Flag for manager decision; no implied withdrawal or alternate promotion.
- Actual/evidence: pending execution.

### RET-053 — Correct notice payload and recipient

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Different athlete and account-holder/guardian identities.
- Steps: Inspect staged notification and actual test inbox.
- Expected: Correct account holder, athlete/event, deadline, next retry and recovery action; no cross-account disclosure.
- Actual/evidence: pending execution.

### RET-054 — Notification delivery failure

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Notification service unavailable or redelivery.
- Steps: Fail/retry delivery.
- Expected: No duplicate payment; delivery retry is distinguished from business payment retry.
- Actual/evidence: pending execution.

### RET-055 — Stale pending notice after success

- Priority: P1; status: Not run; oracle: Product decision.
- Preconditions: Notice queued; payment settles before delivery.
- Steps: Deliver queued message.
- Expected: Define suppress/reword policy; do not claim unpaid without checking approved delivery semantics.
- Actual/evidence: pending execution.

## Card change and successful recovery

### RET-056 — Valid replacement after needs-new-method

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Declined entry; second active test card owned by account.
- Steps: Update that entry to valid card.
- Expected: Card repointed; immediate retry allowed; one successful payment; correct entry becomes confirmed.
- Actual/evidence: pending execution.

### RET-057 — Valid replacement after retryable failure

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Retryable entry scheduled for future retry.
- Steps: Change to valid card before next due.
- Expected: Immediate recovery; later schedule cannot charge again after success.
- Actual/evidence: pending execution.

### RET-058 — Same update replayed

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Valid card update with same request identity.
- Steps: Replay concurrently and sequentially.
- Expected: One logical update/attempt; no duplicate successful capture.
- Actual/evidence: pending execution.

### RET-059 — Same-card repoint in retryable state

- Priority: P1; status: Not run; oracle: Current code.
- Preconditions: Active same card, retryable charge.
- Steps: Submit explicit update naming same card.
- Expected: Observe documented immediate retry behavior; no hidden customer-wide sweep.
- Actual/evidence: pending execution.

### RET-060 — Foreign or inactive saved card

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Card belongs to other account or is inactive.
- Steps: POST entry-card change.
- Expected: Reject; original agreement unchanged; no foreign-card charge.
- Actual/evidence: pending execution.

### RET-061 — Change card on unrelated entry

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Two entries with different selected cards.
- Steps: Update card for entry A.
- Expected: Entry B remains pinned to its own card; no account-wide retry fan-out.
- Actual/evidence: pending execution.

### RET-062 — Authentication-required recovery

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Card requires customer authentication.
- Steps: Complete/fail/cancel authentication in test flow.
- Expected: Only authenticated eligible charge succeeds; safe actionable state on failure/cancel.
- Actual/evidence: pending execution.

### RET-063 — Card update during processing

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Charge CHARGING.
- Steps: Submit card update while attempt is active.
- Expected: Do not silently move an in-flight attempt to another card; preserve outcome attribution.
- Actual/evidence: pending execution.

### RET-064 — Card update races scheduled retry

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Due scheduled attempt and card update start together.
- Steps: Force both orderings using barriers.
- Expected: One permitted in-flight attempt at a time; exact card/amount known; no duplicate collection.
- Actual/evidence: pending execution.

### RET-065 — Card update after success or release

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Charge paid/released.
- Steps: Try repoint and retry.
- Expected: No new collection; operation rejected or safe no-op per contract.
- Actual/evidence: pending execution.

## Withdrawal, alternate and override stop conditions

### RET-066 — Withdrawal before due

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Unpaid entry with retry scheduled tomorrow.
- Steps: Withdraw then advance past all due times.
- Expected: Entry withdrawn; charges/retry eligibility cancelled; no execute or reminders.
- Actual/evidence: pending execution.

### RET-067 — Immediate retry after withdrawal with FAILED row

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: FAILED unpaid entry; no scheduled retry.
- Steps: Withdraw then direct POST retry immediately.
- Expected: Reject at backend regardless of UI actions; no execute command; regression for observed gap.
- Actual/evidence: pending execution.

### RET-068 — Retry after settled withdrawal

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Withdrawn entry already reconciled.
- Steps: POST retry with new and old idempotency keys.
- Expected: No fresh attempt; replay cannot revive payment eligibility.
- Actual/evidence: pending execution.

### RET-069 — Withdrawal during queued dispatch

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Execute staged but not consumed.
- Steps: Withdraw before consumer runs; test both message orders.
- Expected: Release/cancellation prevents unnecessary new charge; explicit handling if execute already won.
- Actual/evidence: pending execution.

### RET-070 — Withdrawal during provider processing

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Payment CHARGING.
- Steps: Withdraw while provider response/webhook is held.
- Expected: Track cancellation requested; keep withdrawn; reconcile success/failure and expose required Finance action.
- Actual/evidence: pending execution.

### RET-071 — Valid-card update then removal then retry

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Declined entry with new valid test card.
- Steps: Update card; withdraw; send retry; correlate all commands/webhooks.
- Expected: Reject new post-removal retry; account for any already-started attempt; never hide successful payment requiring action.
- Actual/evidence: pending execution.

### RET-072 — Declined athlete replaced by alternate

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Full field plus eligible alternate.
- Steps: Withdraw declined athlete; promote alternate; advance old due times.
- Expected: Old athlete stays withdrawn with no new retries; new athlete has independent entry/payment reference and seat.
- Actual/evidence: pending execution.

### RET-073 — Alternate promotion while old payment unresolved

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Original attempt processing; place released.
- Steps: Promote alternate before old payment result arrives.
- Expected: No seat restoration or alternate eviction from late old success; Finance reconciliation retained.
- Actual/evidence: pending execution.

### RET-074 — Re-entry after withdrawal

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Same athlete re-enters legitimately.
- Steps: Create new entry and eligible charge; deliver old retry messages.
- Expected: Old entry not revived; new charge is separately authorised; no reuse of old payment identity.
- Actual/evidence: pending execution.

### RET-075 — Fee waived before retry

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Unpaid entry; fee waiver permitted.
- Steps: Waive fee then tick/manual retry.
- Expected: No further charge or notice; waiver reason/audit preserved.
- Actual/evidence: pending execution.

### RET-076 — Proceed without payment

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: TM records reasoned payment override.
- Steps: Advance schedule and request manual retry.
- Expected: No charge after clearance; UI/history identify override.
- Actual/evidence: pending execution.

### RET-077 — Waiver races manual retry

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Unpaid failed charge.
- Steps: Submit waiver and retry concurrently.
- Expected: Atomic winner; no successful fee waiver while a card attempt is still legitimately in flight.
- Actual/evidence: pending execution.

### RET-078 — Denied/rejected entry cannot retry

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Terminal entry state other than withdrawn.
- Steps: Send stale/direct retry action.
- Expected: Backend rejects terminal entry; UI visibility is not the security guard.
- Actual/evidence: pending execution.

### RET-079 — Event archived/cancelled with unpaid entries

- Priority: P1; status: Not run; oracle: Product decision.
- Preconditions: Unpaid entries and scheduled recoveries.
- Steps: Archive/cancel event using supported path.
- Expected: Approved policy explicitly determines stop/refund behavior; no accidental charging under ambiguous lifecycle.
- Actual/evidence: pending execution.

## Concurrency, idempotency and event ordering

### RET-080 — Same retry key concurrent replay

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: One failed entry; two identical request keys.
- Steps: POST two retry requests together.
- Expected: One logical claim/execute; replay response allowed; at most one provider attempt.
- Actual/evidence: pending execution.

### RET-081 — Different retry keys concurrent race

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: One failed entry; distinct keys.
- Steps: POST two retries at barrier.
- Expected: One wins claim; other refused; one provider attempt.
- Actual/evidence: pending execution.

### RET-082 — Two scheduler instances

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Same charge due in database.
- Steps: Run two workers concurrently with real repositories.
- Expected: FOR UPDATE SKIP LOCKED prevents duplicate claim; one logical dispatch.
- Actual/evidence: pending execution.

### RET-083 — Manual versus scheduler race

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Same charge due and manually retryable.
- Steps: Start manual claim and scheduler together.
- Expected: At most one in-flight attempt; stable attempt identity and truthful counters.
- Actual/evidence: pending execution.

### RET-084 — Duplicate execute delivery

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Payment receives same command twice.
- Steps: Replay same message/request ID.
- Expected: Same logical result; no second processor charge.
- Actual/evidence: pending execution.

### RET-085 — Duplicate paid/failed webhooks

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Deliver same event repeatedly.
- Steps: Inspect payment, competition, history and notices.
- Expected: Monotonic state; one effective outcome; no duplicate confirmation/notification.
- Actual/evidence: pending execution.

### RET-086 — Paid then stale failure

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Deliver newer paid fact before older failed fact.
- Steps: Process both.
- Expected: Paid cannot become failed or reschedule automatically.
- Actual/evidence: pending execution.

### RET-087 — Withdraw then late paid fact

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Local charge cancelled; payment succeeds later.
- Steps: Deliver success after withdrawal.
- Expected: Entry remains withdrawn; payment fact reconciled and visible; no silent loss of paid evidence.
- Actual/evidence: pending execution.

### RET-088 — Failures arrive out of order

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Multiple genuine attempt outcomes delayed.
- Steps: Deliver older failure after newer state.
- Expected: Preserve first-failure anchor; do not regress or restart exhausted schedule.
- Actual/evidence: pending execution.

### RET-089 — Retry after API timeout

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Client times out after accepted retry.
- Steps: Resend identical idempotency key.
- Expected: Return/recover original action; no second logical attempt.
- Actual/evidence: pending execution.

## Outages, deadlines and unanswered attempts

### RET-090 — Worker shortly late

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Retry due 24h; first worker tick 25h.
- Steps: Run pass.
- Expected: One due attempt; no catch-up burst; unchanged policy/deadline.
- Actual/evidence: pending execution.

### RET-091 — Worker skips first offset

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: No failure rescheduling until after 24h.
- Steps: Compute next retry at hour 50.
- Expected: Skip old 24h slot; schedule 72h if within deadline.
- Actual/evidence: pending execution.

### RET-092 — Too-late overdue attempt

- Priority: P0; status: Not run; oracle: Current code.
- Preconditions: Scheduled retry remains; tick at deadline+24h.
- Steps: Test just before/exactly/after tolerance.
- Expected: Code sends only before strict tolerance end; at/after it no late dispatch.
- Actual/evidence: pending execution.

### RET-093 — Command unanswered within timeout

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Requested charge; request_timeout_at future.
- Steps: Tick before timeout.
- Expected: Remain requested; no duplicate retry/waiver admission.
- Actual/evidence: pending execution.

### RET-094 — Command unanswered at timeout

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Requested charge; timeout exactly now.
- Steps: Run release-unanswered then worker.
- Expected: Release claim safely; recovery eligibility recalculated; no permanent stuck state.
- Actual/evidence: pending execution.

### RET-095 — Late answer after timeout/retry

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Old attempt answers after claim release.
- Steps: Deliver late paid/failed result with attempt correlation.
- Expected: No duplicate capture or state regression; reconcile correct attempt.
- Actual/evidence: pending execution.

### RET-096 — Grace expires during in-flight retry

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: A permitted final attempt is awaiting answer.
- Steps: Tick at deadline before answer_by.
- Expected: Do not flag while valid answer window is open; do not dispatch another attempt.
- Actual/evidence: pending execution.

### RET-097 — No answer beyond final window

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: In-flight attempt never answers.
- Steps: Tick at/after answer_by.
- Expected: Flag rather than hold place indefinitely; no endless automatic retries.
- Actual/evidence: pending execution.

### RET-098 — One corrupt charge does not stop others

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Two due charges; first throws inside savepoint.
- Steps: Run full pass.
- Expected: Other valid charge processed; failed count/job status exposes error; no partial inconsistent row.
- Actual/evidence: pending execution.

### RET-099 — Crash around outbox commit

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Crash before commit/after commit/before publish.
- Steps: Restart worker and relay.
- Expected: No orphan state or duplicate logical payment; transactional outbox and idempotency preserve recovery.
- Actual/evidence: pending execution.

### RET-100 — Dependency outage

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Rules lookup/DB/NATS/payment unavailable.
- Steps: Inject each fault and retry service recovery.
- Expected: Visible failure; no false success or new policy promise; safe retriable processing.
- Actual/evidence: pending execution.

## Security, finance visibility and evidence

### RET-101 — Athlete cannot trigger manager retry

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Athlete token and another account token.
- Steps: Call TM retry endpoint.
- Expected: Permission denied; no execute or payment side effect.
- Actual/evidence: pending execution.

### RET-102 — Organisation isolation

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Two organisations with known own fixtures.
- Steps: Try cross-org retry, histories and identifiers.
- Expected: No cross-org read/claim/charge; scoped storage queries enforce ownership.
- Actual/evidence: pending execution.

### RET-103 — Tampered payment inputs

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Valid retry endpoint plus injected user/card/amount/reference fields.
- Steps: Attempt charge redirection or reprice.
- Expected: Only authorised stored agreement used; reject unsupported tampering.
- Actual/evidence: pending execution.

### RET-104 — History distinguishes outcomes

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Accepted request; provider attempted vs refused.
- Steps: Compare histories for both.
- Expected: Do not label HTTP 200 as collected; distinguish charge started, declined, not attempted and succeeded.
- Actual/evidence: pending execution.

### RET-105 — UI state after recovery

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Keep TM roster open during actual valid-card recovery.
- Steps: Observe without reload, then reload.
- Expected: Pending/Collected/Confirmed truthful; no stale Retry action after success.
- Actual/evidence: pending execution.

### RET-106 — Withdrawn success visible for Finance

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Withdrawn entry with late paid outcome.
- Steps: Inspect roster, history and finance/reconciliation path.
- Expected: Successful payment not silently hidden; approved reconciliation/refund action traceable.
- Actual/evidence: pending execution.

### RET-107 — Refund/reconciliation idempotency

- Priority: P0; status: Not run; oracle: Requirement.
- Preconditions: Refund required by approved policy.
- Steps: Repeat workflow/events and retry refund request.
- Expected: At most one correct refund; correct amount/currency; audit links original charge.
- Actual/evidence: pending execution.

### RET-108 — Audit and correlation completeness

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Retry, withdrawal, release and outcome recorded.
- Steps: Trace request/message/entry/charge/provider IDs.
- Expected: Every transition attributable; keys preserved; timestamps distinguish request, dispatch, provider and consumer times.
- Actual/evidence: pending execution.

### RET-109 — No sensitive data in evidence

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Report exports and recordings available.
- Steps: Scan exported API payloads and media.
- Expected: No passwords, tokens, client secrets or full card details; use test-mode identifiers only.
- Actual/evidence: pending execution.

### RET-110 — Load and fairness under bounded batch

- Priority: P1; status: Not run; oracle: Requirement.
- Preconditions: Many due charges across organisations; varied failures.
- Steps: Run controlled local/integration batch.
- Expected: No tenant starvation or duplicate claims; each failed item isolated; avoid payment-provider load testing.
- Actual/evidence: pending execution.
