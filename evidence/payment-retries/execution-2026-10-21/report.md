# Payment retry matrix execution — 21 October 2026

Matrix outcomes: {"PASS":44,"PARTIAL":51,"FAIL":5,"REVIEW":5,"BLOCKED":5}. Native tests: {"PASS":847,"FAIL":7}. Live retry assertions: {"PASS":12}. Fresh recovery assertions: {"PASS":12,"FAIL":1}. These counts are separate and must not be added as matrix coverage.

PASS means the stated case was verified within the named execution layer. PARTIAL means some steps or external integrations remain unverified. BLOCKED means the case was not executed. REVIEW means product approval is needed for observed current-code behavior. FAIL means an acceptance assertion failed.

## Material findings
1. Already-used 24h offset can be selected again at exactly that timestamp.
2. Terminal entries with remaining FAILED charge eligibility can claim manual retries; repository-only DB reproduction plus four terminal-state unit variants. Normal application withdrawal/alternate worker path passed.
3. Competition charge-result handler ignores late success after cancellation; broader Finance reconciliation not established.
4. Open manager roster stays stale after successful live card recovery until refresh (RET-105).

## Scope and environment
Selected native suites ran on local source using disposable Postgres and explicit test clocks. Native defaults include three retries/nine-day cutoff; added version-16 cases explicitly use two retries/ten days. The deployed revision was not verified. A separate local environment was needed because checked-out package metadata references conflicting remote versions. Final environment is reproducible from the retained manifest. No application fix was made. Fresh live setup initially hit schedule conflicts; the runner was updated to acknowledge QA schedule warnings and a new isolated fixture was used. The first shared-cookie recovery observation was retested with separate athlete/manager sessions. No shared payment rules or dev database timestamps were edited.

## Known limits
No controlled provider-held cancellation, broker crash/restart, real notification outage/inbox matrix, refund or live full-format alternate scenario. Partial evidence is not counted as a passed case. No Jira ticket was created.

## Case-by-case results

### RET-001 — Read current rules

- Status: PASS; layer: Live dev; priority: P0.
- Preconditions: Authenticated manager; baseline version 16
- Steps: GET payment-rules and compare all values
- Expected: Retry offsets 24/72h; grace 168h; notices 24/72/120/168h; cutoff 10d
- Observed: Fresh authenticated GET returned HTTP 200 with version-16 settings; actual values retained in live evidence.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: See live check evidence or blocker.

### RET-002 — Pin rules on first failure

- Status: PARTIAL; layer: Unit + Postgres; priority: P1.
- Preconditions: Fresh retryable charge; version 16 active
- Steps: Record first failure at T0; inspect charge row
- Expected: first_failed_at=T0; version 16 and effective deadline pinned once
- Observed: First-failure pinning and default-version DB scheduling passed.
- Remaining: No dev database read proving this new charge is pinned to version 16; version-16 fixtures also exercised locally.
- Executed native evidence: competition-integration::test_a_decline_is_scheduled_and_one_pass_sends_the_retry_and_the_notice [PASS]; competition-unit::test_the_first_decline_starts_the_clock_and_schedules_the_first_retry [PASS]

### RET-003 — Rule change cannot reschedule existing charge

- Status: PASS; layer: Unit; priority: P0.
- Preconditions: Charge already pinned to version 16
- Steps: Change isolated test organisation to version 17; process another failure
- Expected: Original charge retains version 16, T0 and deadline; no revised promise
- Observed: Existing charge retained its first clock and pinned rules when current settings changed in isolated stores.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: competition-unit::test_editing_the_rules_later_cannot_move_a_date_an_athlete_was_given [PASS]

### RET-004 — New charge uses new rule version

- Status: PASS; layer: Unit; priority: P1.
- Preconditions: Isolated organisation has version 17
- Steps: Fail a new independent charge
- Expected: New charge uses version 17; older charge unchanged
- Observed: New charge uses newly saved rules in the application test.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: competition-unit::test_a_charge_that_started_after_the_rules_were_saved_runs_on_them [PASS]

### RET-005 — Repeated failure preserves first-failure clock

- Status: PASS; layer: Unit; priority: P1.
- Preconditions: Failure at T0 already recorded
- Steps: Record failures at T0+25h and T0+73h
- Expected: T0 never moves; grace is not restarted
- Observed: Later declines and manual failure do not restart the first-failure clock.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: competition-unit::test_a_later_decline_keeps_the_first_clock_and_schedules_the_next_retry [PASS]; competition-unit::test_a_manual_retry_that_fails_does_not_restart_the_schedule [PASS]

### RET-006 — Rule version zero defaults

- Status: PASS; layer: Unit + Postgres; priority: P1.
- Preconditions: Isolated organisation has no saved settings
- Steps: Create first failure; read pinned version and defaults
- Expected: Version 0 uses code defaults; do not substitute dev version-16 values
- Observed: Default-version behavior verified; native defaults differ from saved dev version 16.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: competition-integration::test_a_decline_is_scheduled_and_one_pass_sends_the_retry_and_the_notice [PASS]; competition-unit::test_the_defaults_are_what_a_charge_with_no_pinned_version_falls_back_to [PASS]; competition-unit::test_an_organisation_that_never_saved_is_on_the_defaults_at_version_zero [PASS]

### RET-007 — Reject invalid configuration

- Status: PARTIAL; layer: Unit; priority: P1.
- Preconditions: Isolated settings tenant
- Steps: Try duplicate/descending/negative/fractional offsets; retry beyond grace; invalid types and bounds
- Expected: Invalid input rejected with actionable errors and no partial save; exact numeric limits follow schema
- Observed: Ascending schedules, duplicate offsets and retry-after-grace rejection tested.
- Remaining: All numeric schema/type limits and every invalid HTTP payload were not exercised on an isolated dev settings tenant.
- Executed native evidence: competition-unit::test_each_retry_is_later_than_the_one_before[retries0] [PASS]; competition-unit::test_each_retry_is_later_than_the_one_before[retries1] [PASS]; competition-unit::test_each_retry_is_later_than_the_one_before[retries2] [PASS]; competition-unit::test_each_notice_is_later_than_the_one_before[notices0] [PASS]; competition-unit::test_each_notice_is_later_than_the_one_before[notices1] [PASS]; competition-unit::test_a_refused_save_writes_nothing[named0-RetryScheduleError] [PASS]; competition-unit::test_a_refused_save_writes_nothing[named1-NoticeScheduleError] [PASS]; competition-unit::test_a_refused_save_writes_nothing[named2-RetryAfterGraceError] [PASS]; competition-unit::test_a_refused_save_writes_nothing[named3-RetryAfterGraceError] [PASS]

### RET-008 — Zero automatic retries

- Status: PASS; layer: Unit; priority: P1.
- Preconditions: Isolated policy retry list empty
- Steps: Fail a charge and advance all notice boundaries
- Expected: No automatic execute; notices and grace decision follow policy
- Observed: Empty automatic schedule produces no retry and retains notification behavior.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: boundaries::test_zero_retry_policy_still_has_notices [PASS]; competition-unit::test_no_automatic_retry_is_no_retry [PASS]; competition-unit::test_no_automatic_retry_is_valid_with_any_grace_period [PASS]

### RET-009 — Concurrent settings edits

- Status: PARTIAL; layer: Unit; priority: P1.
- Preconditions: Two managers read same settings version
- Steps: Submit different updates using same expected version
- Expected: One wins; stale write rejected; no lost update
- Observed: Lost settings-version race stages no history.
- Remaining: No simultaneous live or real-DB version-16 settings edit was performed.
- Executed native evidence: competition-unit::test_losing_a_race_for_the_next_version_stages_no_history [PASS]

### RET-010 — Settings access control

- Status: PARTIAL; layer: Live dev + Unit; priority: P1.
- Preconditions: Athlete and unauthorised manager sessions
- Steps: Read/edit payment rules
- Expected: Unauthorised operations rejected; no change to shared configuration
- Observed: Athlete read denial tested live; role refusal covered locally.
- Remaining: Manager edit-denial combinations were not all submitted against dev.
- Executed native evidence: competition-unit::test_a_non_hub_role_is_refused [PASS]; competition-unit::test_a_non_hub_role_cannot_promote [PASS]

### RET-011 — Retryable initial decline

- Status: PARTIAL; layer: Postgres + Unit; priority: P0.
- Preconditions: Eligible field entry; retryable provider failure
- Steps: Confirm and charge; consume failure at T0
- Expected: Payment pending; first retry scheduled at T0+24h; correct amount/card/reference
- Observed: Real-DB retryable failure scheduled an execute and notice in a worker pass.
- Remaining: Failure was injected through the application boundary locally; no live Stripe retryable failure/automatic dev worker trace.
- Executed native evidence: competition-integration::test_a_decline_is_scheduled_and_one_pass_sends_the_retry_and_the_notice [PASS]

### RET-012 — Needs-new-method decline

- Status: PARTIAL; layer: Live dev + Postgres; priority: P0.
- Preconditions: Provider returns needs_new_method
- Steps: Consume failure; advance past 24h and 72h
- Expected: No automatic charge on the invalid card; recovery guidance/notices remain
- Observed: Fresh test card genuinely declined; local worker does not automatically charge needs-new-method.
- Remaining: A dev scheduled worker was not time-shifted through every offset for that fixture.
- Executed native evidence: competition-integration::test_a_decline_is_scheduled_and_one_pass_sends_the_retry_and_the_notice [PASS]; competition-unit::test_a_decline_that_needs_a_new_card_is_never_retried_but_is_still_noticed [PASS]

### RET-013 — Authentication-required decline

- Status: PARTIAL; layer: Unit; priority: P0.
- Preconditions: Provider returns action_required
- Steps: Consume failure; tick at all retry boundaries
- Expected: No blind off-session retry; athlete is offered appropriate authentication recovery
- Observed: Off-session action-required execution refused locally.
- Remaining: No actual browser 3DS recovery challenge or dev scheduler trace.
- Executed native evidence: competition-unit::test_a_decline_that_cannot_be_retried_has_no_retry[action_required] [PASS]; competition-unit::test_a_decline_that_cannot_be_retried_has_no_retry[needs_new_method] [PASS]; competition-unit::test_a_decline_that_cannot_be_retried_has_no_retry[None] [PASS]; competition-unit::test_a_decline_that_cannot_be_retried_is_failed_with_nothing_scheduled[action_required] [PASS]; competition-unit::test_a_decline_that_cannot_be_retried_is_failed_with_nothing_scheduled[needs_new_method] [PASS]; competition-unit::test_a_decline_that_cannot_be_retried_is_failed_with_nothing_scheduled[None] [PASS]; payment-unit::test_action_required_is_rejected_never_retried_off_session [PASS]

### RET-014 — Unknown failure class

- Status: PASS; layer: Unit; priority: P1.
- Preconditions: Failure class null or unrecognised
- Steps: Consume failure; run due ticks
- Expected: No automatic retry based on an assumed classification
- Observed: Null and unknown classifications have no automatic schedule.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: boundaries::test_non_retryable_never_scheduled[needs_new_method] [PASS]; boundaries::test_non_retryable_never_scheduled[action_required] [PASS]; boundaries::test_non_retryable_never_scheduled[None] [PASS]; boundaries::test_non_retryable_never_scheduled[unexpected] [PASS]; competition-unit::test_only_a_retryable_decline_is_ever_retried [PASS]

### RET-015 — First payment refusal without attempt

- Status: PASS; layer: Unit + Postgres; priority: P1.
- Preconditions: No usable saved card; no prior failure class
- Steps: Consume attempted=false result
- Expected: Clock starts for notices/escalation; no provider attempt falsely recorded; no auto retry
- Observed: A non-attempt starts recovery clock without pretending a provider attempt occurred.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: competition-integration::test_a_charge_payment_refused_to_attempt_still_starts_the_grace_period [PASS]; competition-unit::test_a_first_refusal_starts_the_clock_and_is_never_retried [PASS]

### RET-016 — Refused retry preserves earlier classification

- Status: PASS; layer: Unit; priority: P1.
- Preconditions: Prior retryable decline then attempted=false
- Steps: Consume refusal and inspect retry state
- Expected: Earlier genuine failure class preserved; counters distinguish refusal from attempted decline
- Observed: Earlier genuine decline classification survives an attempted=false result.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: competition-unit::test_a_refused_retry_keeps_the_class_of_the_decline_before_it [PASS]

### RET-017 — Successful initial payment

- Status: PARTIAL; layer: Unit + Postgres; priority: P0.
- Preconditions: Valid saved test card
- Steps: Confirm and charge; consume success twice
- Expected: One successful charge; eligible entry confirmed; no recovery schedule
- Observed: Payment execution and paid transition passed locally.
- Remaining: Fresh live event scenario began with decline, not an initial successful entry-fee collection; duplicate initial-success event not newly exercised end to end.
- Executed native evidence: payment-integration::test_charge_lifecycle_ready_charging_paid [PASS]; payment-unit::test_happy_path_charges_the_pinned_saved_payment_method [PASS]

### RET-018 — Failure with missing competition charge

- Status: PASS; layer: Unit; priority: P1.
- Preconditions: Unknown entry/reference or unrelated organisation
- Steps: Deliver failure fact
- Expected: No unrelated state changed; diagnostic behavior recorded; no invented charge
- Observed: Missing competition charge causes no invented state or scheduled payment.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: competition-unit::test_a_decline_with_no_charge_row_does_nothing [PASS]

### RET-019 — Duplicate first-failure event

- Status: PARTIAL; layer: Unit; priority: P1.
- Preconditions: Same event delivered twice
- Steps: Consume duplicate with identical event identity
- Expected: T0/policy/deadline unchanged; no duplicate notice/execute/audit effects
- Observed: Pin-once and redelivery safety covered in selected unit tests.
- Remaining: No full first-failure consumer redelivery and real bus/outbox trace for this exact case.
- Executed native evidence: competition-unit::test_the_first_decline_starts_the_clock_and_schedules_the_first_retry [PASS]; payment-unit::test_no_payment_intent_redelivery_safety_does_not_double_announce [PASS]

### RET-020 — Failure after success

- Status: PARTIAL; layer: Unit + Postgres; priority: P0.
- Preconditions: Charge already paid
- Steps: Deliver older failure fact
- Expected: Paid state does not regress; retry not restarted
- Observed: Stale outcomes/illegal terminal transitions rejected locally.
- Remaining: No live provider paid-then-stale-failure delivery sequence.
- Executed native evidence: payment-integration::test_apply_charge_outcome_drops_a_stale_redelivery [PASS]; payment-unit::test_terminal_states_refuse_every_further_transition[ready-paid] [PASS]; payment-unit::test_terminal_states_refuse_every_further_transition[ready-released] [PASS]; payment-unit::test_terminal_states_refuse_every_further_transition[charging-paid] [PASS]; payment-unit::test_terminal_states_refuse_every_further_transition[charging-released] [PASS]; payment-unit::test_terminal_states_refuse_every_further_transition[retryable-paid] [PASS]; payment-unit::test_terminal_states_refuse_every_further_transition[retryable-released] [PASS]; payment-unit::test_watermark_refuses_a_real_change_at_or_before_the_watermark [PASS]

### RET-021 — First due boundary

- Status: PASS; layer: Unit / explicit version 16; priority: P0.
- Preconditions: Retryable charge scheduled for T0+24h
- Steps: Tick at due minus 1ms, exactly due, due plus 1ms on separate fixtures
- Expected: No early dispatch; one dispatch at due; later duplicate tick cannot repeat it
- Observed: At due minus 1ms no dispatch; exactly due and plus 1ms dispatch once; subsequent tick does not repeat.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: lifecycle::test_matrix_worker_dispatch_exact_due_boundaries[-1-24] [PASS]; lifecycle::test_matrix_worker_dispatch_exact_due_boundaries[-1-72] [PASS]; lifecycle::test_matrix_worker_dispatch_exact_due_boundaries[0-24] [PASS]; lifecycle::test_matrix_worker_dispatch_exact_due_boundaries[0-72] [PASS]; lifecycle::test_matrix_worker_dispatch_exact_due_boundaries[1-24] [PASS]; lifecycle::test_matrix_worker_dispatch_exact_due_boundaries[1-72] [PASS]

### RET-022 — Second due boundary

- Status: PASS; layer: Unit / explicit version 16; priority: P0.
- Preconditions: First retry failed; second scheduled at T0+72h
- Steps: Tick at due minus 1ms, due, due plus 1ms
- Expected: No early second attempt; one at due; first-failure anchor retained
- Observed: At due minus 1ms no dispatch; exactly due and plus 1ms dispatch once; subsequent tick does not repeat.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: lifecycle::test_matrix_worker_dispatch_exact_due_boundaries[-1-24] [PASS]; lifecycle::test_matrix_worker_dispatch_exact_due_boundaries[-1-72] [PASS]; lifecycle::test_matrix_worker_dispatch_exact_due_boundaries[0-24] [PASS]; lifecycle::test_matrix_worker_dispatch_exact_due_boundaries[0-72] [PASS]; lifecycle::test_matrix_worker_dispatch_exact_due_boundaries[1-24] [PASS]; lifecycle::test_matrix_worker_dispatch_exact_due_boundaries[1-72] [PASS]

### RET-023 — 72 hours is not relative to first retry

- Status: PASS; layer: Unit; priority: P0.
- Preconditions: First attempt ran late at T0+25h
- Steps: Process its failure and inspect next due
- Expected: Second due stays T0+72h, not T0+97h
- Observed: Next retry remains anchored to original failure rather than previous retry time.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: competition-unit::test_each_retry_is_counted_from_the_first_failure_not_the_last[0-0-24] [PASS]; competition-unit::test_each_retry_is_counted_from_the_first_failure_not_the_last[25-1-72] [PASS]; competition-unit::test_each_retry_is_counted_from_the_first_failure_not_the_last[73-2-168] [PASS]; competition-unit::test_each_retry_is_counted_from_the_first_failure_not_the_last[24-0-24] [PASS]; competition-unit::test_each_retry_is_counted_from_the_first_failure_not_the_last[72-1-72] [PASS]; competition-unit::test_a_later_decline_keeps_the_first_clock_and_schedules_the_next_retry [PASS]

### RET-024 — Retry attempts exhausted

- Status: PASS; layer: Unit / explicit version 16; priority: P0.
- Preconditions: Two configured automatic attempts sent and failed
- Steps: Advance beyond 72h while before grace end
- Expected: No third automatic attempt; no implied retry at 168h
- Observed: After failures of the 24h and 72h attempts, no third automatic retry is scheduled.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: lifecycle::test_matrix_no_third_retry_under_version16 [PASS]

### RET-025 — Manual retry does not consume automatic index incorrectly

- Status: PARTIAL; layer: Unit; priority: P1.
- Preconditions: Manual retry before 24h fails
- Steps: Inspect retries_sent and next due
- Expected: Manual and automatic attempts distinguished; configured automatic count not silently consumed
- Observed: Manual failure does not reset schedule or create a burst.
- Remaining: Exact end-to-end manual versus automatic counter accounting was not independently queried in dev DB.
- Executed native evidence: competition-unit::test_a_manual_retry_that_fails_does_not_restart_the_schedule [PASS]; competition-unit::test_a_failed_manual_retry_is_not_followed_by_a_burst_of_automatic_ones [PASS]

### RET-026 — Late manual decline skips old due times

- Status: PASS; layer: Unit; priority: P1.
- Preconditions: Manual retry fails at T0+50h
- Steps: Calculate next due
- Expected: Next retry 72h; no immediate replay of missed 24h attempt
- Observed: Past offsets skipped; exhausted configured schedule produces no future retry.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: competition-unit::test_a_retry_whose_time_has_passed_is_skipped_not_sent_at_once[100-168] [PASS]; competition-unit::test_a_retry_whose_time_has_passed_is_skipped_not_sent_at_once[30-72] [PASS]; competition-unit::test_a_retry_whose_time_has_passed_is_skipped_not_sent_at_once[73-168] [PASS]; competition-unit::test_when_every_retry_in_the_rules_has_passed_there_is_none [PASS]; lifecycle::test_matrix_no_third_retry_under_version16 [PASS]

### RET-027 — Failure after final offset

- Status: PASS; layer: Unit; priority: P1.
- Preconditions: Manual failure at T0+100h
- Steps: Recalculate automatic due
- Expected: No remaining automatic due; no burst of backdated attempts
- Observed: Past offsets skipped; exhausted configured schedule produces no future retry.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: competition-unit::test_a_retry_whose_time_has_passed_is_skipped_not_sent_at_once[100-168] [PASS]; competition-unit::test_a_retry_whose_time_has_passed_is_skipped_not_sent_at_once[30-72] [PASS]; competition-unit::test_a_retry_whose_time_has_passed_is_skipped_not_sent_at_once[73-168] [PASS]; competition-unit::test_when_every_retry_in_the_rules_has_passed_there_is_none [PASS]; lifecycle::test_matrix_no_third_retry_under_version16 [PASS]

### RET-028 — Exact-due rescheduling cannot create duplicate attempt

- Status: FAIL; layer: Unit / exact boundary; priority: P0.
- Preconditions: Failure/replay lands exactly on configured offset
- Steps: Recalculate due and tick repeatedly
- Expected: At most one logical attempt for that offset; no loop at the same timestamp
- Observed: With retries_sent=1 and now exactly T0+24h, next_retry_at selected 24h again instead of 72h.
- Remaining: Provider duplicate capture not demonstrated; failed scheduling acceptance assertion is retained.
- Executed native evidence: boundaries::test_completed_retry_offset_is_not_rescheduled_at_same_instant [FAIL]

### RET-029 — Different attempt keys, same charge reference

- Status: PASS; layer: Unit + Postgres; priority: P1.
- Preconditions: Two legitimate scheduled attempts
- Steps: Inspect execute commands
- Expected: Keys retry-{chargeId}-1 and retry-{chargeId}-2; same original entry reference
- Observed: Scheduled commands use per-attempt keys with unchanged entry reference.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: competition-integration::test_a_decline_is_scheduled_and_one_pass_sends_the_retry_and_the_notice [PASS]; competition-unit::test_each_attempt_has_its_own_request_id_so_payment_treats_it_as_new [PASS]

### RET-030 — Fresh missing timer fields

- Status: PARTIAL; layer: Unit; priority: P1.
- Preconditions: Legacy/incomplete charge lacks first_failed_at or due
- Steps: Run retry worker
- Expected: No accidental charge; explicit skip/recovery behavior; no whole-pass crash
- Observed: Missing first-failure timestamp caused no dispatch.
- Remaining: All legacy/missing-due combinations and operational diagnostic paths not enumerated.
- Executed native evidence: lifecycle::test_matrix_no_first_failure_timestamp_does_not_dispatch [PASS]

### RET-031 — Event start unavailable

- Status: PASS; layer: Unit; priority: P1.
- Preconditions: Retryable charge with no event start
- Steps: Pin deadline
- Expected: Deadline=T0+168h; graceful fallback recorded
- Observed: Missing event-start timestamp falls back to the grace deadline.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: boundaries::test_no_event_start_uses_grace [PASS]

### RET-032 — Amount and currency cannot drift

- Status: PASS; layer: Unit + Postgres; priority: P0.
- Preconditions: Entry amount/card agreement established
- Steps: Change unrelated prices; run retries
- Expected: Charge uses agreed stored amount/currency; no new tax/fee calculation without explicit re-agreement
- Observed: Agreed fee and pinned saved method remain authoritative; mismatched re-create rejected.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: competition-unit::test_each_charge_records_what_that_member_agreed_to_not_what_the_event_says_now [PASS]; payment-integration::test_create_or_none_stores_the_agreed_amount [PASS]; payment-unit::test_execute_charges_the_pinned_method_not_a_newer_active_one [PASS]

### RET-033 — Seven-day deadline

- Status: PASS; layer: Unit / explicit version 16; priority: P0.
- Preconditions: Event sufficiently far away
- Steps: Tick at T0+168h minus 1ms, exactly 168h, plus 1ms
- Expected: Before deadline no premature expiry; at deadline escalate if no in-flight attempt; do not auto-withdraw
- Observed: At 168h minus 1ms no flag; at/after deadline flag when no valid in-flight answer window.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: lifecycle::test_matrix_deadline_boundary_without_inflight[-1] [PASS]; lifecycle::test_matrix_deadline_boundary_without_inflight[0] [PASS]; lifecycle::test_matrix_deadline_boundary_without_inflight[1] [PASS]

### RET-034 — Event cutoff wins

- Status: PARTIAL; layer: Unit + Postgres; priority: P0.
- Preconditions: Event cutoff=T0+48h
- Steps: Fail at T0 and tick at 24h/48h/72h
- Expected: 24h retry eligible; 72h retry not scheduled; escalate at 48h
- Observed: Shortened deadline calculation and worker cutoff behavior passed.
- Remaining: Native DB seed-policy test uses default nine-day setting; explicit 10-day cutoff arithmetic verified locally, not full live 48h sequence.
- Executed native evidence: boundaries::test_effective_deadline_around_cutoff[-1] [PASS]; boundaries::test_effective_deadline_around_cutoff[0] [PASS]; boundaries::test_effective_deadline_around_cutoff[1] [PASS]; boundaries::test_effective_deadline_around_cutoff[48] [PASS]; boundaries::test_effective_deadline_around_cutoff[168] [PASS]; boundaries::test_effective_deadline_around_cutoff[240] [PASS]; competition-integration::test_the_deadline_is_nine_days_before_the_event_when_that_comes_first [PASS]; competition-unit::test_the_deadline_is_nine_days_before_the_event_when_that_comes_first [PASS]; competition-unit::test_a_notice_after_the_deadline_is_not_sent_but_the_flag_is [PASS]

### RET-035 — Grace deadline wins

- Status: PASS; layer: Unit; priority: P1.
- Preconditions: Event cutoff later than T0+168h
- Steps: Pin deadline
- Expected: Use seven-day grace, not later event cutoff
- Observed: Deadline equals the earlier of grace and event cutoff, including equality.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: boundaries::test_effective_deadline_around_cutoff[-1] [PASS]; boundaries::test_effective_deadline_around_cutoff[0] [PASS]; boundaries::test_effective_deadline_around_cutoff[1] [PASS]; boundaries::test_effective_deadline_around_cutoff[48] [PASS]; boundaries::test_effective_deadline_around_cutoff[168] [PASS]; boundaries::test_effective_deadline_around_cutoff[240] [PASS]

### RET-036 — Cutoff and grace equal

- Status: PASS; layer: Unit; priority: P1.
- Preconditions: Event cutoff exactly T0+168h
- Steps: Pin deadline and tick boundary
- Expected: One effective deadline; no duplicate escalation
- Observed: Deadline equals the earlier of grace and event cutoff, including equality.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: boundaries::test_effective_deadline_around_cutoff[-1] [PASS]; boundaries::test_effective_deadline_around_cutoff[0] [PASS]; boundaries::test_effective_deadline_around_cutoff[1] [PASS]; boundaries::test_effective_deadline_around_cutoff[48] [PASS]; boundaries::test_effective_deadline_around_cutoff[168] [PASS]; boundaries::test_effective_deadline_around_cutoff[240] [PASS]

### RET-037 — Failure inside short-notice window

- Status: PARTIAL; layer: Unit + Postgres; priority: P0.
- Preconditions: T0 is later than event minus 10 days
- Steps: Record failure then worker tick
- Expected: No automatic retry; escalate on processing without granting fresh seven days
- Observed: Failure inside short-notice window flags rather than creates automatic retries.
- Remaining: Native integration uses code-default nine days, not an altered dev ten-day clock.
- Executed native evidence: competition-integration::test_a_payment_failing_inside_the_last_nine_days_is_flagged_at_once [PASS]; competition-unit::test_a_payment_failing_inside_the_window_has_a_deadline_already_past [PASS]; competition-unit::test_a_payment_failing_inside_the_window_is_flagged_at_once_and_never_retried [PASS]

### RET-038 — Failure exactly at event cutoff

- Status: PARTIAL; layer: Unit; priority: P0.
- Preconditions: T0 equals event minus 10 days
- Steps: Record failure then tick at same instant
- Expected: No future retry; escalation is due immediately
- Observed: Past/equal/imminent cutoff arithmetic covered, including negative remaining time.
- Remaining: Not all exact first-failure worker invocations at ±1ms and already-started event variants have a complete live/DB execution.
- Executed native evidence: boundaries::test_effective_deadline_around_cutoff[-1] [PASS]; boundaries::test_effective_deadline_around_cutoff[0] [PASS]; boundaries::test_effective_deadline_around_cutoff[1] [PASS]; boundaries::test_effective_deadline_around_cutoff[48] [PASS]; boundaries::test_effective_deadline_around_cutoff[168] [PASS]; boundaries::test_effective_deadline_around_cutoff[240] [PASS]; competition-integration::test_a_payment_failing_inside_the_last_nine_days_is_flagged_at_once [PASS]; competition-unit::test_a_payment_failing_inside_the_window_has_a_deadline_already_past [PASS]; competition-unit::test_a_payment_failing_inside_the_window_is_flagged_at_once_and_never_retried [PASS]

### RET-039 — Failure one instant before cutoff

- Status: PARTIAL; layer: Unit; priority: P1.
- Preconditions: Cutoff=T0+1ms
- Steps: Record failure; tick before/at/after cutoff
- Expected: No retry that cannot fit; exact escalation boundary respected
- Observed: Past/equal/imminent cutoff arithmetic covered, including negative remaining time.
- Remaining: Not all exact first-failure worker invocations at ±1ms and already-started event variants have a complete live/DB execution.
- Executed native evidence: boundaries::test_effective_deadline_around_cutoff[-1] [PASS]; boundaries::test_effective_deadline_around_cutoff[0] [PASS]; boundaries::test_effective_deadline_around_cutoff[1] [PASS]; boundaries::test_effective_deadline_around_cutoff[48] [PASS]; boundaries::test_effective_deadline_around_cutoff[168] [PASS]; boundaries::test_effective_deadline_around_cutoff[240] [PASS]; competition-integration::test_a_payment_failing_inside_the_last_nine_days_is_flagged_at_once [PASS]; competition-unit::test_a_payment_failing_inside_the_window_has_a_deadline_already_past [PASS]; competition-unit::test_a_payment_failing_inside_the_window_is_flagged_at_once_and_never_retried [PASS]

### RET-040 — Event today or already started

- Status: PARTIAL; layer: Unit; priority: P1.
- Preconditions: Failure after cutoff and event-start boundary
- Steps: Record decline and run worker
- Expected: No automatic recovery chase extending into event; TM action required
- Observed: Past/equal/imminent cutoff arithmetic covered, including negative remaining time.
- Remaining: Not all exact first-failure worker invocations at ±1ms and already-started event variants have a complete live/DB execution.
- Executed native evidence: boundaries::test_effective_deadline_around_cutoff[-1] [PASS]; boundaries::test_effective_deadline_around_cutoff[0] [PASS]; boundaries::test_effective_deadline_around_cutoff[1] [PASS]; boundaries::test_effective_deadline_around_cutoff[48] [PASS]; boundaries::test_effective_deadline_around_cutoff[168] [PASS]; boundaries::test_effective_deadline_around_cutoff[240] [PASS]; competition-integration::test_a_payment_failing_inside_the_last_nine_days_is_flagged_at_once [PASS]; competition-unit::test_a_payment_failing_inside_the_window_has_a_deadline_already_past [PASS]; competition-unit::test_a_payment_failing_inside_the_window_is_flagged_at_once_and_never_retried [PASS]

### RET-041 — Retry exactly at cutoff

- Status: REVIEW; layer: Unit / observed current code; priority: P0.
- Preconditions: Isolated policy permits due==effective deadline
- Steps: Tick at that instant
- Expected: Current code permits due retry before flag; confirm whether Product accepts this against strict cutoff wording
- Observed: Current worker dispatches the due retry at the effective cutoff.
- Remaining: DEC-02: Product must approve exact-cutoff retry before acceptance verdict.
- Executed native evidence: lifecycle::test_matrix_retry_exactly_at_cutoff_current_code [PASS]

### RET-042 — Late tick versus strict cutoff

- Status: REVIEW; layer: Unit / observed current code; priority: P0.
- Preconditions: Due retry before deadline; worker wakes after cutoff but within 24h tolerance
- Steps: Tick and inspect dispatch
- Expected: Code can dispatch a previously scheduled retry after deadline; decide strict stop requirement before sign-off
- Observed: A previously scheduled retry can dispatch at hour 25 when event cutoff was hour 24.
- Remaining: DEC-01: bounded late dispatch conflicts with a strictly interpreted event cutoff.
- Executed native evidence: lifecycle::test_matrix_due_retry_after_cutoff_within_late_window_current_code [PASS]

### RET-043 — UTC midnight versus venue midnight

- Status: REVIEW; layer: Unit / observed current code; priority: P1.
- Preconditions: Same date at UTC-10 and UTC+14 venues
- Steps: Compare event cutoff timestamps
- Expected: Current code uses UTC date midnight; confirm business timezone requirement and any hour-level discrepancy
- Observed: Event start for retry cutoff is UTC date midnight.
- Remaining: DEC-03: venue-local versus UTC policy needs confirmation.
- Executed native evidence: boundaries::test_current_utc_event_midnight_is_explicit [PASS]

### RET-044 — DST/leap-day/year rollover

- Status: PASS; layer: Unit; priority: P1.
- Preconditions: T0 near DST change, Feb 29 or Dec 31
- Steps: Advance elapsed 24/72/168 hours
- Expected: No duplicated/skipped offsets from local clock changes; exact UTC elapsed durations
- Observed: UTC elapsed-duration offsets held across DST season, leap day and year end samples.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: boundaries::test_dst_leap_year_and_year_rollover_elapsed_offsets[start0] [PASS]; boundaries::test_dst_leap_year_and_year_rollover_elapsed_offsets[start1] [PASS]; boundaries::test_dst_leap_year_and_year_rollover_elapsed_offsets[start2] [PASS]

### RET-045 — All four notice boundaries

- Status: PASS; layer: Unit; priority: P1.
- Preconditions: Unpaid eligible entry; no prior notices
- Steps: Parameterise N=24/72/120/168h; tick N-1ms/N/N+1ms
- Expected: Each due notice once; none early; repeated tick does not duplicate
- Observed: All four notification thresholds tested at ±1ms and exact time; repeat notice suppression covered.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: boundaries::test_notice_exact_boundary[-1-24] [PASS]; boundaries::test_notice_exact_boundary[-1-72] [PASS]; boundaries::test_notice_exact_boundary[0-24] [PASS]; boundaries::test_notice_exact_boundary[0-72] [PASS]; boundaries::test_notice_exact_boundary[1-24] [PASS]; boundaries::test_notice_exact_boundary[1-72] [PASS]; boundaries::test_late_notice_exact_boundary[-1-120-3] [PASS]; boundaries::test_late_notice_exact_boundary[-1-168-4] [PASS]; boundaries::test_late_notice_exact_boundary[0-120-3] [PASS]; boundaries::test_late_notice_exact_boundary[0-168-4] [PASS]; boundaries::test_late_notice_exact_boundary[1-120-3] [PASS]; boundaries::test_late_notice_exact_boundary[1-168-4] [PASS]; competition-unit::test_each_notice_is_sent_once [PASS]

### RET-046 — Non-retryable card still notified

- Status: PASS; layer: Unit + Postgres; priority: P1.
- Preconditions: Needs-new-method or action-required failure
- Steps: Advance notice boundaries before deadline
- Expected: Actionable recovery notices sent without automatic off-session attempts
- Observed: Non-retryable card remained unscheduled while notice was staged.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: competition-integration::test_a_decline_is_scheduled_and_one_pass_sends_the_retry_and_the_notice [PASS]; competition-unit::test_a_decline_that_needs_a_new_card_is_never_retried_but_is_still_noticed [PASS]

### RET-047 — Latest overdue notice only

- Status: PASS; layer: Unit + Postgres; priority: P1.
- Preconditions: Worker down from T0 until hour 130
- Steps: Resume before deadline
- Expected: Send latest due notice, not a burst of day-1/day-3/day-5 messages
- Observed: Only latest overdue notice staged; no burst of every missed reminder.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: competition-integration::test_when_the_grace_period_ends_the_entry_is_flagged_once [PASS]; competition-unit::test_after_a_stretch_with_the_job_down_the_athlete_is_told_once_where_they_are_now [PASS]; competition-unit::test_after_a_stretch_with_the_job_down_only_the_latest_notice_goes [PASS]

### RET-048 — Notice after shortened deadline

- Status: PASS; layer: Unit + Postgres; priority: P1.
- Preconditions: Effective deadline 48h
- Steps: Tick at hours 72/120/168
- Expected: No notice whose scheduled offset is beyond deadline; escalation handled once
- Observed: No notice scheduled beyond shortened cutoff is emitted.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: competition-unit::test_a_notice_that_would_fall_after_the_deadline_is_never_sent [PASS]; competition-unit::test_a_notice_after_the_deadline_is_not_sent_but_the_flag_is [PASS]

### RET-049 — Success suppresses later notices

- Status: PARTIAL; layer: Unit; priority: P1.
- Preconditions: Payment succeeds before next notice
- Steps: Advance all later boundaries
- Expected: No further retry/reminder/escalation for settled charge
- Observed: Paid state and confirmation transition covered.
- Remaining: No complete post-success scheduler + live inbox sweep through all later reminders.
- Executed native evidence: competition-unit::test_paid_confirms_an_entry_that_was_charging [PASS]; payment-unit::test_terminal_states_refuse_every_further_transition[ready-paid] [PASS]; payment-unit::test_terminal_states_refuse_every_further_transition[ready-released] [PASS]; payment-unit::test_terminal_states_refuse_every_further_transition[charging-paid] [PASS]; payment-unit::test_terminal_states_refuse_every_further_transition[charging-released] [PASS]; payment-unit::test_terminal_states_refuse_every_further_transition[retryable-paid] [PASS]; payment-unit::test_terminal_states_refuse_every_further_transition[retryable-released] [PASS]

### RET-050 — Withdrawal suppresses recovery notices

- Status: PASS; layer: Unit + Postgres; priority: P1.
- Preconditions: Entry withdrawn before next notice
- Steps: Advance due boundaries
- Expected: Removed athlete no longer chased for entry payment
- Observed: Withdrawal/terminal state stops pending worker dispatch and notifications.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: competition-integration::test_an_entry_that_lost_its_place_is_not_chased [PASS]; lifecycle::test_matrix_terminal_entry_stops_scheduled_retry_and_notices[withdrawn] [PASS]; lifecycle::test_matrix_terminal_entry_stops_scheduled_retry_and_notices[removed] [PASS]; lifecycle::test_matrix_terminal_entry_stops_scheduled_retry_and_notices[not_selected] [PASS]; lifecycle::test_matrix_terminal_entry_stops_scheduled_retry_and_notices[expired] [PASS]

### RET-051 — Flag is idempotent

- Status: PASS; layer: Unit + Postgres; priority: P1.
- Preconditions: Expired unpaid entry already flagged
- Steps: Repeat worker ticks/replayed failure
- Expected: No duplicate TM action-required escalation; no new automatic schedule
- Observed: Repeated passes do not re-escalate flagged recovery.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: competition-integration::test_when_the_grace_period_ends_the_entry_is_flagged_once [PASS]; competition-unit::test_a_flagged_entry_is_not_worked_again [PASS]

### RET-052 — Grace expiry does not auto-promote

- Status: PARTIAL; layer: Unit + Postgres; priority: P1.
- Preconditions: Unpaid entry reaches deadline
- Steps: Run worker and inspect roster/alternates
- Expected: Flag for manager decision; no implied withdrawal or alternate promotion
- Observed: Expiry stages notice/escalation; no auto-withdrawal in exercised worker.
- Remaining: No full-field live UI at grace expiry to demonstrate alternate roster unchanged.
- Executed native evidence: competition-integration::test_when_the_grace_period_ends_the_entry_is_flagged_once [PASS]

### RET-053 — Correct notice payload and recipient

- Status: PARTIAL; layer: Unit + Postgres; priority: P1.
- Preconditions: Different athlete and account-holder/guardian identities
- Steps: Inspect staged notification and actual test inbox
- Expected: Correct account holder, athlete/event, deadline, next retry and recovery action; no cross-account disclosure
- Observed: Event, amount and recovery notification payload tested.
- Remaining: No actual inbox delivery, guardian-recipient matrix or cross-account email verification in this run.
- Executed native evidence: competition-integration::test_a_notice_carries_the_event_s_name_and_the_amount [PASS]; competition-unit::test_a_notice_is_published_when_due_with_what_an_email_can_say [PASS]

### RET-054 — Notification delivery failure

- Status: BLOCKED; layer: Not executed; priority: P1.
- Preconditions: Notification service unavailable or redelivery
- Steps: Fail/retry delivery
- Expected: No duplicate payment; delivery retry is distinguished from business payment retry
- Observed: Notification delivery-outage test not run.
- Remaining: Requires isolated notification delivery transport, fault injection and test-inbox evidence.
- Executed native evidence: See live check evidence or blocker.

### RET-055 — Stale pending notice after success

- Status: REVIEW; layer: Not executed; priority: P1.
- Preconditions: Notice queued; payment settles before delivery
- Steps: Deliver queued message
- Expected: Define suppress/reword policy; do not claim unpaid without checking approved delivery semantics
- Observed: No queued-notice-after-payment experiment.
- Remaining: DEC-04: suppression/rewording policy required before verdict.
- Executed native evidence: See live check evidence or blocker.

### RET-056 — Valid replacement after needs-new-method

- Status: PASS; layer: Live dev + Unit; priority: P0.
- Preconditions: Declined entry; second active test card owned by account
- Steps: Update that entry to valid card
- Expected: Card repointed; immediate retry allowed; one successful payment; correct entry becomes confirmed
- Observed: Fresh live decline recovered with valid saved Visa: HTTP 202; payment Collected; entry Confirmed; real test-mode webhook history recorded.
- Remaining: No independent Stripe API lookup of PaymentIntent; success evidenced by application readback/history.
- Executed native evidence: payment-unit::test_should_retry_now_triggers_run_execute_with_a_derived_request_id [PASS]

### RET-057 — Valid replacement after retryable failure

- Status: PARTIAL; layer: Unit; priority: P0.
- Preconditions: Retryable entry scheduled for future retry
- Steps: Change to valid card before next due
- Expected: Immediate recovery; later schedule cannot charge again after success
- Observed: Retryable-status explicit card update triggers execute in application/handler tests.
- Remaining: Fresh live decline was needs-new-method, not retryable.
- Executed native evidence: payment-unit::test_should_retry_now_matches_retry_immediately_constant[action_required] [PASS]; payment-unit::test_should_retry_now_matches_retry_immediately_constant[awaiting_saved_payment_method] [PASS]; payment-unit::test_should_retry_now_matches_retry_immediately_constant[needs_new_method] [PASS]; payment-unit::test_should_retry_now_matches_retry_immediately_constant[ready] [PASS]; payment-unit::test_should_retry_now_matches_retry_immediately_constant[retryable] [PASS]; payment-unit::test_should_retry_now_triggers_run_execute_with_a_derived_request_id [PASS]

### RET-058 — Same update replayed

- Status: PARTIAL; layer: Live dev + Unit; priority: P0.
- Preconditions: Valid card update with same request identity
- Steps: Replay concurrently and sequentially
- Expected: One logical update/attempt; no duplicate successful capture
- Observed: Same card-change request key replayed; one success recorded in history.
- Remaining: Provider-side attempt count not independently queried.
- Executed native evidence: payment-unit::test_repoint_retry_request_id_is_stable_across_redelivery [PASS]

### RET-059 — Same-card repoint in retryable state

- Status: PASS; layer: Unit + Postgres; priority: P1.
- Preconditions: Active same card, retryable charge
- Steps: Submit explicit update naming same card
- Expected: Observe documented immediate retry behavior; no hidden customer-wide sweep
- Observed: Same-card repoint and immediate-retry decision tested locally.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: payment-integration::test_repoint_saved_payment_method_to_the_same_id_is_a_no_op [PASS]; payment-unit::test_should_retry_now_matches_retry_immediately_constant[action_required] [PASS]; payment-unit::test_should_retry_now_matches_retry_immediately_constant[awaiting_saved_payment_method] [PASS]; payment-unit::test_should_retry_now_matches_retry_immediately_constant[needs_new_method] [PASS]; payment-unit::test_should_retry_now_matches_retry_immediately_constant[ready] [PASS]; payment-unit::test_should_retry_now_matches_retry_immediately_constant[retryable] [PASS]

### RET-060 — Foreign or inactive saved card

- Status: PARTIAL; layer: Live dev + Unit; priority: P0.
- Preconditions: Card belongs to other account or is inactive
- Steps: POST entry-card change
- Expected: Reject; original agreement unchanged; no foreign-card charge
- Observed: Unknown-card UUID rejected live; foreign/non-active ownership cases covered in unit tests.
- Remaining: No live second-account card attack.
- Executed native evidence: payment-unit::test_repoint_rejected_for_a_saved_payment_method_of_another_customer [PASS]; payment-unit::test_repoint_rejected_for_a_non_active_saved_payment_method[pending] [PASS]; payment-unit::test_repoint_rejected_for_a_non_active_saved_payment_method[invalidated] [PASS]

### RET-061 — Change card on unrelated entry

- Status: PARTIAL; layer: Unit; priority: P0.
- Preconditions: Two entries with different selected cards
- Steps: Update card for entry A
- Expected: Entry B remains pinned to its own card; no account-wide retry fan-out
- Observed: Pinned-card selection is charge-specific in tests.
- Remaining: Two simultaneous live entries and customer-wide fan-out were not newly exercised.
- Executed native evidence: payment-unit::test_execute_charges_the_pinned_method_not_a_newer_active_one [PASS]

### RET-062 — Authentication-required recovery

- Status: BLOCKED; layer: Not executed; priority: P1.
- Preconditions: Card requires customer authentication
- Steps: Complete/fail/cancel authentication in test flow
- Expected: Only authenticated eligible charge succeeds; safe actionable state on failure/cancel
- Observed: Real browser authentication challenge/cancel recovery was not run.
- Remaining: Requires controlled 3DS card setup and hosted challenge-flow fixture.
- Executed native evidence: See live check evidence or blocker.

### RET-063 — Card update during processing

- Status: PASS; layer: Unit + Postgres; priority: P1.
- Preconditions: Charge CHARGING
- Steps: Submit card update while attempt is active
- Expected: Do not silently move an in-flight attempt to another card; preserve outcome attribution
- Observed: Card replacement/execute cannot override an already-charging state in tested payment layer.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: payment-unit::test_charge_already_charging_is_rejected_without_a_second_gateway_call [PASS]; payment-unit::test_repoint_rejected_for_paid_released_or_charging[paid] [PASS]; payment-unit::test_repoint_rejected_for_paid_released_or_charging[released] [PASS]; payment-unit::test_repoint_rejected_for_paid_released_or_charging[charging] [PASS]

### RET-064 — Card update races scheduled retry

- Status: PARTIAL; layer: Unit; priority: P0.
- Preconditions: Due scheduled attempt and card update start together
- Steps: Force both orderings using barriers
- Expected: One permitted in-flight attempt at a time; exact card/amount known; no duplicate collection
- Observed: Payment in-flight gating and locked confirmation claim covered.
- Remaining: No controlled card-update-versus-scheduled-worker race with provider request barriers.
- Executed native evidence: payment-unit::test_charge_already_charging_is_rejected_without_a_second_gateway_call [PASS]; payment-unit::test_claim_charge_for_confirmation_locks_the_saved_payment_method [PASS]

### RET-065 — Card update after success or release

- Status: PARTIAL; layer: Live dev + Unit + Postgres; priority: P0.
- Preconditions: Charge paid/released
- Steps: Try repoint and retry
- Expected: No new collection; operation rejected or safe no-op per contract
- Observed: Paid retry rejected live; paid/released card-change gates tested locally.
- Remaining: All live card-change-after-release variants not run.
- Executed native evidence: payment-unit::test_terminal_status_is_rejected[paid] [PASS]; payment-unit::test_terminal_status_is_rejected[released] [PASS]; payment-unit::test_repoint_rejected_for_paid_released_or_charging[paid] [PASS]; payment-unit::test_repoint_rejected_for_paid_released_or_charging[released] [PASS]; payment-unit::test_repoint_rejected_for_paid_released_or_charging[charging] [PASS]

### RET-066 — Withdrawal before due

- Status: PASS; layer: Unit + Postgres; priority: P0.
- Preconditions: Unpaid entry with retry scheduled tomorrow
- Steps: Withdraw then advance past all due times
- Expected: Entry withdrawn; charges/retry eligibility cancelled; no execute or reminders
- Observed: Scheduled charge stopped after withdrawal in real DB worker tests.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: alternate-db::test_declined_withdrawal_alternate_promotion_stops_old_scheduled_retry [PASS]; competition-integration::test_an_entry_that_lost_its_place_is_not_chased [PASS]

### RET-067 — Immediate retry after withdrawal with FAILED row

- Status: FAIL; layer: Postgres + Unit; priority: P0.
- Preconditions: FAILED unpaid entry; no scheduled retry
- Steps: Withdraw then direct POST retry immediately
- Expected: Reject at backend regardless of UI actions; no execute command; regression for observed gap
- Observed: Repository-only withdrawal left FAILED eligibility; manual prepare returned chargeable=true and staged execute.
- Remaining: This bypassed the application withdrawal orchestration that cancels eligibility. It proves a missing defensive lifecycle guard, not that normal withdrawal always keeps retrying; the complete application withdrawal/alternate worker test passed.
- Executed native evidence: lifecycle::test_matrix_terminal_entry_must_not_prepare_manual_retry[withdrawn] [FAIL]; lifecycle::test_matrix_terminal_entry_must_not_prepare_manual_retry[removed] [FAIL]; lifecycle::test_matrix_terminal_entry_must_not_prepare_manual_retry[not_selected] [FAIL]; lifecycle::test_matrix_terminal_entry_must_not_prepare_manual_retry[expired] [FAIL]; regressions-db::test_withdrawal_blocks_manual_retry_of_failed_charge [FAIL]

### RET-068 — Retry after settled withdrawal

- Status: PARTIAL; layer: Live dev; priority: P0.
- Preconditions: Withdrawn entry already reconciled
- Steps: POST retry with new and old idempotency keys
- Expected: No fresh attempt; replay cannot revive payment eligibility
- Observed: Both previously withdrawn fixtures returned 409 on fresh retry requests in current run.
- Remaining: Old-key replay after withdrawal and every terminal lifecycle point were not covered.
- Executed native evidence: See live check evidence or blocker.

### RET-069 — Withdrawal during queued dispatch

- Status: PARTIAL; layer: Unit + Postgres; priority: P0.
- Preconditions: Execute staged but not consumed
- Steps: Withdraw before consumer runs; test both message orders
- Expected: Release/cancellation prevents unnecessary new charge; explicit handling if execute already won
- Observed: Release staging and in-flight refusal verified.
- Remaining: No broker-level execute/release reordering barrier experiment.
- Executed native evidence: competition-unit::test_withdrawing_stages_a_release_even_with_no_open_charge [PASS]; payment-integration::test_release_refused_while_charging [PASS]

### RET-070 — Withdrawal during provider processing

- Status: PARTIAL; layer: Unit + Postgres; priority: P0.
- Preconditions: Payment CHARGING
- Steps: Withdraw while provider response/webhook is held
- Expected: Track cancellation requested; keep withdrawn; reconcile success/failure and expose required Finance action
- Observed: CHARGING release refused; separate late-success reconciliation acceptance test failed.
- Remaining: Provider-held live attempt and cancellation-request tracking not demonstrated end to end.
- Executed native evidence: payment-unit::test_release_rejected_while_charging_with_a_distinct_reason [PASS]; regressions-db::test_late_success_is_not_lost_after_withdrawal_cancels_requested_charge [FAIL]

### RET-071 — Valid-card update then removal then retry

- Status: PARTIAL; layer: Prior live observation + fresh Postgres; priority: P0.
- Preconditions: Declined entry with new valid test card
- Steps: Update card; withdraw; send retry; correlate all commands/webhooks
- Expected: Reject new post-removal retry; account for any already-started attempt; never hide successful payment requiring action
- Observed: Related lifecycle defects reproduced locally; earlier valid-card/removal run retained separately.
- Remaining: Exact valid-card-then-removal live sequence was not repeated in this execution; no processor correlation to isolate its earlier success.
- Executed native evidence: regressions-db::test_withdrawal_blocks_manual_retry_of_failed_charge [FAIL]; regressions-db::test_late_success_is_not_lost_after_withdrawal_cancels_requested_charge [FAIL]

### RET-072 — Declined athlete replaced by alternate

- Status: PARTIAL; layer: Postgres; priority: P0.
- Preconditions: Full field plus eligible alternate
- Steps: Withdraw declined athlete; promote alternate; advance old due times
- Expected: Old athlete stays withdrawn with no new retries; new athlete has independent entry/payment reference and seat
- Observed: Real DB coupled declined withdrawal, alternate promotion and scheduler stop test executed.
- Remaining: Synthetic isolated one-seat event; no live full-format field/alternate payment collection.
- Executed native evidence: alternate-db::test_declined_withdrawal_alternate_promotion_stops_old_scheduled_retry [PASS]

### RET-073 — Alternate promotion while old payment unresolved

- Status: PARTIAL; layer: Unit + Postgres; priority: P0.
- Preconditions: Original attempt processing; place released
- Steps: Promote alternate before old payment result arrives
- Expected: No seat restoration or alternate eviction from late old success; Finance reconciliation retained
- Observed: Late-result state handling and reconciliation defect examined.
- Remaining: No combined live alternate promotion while provider attempt deliberately held.
- Executed native evidence: competition-unit::test_nobody_outside_the_field_is_counted_as_charged [PASS]; regressions-db::test_late_success_is_not_lost_after_withdrawal_cancels_requested_charge [FAIL]

### RET-074 — Re-entry after withdrawal

- Status: PARTIAL; layer: Unit + Postgres; priority: P0.
- Preconditions: Same athlete re-enters legitimately
- Steps: Create new entry and eligible charge; deliver old retry messages
- Expected: Old entry not revived; new charge is separately authorised; no reuse of old payment identity
- Observed: Entry identity/ownership and released-reference handling covered separately.
- Remaining: Complete re-entry plus stale old payment-command delivery not run.
- Executed native evidence: competition-unit::test_an_entry_is_created_waitlisted_with_the_event_fee [PASS]; competition-unit::test_another_member_and_an_unknown_reference_are_refused_alike [PASS]

### RET-075 — Fee waived before retry

- Status: PASS; layer: Unit + Postgres; priority: P0.
- Preconditions: Unpaid entry; fee waiver permitted
- Steps: Waive fee then tick/manual retry
- Expected: No further charge or notice; waiver reason/audit preserved
- Observed: Waiver cancels eligibility and subsequent worker emits no charge or notice.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: competition-integration::test_an_athlete_cleared_to_compete_without_paying_is_never_charged_again [PASS]; competition-unit::test_an_athlete_cleared_to_compete_without_paying_is_never_charged_again [PASS]; competition-unit::test_waiving_the_fee_stages_a_release [PASS]

### RET-076 — Proceed without payment

- Status: PARTIAL; layer: Unit; priority: P0.
- Preconditions: TM records reasoned payment override
- Steps: Advance schedule and request manual retry
- Expected: No charge after clearance; UI/history identify override
- Observed: Override/cleared guard stops automatic charge in isolated stores.
- Remaining: Every live override mode and manual-retry follow-up not run.
- Executed native evidence: competition-integration::test_an_athlete_cleared_to_compete_without_paying_is_never_charged_again [PASS]; competition-unit::test_an_athlete_cleared_to_compete_without_paying_is_never_charged_again [PASS]

### RET-077 — Waiver races manual retry

- Status: PASS; layer: Postgres; priority: P0.
- Preconditions: Unpaid failed charge
- Steps: Submit waiver and retry concurrently
- Expected: Atomic winner; no successful fee waiver while a card attempt is still legitimately in flight
- Observed: Concurrent real DB claim/waiver locking prevents waiver from slipping past an active request.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: competition-integration::test_a_manual_retry_claims_the_charge_so_a_waiver_cannot_follow_it [PASS]; competition-integration::test_a_waiver_waits_for_a_retry_claim_that_has_not_committed_yet [PASS]

### RET-078 — Denied/rejected entry cannot retry

- Status: FAIL; layer: Unit; priority: P1.
- Preconditions: Terminal entry state other than withdrawn
- Steps: Send stale/direct retry action
- Expected: Backend rejects terminal entry; UI visibility is not the security guard
- Observed: Withdrawn, Removed, Not selected and Expired entries all allowed manual preparation when a FAILED charge was exposed.
- Remaining: Four failing parameter variants share the missing terminal-status guard.
- Executed native evidence: lifecycle::test_matrix_terminal_entry_must_not_prepare_manual_retry[withdrawn] [FAIL]; lifecycle::test_matrix_terminal_entry_must_not_prepare_manual_retry[removed] [FAIL]; lifecycle::test_matrix_terminal_entry_must_not_prepare_manual_retry[not_selected] [FAIL]; lifecycle::test_matrix_terminal_entry_must_not_prepare_manual_retry[expired] [FAIL]

### RET-079 — Event archived/cancelled with unpaid entries

- Status: REVIEW; layer: Not executed; priority: P1.
- Preconditions: Unpaid entries and scheduled recoveries
- Steps: Archive/cancel event using supported path
- Expected: Approved policy explicitly determines stop/refund behavior; no accidental charging under ambiguous lifecycle
- Observed: Event archived/cancelled recovery policy not experimentally altered.
- Remaining: DEC-05: clarify stop/refund policy.
- Executed native evidence: See live check evidence or blocker.

### RET-080 — Same retry key concurrent replay

- Status: PARTIAL; layer: Live dev; priority: P0.
- Preconditions: One failed entry; two identical request keys
- Steps: POST two retry requests together
- Expected: One logical claim/execute; replay response allowed; at most one provider attempt
- Observed: Same-key concurrent requests returned 200/200 with one new history outcome.
- Remaining: Inactive-card fixture did not create fresh provider attempts; exact provider dedup count not queried.
- Executed native evidence: See live check evidence or blocker.

### RET-081 — Different retry keys concurrent race

- Status: PARTIAL; layer: Live dev; priority: P0.
- Preconditions: One failed entry; distinct keys
- Steps: POST two retries at barrier
- Expected: One wins claim; other refused; one provider attempt
- Observed: Distinct-key concurrent requests returned 200/409 and one outcome.
- Remaining: Provider-attempt correlation absent; active failure fixture had inactive card.
- Executed native evidence: See live check evidence or blocker.

### RET-082 — Two scheduler instances

- Status: PASS; layer: Postgres; priority: P0.
- Preconditions: Same charge due in database
- Steps: Run two workers concurrently with real repositories
- Expected: FOR UPDATE SKIP LOCKED prevents duplicate claim; one logical dispatch
- Observed: Two simultaneous real worker passes staged exactly one execute for the due entry.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: concurrency-org::test_two_real_workers_claim_one_due_charge_once [PASS]

### RET-083 — Manual versus scheduler race

- Status: PARTIAL; layer: Postgres + Unit; priority: P0.
- Preconditions: Same charge due and manually retryable
- Steps: Start manual claim and scheduler together
- Expected: At most one in-flight attempt; stable attempt identity and truthful counters
- Observed: Manual claim locking and two-worker race tested separately.
- Remaining: Manual-versus-scheduler concurrent barrier not run as a combined case.
- Executed native evidence: competition-integration::test_a_manual_retry_claims_the_charge_so_a_waiver_cannot_follow_it [PASS]; concurrency-org::test_two_real_workers_claim_one_due_charge_once [PASS]

### RET-084 — Duplicate execute delivery

- Status: PARTIAL; layer: Unit + Postgres; priority: P0.
- Preconditions: Payment receives same command twice
- Steps: Replay same message/request ID
- Expected: Same logical result; no second processor charge
- Observed: Idempotent state/request handling verified locally.
- Remaining: No duplicate execute delivered through a running broker with Stripe-side attempt count.
- Executed native evidence: payment-integration::test_create_or_none_is_idempotent_on_reference_id [PASS]; payment-integration::test_record_payment_intent_is_a_no_op_on_a_repeated_id [PASS]; payment-unit::test_no_payment_intent_redelivery_safety_does_not_double_announce [PASS]

### RET-085 — Duplicate paid/failed webhooks

- Status: PARTIAL; layer: Unit + Postgres; priority: P0.
- Preconditions: Deliver same event repeatedly
- Steps: Inspect payment, competition, history and notices
- Expected: Monotonic state; one effective outcome; no duplicate confirmation/notification
- Observed: Duplicate/stale outcome gates tested.
- Remaining: Both webhook types not replayed through full live payment→competition→notification chain.
- Executed native evidence: payment-integration::test_apply_charge_outcome_drops_a_stale_redelivery [PASS]; payment-unit::test_watermark_no_op_always_allowed_even_when_stale [PASS]; payment-unit::test_watermark_refuses_a_real_change_at_or_before_the_watermark [PASS]; payment-unit::test_watermark_allows_a_real_change_strictly_after [PASS]; payment-unit::test_watermark_does_not_override_an_illegal_transition [PASS]; payment-unit::test_no_payment_intent_redelivery_safety_does_not_double_announce [PASS]

### RET-086 — Paid then stale failure

- Status: PARTIAL; layer: Unit + Postgres; priority: P0.
- Preconditions: Deliver newer paid fact before older failed fact
- Steps: Process both
- Expected: Paid cannot become failed or reschedule automatically
- Observed: Paid/terminal and watermark protections exercised locally.
- Remaining: Live older-failure event injection not performed.
- Executed native evidence: payment-integration::test_apply_charge_outcome_drops_a_stale_redelivery [PASS]; payment-unit::test_terminal_states_refuse_every_further_transition[ready-paid] [PASS]; payment-unit::test_terminal_states_refuse_every_further_transition[ready-released] [PASS]; payment-unit::test_terminal_states_refuse_every_further_transition[charging-paid] [PASS]; payment-unit::test_terminal_states_refuse_every_further_transition[charging-released] [PASS]; payment-unit::test_terminal_states_refuse_every_further_transition[retryable-paid] [PASS]; payment-unit::test_terminal_states_refuse_every_further_transition[retryable-released] [PASS]; payment-unit::test_watermark_refuses_a_real_change_at_or_before_the_watermark [PASS]

### RET-087 — Withdraw then late paid fact

- Status: FAIL; layer: Postgres; priority: P0.
- Preconditions: Local charge cancelled; payment succeeds later
- Steps: Deliver success after withdrawal
- Expected: Entry remains withdrawn; payment fact reconciled and visible; no silent loss of paid evidence
- Observed: record_charge_result returned None for a late success after cancellation; competition charge remained cancelled.
- Remaining: Payment-service record may still hold the money; absence of a broader Finance reconciler was not proven by this component test.
- Executed native evidence: regressions-db::test_late_success_is_not_lost_after_withdrawal_cancels_requested_charge [FAIL]

### RET-088 — Failures arrive out of order

- Status: PARTIAL; layer: Unit + Postgres; priority: P1.
- Preconditions: Multiple genuine attempt outcomes delayed
- Steps: Deliver older failure after newer state
- Expected: Preserve first-failure anchor; do not regress or restart exhausted schedule
- Observed: Clock pinning and stale state transitions covered.
- Remaining: No full multi-attempt out-of-order live bus delivery sequence.
- Executed native evidence: competition-unit::test_a_later_decline_keeps_the_first_clock_and_schedules_the_next_retry [PASS]; payment-integration::test_apply_charge_outcome_drops_a_stale_redelivery [PASS]

### RET-089 — Retry after API timeout

- Status: PARTIAL; layer: Live dev + Unit; priority: P0.
- Preconditions: Client times out after accepted retry
- Steps: Resend identical idempotency key
- Expected: Return/recover original action; no second logical attempt
- Observed: Same-key replay and claim gating covered.
- Remaining: No forced client disconnect/HTTP timeout after accept to prove transport recovery.
- Executed native evidence: competition-unit::test_a_second_retry_of_the_same_charge_is_told_there_is_nothing_to_retry [PASS]

### RET-090 — Worker shortly late

- Status: PASS; layer: Unit + Postgres; priority: P1.
- Preconditions: Retry due 24h; first worker tick 25h
- Steps: Run pass
- Expected: One due attempt; no catch-up burst; unchanged policy/deadline
- Observed: A 25-hour-old failure produced one due retry and notice; repeated pass did not duplicate.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: competition-integration::test_a_decline_is_scheduled_and_one_pass_sends_the_retry_and_the_notice [PASS]; competition-unit::test_a_retry_is_sent_when_it_is_due_and_not_before [PASS]

### RET-091 — Worker skips first offset

- Status: PASS; layer: Unit; priority: P1.
- Preconditions: No failure rescheduling until after 24h
- Steps: Compute next retry at hour 50
- Expected: Skip old 24h slot; schedule 72h if within deadline
- Observed: Hour-50 rescheduling skips the elapsed first slot and does not burst catch-up charges.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: competition-unit::test_a_retry_whose_time_has_passed_is_skipped_not_sent_at_once[100-168] [PASS]; competition-unit::test_a_retry_whose_time_has_passed_is_skipped_not_sent_at_once[30-72] [PASS]; competition-unit::test_a_retry_whose_time_has_passed_is_skipped_not_sent_at_once[73-168] [PASS]; competition-unit::test_a_failed_manual_retry_is_not_followed_by_a_burst_of_automatic_ones [PASS]

### RET-092 — Too-late overdue attempt

- Status: PASS; layer: Unit / explicit version 16; priority: P0.
- Preconditions: Scheduled retry remains; tick at deadline+24h
- Steps: Test just before/exactly/after tolerance
- Expected: Code sends only before strict tolerance end; at/after it no late dispatch
- Observed: Dispatch occurs just before deadline+24h; at and after exact tolerance end no late dispatch.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: lifecycle::test_matrix_lateness_tolerance_boundary[-1] [PASS]; lifecycle::test_matrix_lateness_tolerance_boundary[0] [PASS]; lifecycle::test_matrix_lateness_tolerance_boundary[1] [PASS]

### RET-093 — Command unanswered within timeout

- Status: PASS; layer: Unit; priority: P1.
- Preconditions: Requested charge; request_timeout_at future
- Steps: Tick before timeout
- Expected: Remain requested; no duplicate retry/waiver admission
- Observed: Requested charge remains waiting inside its answer window.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: competition-unit::test_a_requested_charge_still_inside_its_window_is_left_waiting [PASS]

### RET-094 — Command unanswered at timeout

- Status: PARTIAL; layer: Unit + Postgres; priority: P0.
- Preconditions: Requested charge; timeout exactly now
- Steps: Run release-unanswered then worker
- Expected: Release claim safely; recovery eligibility recalculated; no permanent stuck state
- Observed: Expired unanswered claim released; flagged manual claim also recovered.
- Remaining: Exact timeout minus/exact/plus millisecond DB sequence not all covered.
- Executed native evidence: competition-integration::test_a_flagged_hand_retry_nobody_answered_is_released_by_the_job [PASS]; competition-unit::test_a_requested_charge_nobody_answered_goes_back_to_failed [PASS]

### RET-095 — Late answer after timeout/retry

- Status: PARTIAL; layer: Unit + Postgres; priority: P0.
- Preconditions: Old attempt answers after claim release
- Steps: Deliver late paid/failed result with attempt correlation
- Expected: No duplicate capture or state regression; reconcile correct attempt
- Observed: Timeout release and stale-result guards tested separately.
- Remaining: No delayed provider answer after a newly sent replacement retry with exact attempt correlation.
- Executed native evidence: competition-unit::test_a_requested_charge_nobody_answered_goes_back_to_failed [PASS]; payment-integration::test_apply_charge_outcome_drops_a_stale_redelivery [PASS]

### RET-096 — Grace expires during in-flight retry

- Status: PASS; layer: Unit; priority: P1.
- Preconditions: A permitted final attempt is awaiting answer
- Steps: Tick at deadline before answer_by
- Expected: Do not flag while valid answer window is open; do not dispatch another attempt
- Observed: Allowed final attempt holds escalation while answer window is valid; no second concurrent dispatch.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: competition-unit::test_the_last_retry_is_sent_even_though_it_falls_on_the_deadline [PASS]; competition-unit::test_the_entry_is_flagged_once_the_last_retry_has_been_answered [PASS]

### RET-097 — No answer beyond final window

- Status: PASS; layer: Unit + Postgres; priority: P1.
- Preconditions: In-flight attempt never answers
- Steps: Tick at/after answer_by
- Expected: Flag rather than hold place indefinitely; no endless automatic retries
- Observed: Unanswered attempt cannot hold the process forever; timeout/flag recovery exercised.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: competition-integration::test_a_flagged_hand_retry_nobody_answered_is_released_by_the_job [PASS]; competition-unit::test_a_retry_nobody_answers_does_not_hold_the_flag_back_for_ever [PASS]

### RET-098 — One corrupt charge does not stop others

- Status: PARTIAL; layer: Unit; priority: P0.
- Preconditions: Two due charges; first throws inside savepoint
- Steps: Run full pass
- Expected: Other valid charge processed; failed count/job status exposes error; no partial inconsistent row
- Observed: Per-item simulated failure left other charges processed and failed count visible.
- Remaining: Same corruption not injected into real DB savepoint execution.
- Executed native evidence: See live check evidence or blocker.

### RET-099 — Crash around outbox commit

- Status: BLOCKED; layer: Not executed; priority: P0.
- Preconditions: Crash before commit/after commit/before publish
- Steps: Restart worker and relay
- Expected: No orphan state or duplicate logical payment; transactional outbox and idempotency preserve recovery
- Observed: Process-kill fault injection around outbox commit/publish not performed.
- Remaining: Needs controlled relay/broker lifecycle and durable restart fixtures.
- Executed native evidence: See live check evidence or blocker.

### RET-100 — Dependency outage

- Status: PARTIAL; layer: Unit; priority: P1.
- Preconditions: Rules lookup/DB/NATS/payment unavailable
- Steps: Inject each fault and retry service recovery
- Expected: Visible failure; no false success or new policy promise; safe retriable processing
- Observed: One collaborator failure isolated in application tests.
- Remaining: Full DB/NATS/payment outage and recovery permutations not executed.
- Executed native evidence: See live check evidence or blocker.

### RET-101 — Athlete cannot trigger manager retry

- Status: PARTIAL; layer: Live dev + Unit; priority: P0.
- Preconditions: Athlete token and another account token
- Steps: Call TM retry endpoint
- Expected: Permission denied; no execute or payment side effect
- Observed: Authenticated athlete retry request returned 403.
- Remaining: Another-account authenticated session and all permission variants not covered live.
- Executed native evidence: competition-unit::test_a_non_hub_role_is_refused [PASS]; competition-unit::test_a_non_hub_role_cannot_promote [PASS]

### RET-102 — Organisation isolation

- Status: PARTIAL; layer: Postgres; priority: P0.
- Preconditions: Two organisations with known own fixtures
- Steps: Try cross-org retry, histories and identifiers
- Expected: No cross-org read/claim/charge; scoped storage queries enforce ownership
- Observed: Second bound organisation could neither read original entry nor prepare its retry.
- Remaining: No live second-tenant HTTP or payment-charge operation test.
- Executed native evidence: concurrency-org::test_other_organisation_cannot_prepare_retry_or_read_entry [PASS]

### RET-103 — Tampered payment inputs

- Status: PARTIAL; layer: Unit; priority: P0.
- Preconditions: Valid retry endpoint plus injected user/card/amount/reference fields
- Steps: Attempt charge redirection or reprice
- Expected: Only authorised stored agreement used; reject unsupported tampering
- Observed: Stored-user/reference/amount guards tested at service boundaries.
- Remaining: Tampered live HTTP payload fields not exhaustively submitted.
- Executed native evidence: competition-unit::test_the_charge_names_who_to_charge_and_a_key_fixed_by_the_confirmation [PASS]; payment-unit::test_wrong_owner_gets_the_same_message_as_not_found [PASS]; payment-unit::test_create_retry_with_a_different_amount_is_rejected_distinctly [PASS]; payment-unit::test_confirmation_none_for_wrong_owner [PASS]; payment-unit::test_repoint_rejected_for_wrong_owner [PASS]; payment-unit::test_abandon_rejects_wrong_owner_with_the_same_message_as_not_found [PASS]

### RET-104 — History distinguishes outcomes

- Status: PASS; layer: Live dev + Unit; priority: P1.
- Preconditions: Accepted request; provider attempted vs refused
- Steps: Compare histories for both
- Expected: Do not label HTTP 200 as collected; distinguish charge started, declined, not attempted and succeeded
- Observed: Live histories distinguish original decline from not-attempted outcomes; valid recovery recorded separately as succeeded.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: competition-unit::test_a_charge_payment_refused_to_attempt_says_so_and_is_not_an_attempt [PASS]

### RET-105 — UI state after recovery

- Status: FAIL; layer: Live dev; priority: P1.
- Preconditions: Keep TM roster open during actual valid-card recovery
- Steps: Observe without reload, then reload
- Expected: Pending/Collected/Confirmed truthful; no stale Retry action after success
- Observed: Fresh dev recovery reached Collected/Confirmed in API readback, but the open authenticated manager roster stayed Declined/Pending for the 90-second observation. Refresh displayed Collected. Separate athlete/manager sessions used.
- Remaining: Deployed source revision and intended refresh SLA not verified; source hook has no interval. Earlier shared-cookie observation was independently retested.
- Executed native evidence: See live check evidence or blocker.

### RET-106 — Withdrawn success visible for Finance

- Status: PARTIAL; layer: Prior dev + fresh Postgres; priority: P0.
- Preconditions: Withdrawn entry with late paid outcome
- Steps: Inspect roster, history and finance/reconciliation path
- Expected: Successful payment not silently hidden; approved reconciliation/refund action traceable
- Observed: Known withdrawn history/payment visibility concern retained; local reconciliation failure reproduced.
- Remaining: No fresh Finance dashboard/action demonstration or withdrawn-success UI rerun.
- Executed native evidence: regressions-db::test_late_success_is_not_lost_after_withdrawal_cancels_requested_charge [FAIL]

### RET-107 — Refund/reconciliation idempotency

- Status: BLOCKED; layer: Not executed; priority: P0.
- Preconditions: Refund required by approved policy
- Steps: Repeat workflow/events and retry refund request
- Expected: At most one correct refund; correct amount/currency; audit links original charge
- Observed: No refund initiated or duplicated.
- Remaining: Requires agreed refund decision plus isolated refund workflow/provider correlation.
- Executed native evidence: See live check evidence or blocker.

### RET-108 — Audit and correlation completeness

- Status: PARTIAL; layer: Live dev + Unit; priority: P1.
- Preconditions: Retry, withdrawal, release and outcome recorded
- Steps: Trace request/message/entry/charge/provider IDs
- Expected: Every transition attributable; keys preserved; timestamps distinguish request, dispatch, provider and consumer times
- Observed: Application history, request IDs and synthetic execute identities captured.
- Remaining: Full execute/release/Stripe provider timestamp correlation remains unavailable.
- Executed native evidence: competition-unit::test_each_rule_changed_is_a_history_line_with_the_save_s_request_id [PASS]; competition-unit::test_a_history_line_states_what_the_rule_was_in_force_not_what_the_form_held [PASS]; competition-unit::test_each_charge_started_leaves_a_line_on_its_entrys_history_naming_the_manager [PASS]

### RET-109 — No sensitive data in evidence

- Status: PASS; layer: Export scan; priority: P1.
- Preconditions: Report exports and recordings available
- Steps: Scan exported API payloads and media
- Expected: No passwords, tokens, client secrets or full card details; use test-mode identifiers only
- Observed: Published result JSON and XML scanned for passwords, JWTs, bearer values, client secrets and API secret keys before publication.
- Remaining: None within the named layer; not a claim of all-layer certification.
- Executed native evidence: See live check evidence or blocker.

### RET-110 — Load and fairness under bounded batch

- Status: BLOCKED; layer: Not executed; priority: P1.
- Preconditions: Many due charges across organisations; varied failures
- Steps: Run controlled local/integration batch
- Expected: No tenant starvation or duplicate claims; each failed item isolated; avoid payment-provider load testing
- Observed: Bounded fairness/load batch not executed.
- Remaining: No benchmark fixture or pass/fail throughput/fairness targets; do not treat ordinary unit-test volume as a load test.
- Executed native evidence: See live check evidence or blocker.


# Payment retry execution: technical findings

These findings describe the inspected local source. The deployed revision was not verified. Suggested priorities below are QA recommendations, not assigned Jira priorities. No Jira ticket or application fix was created.

## F-01 — Completed retry offset can be selected again at exact boundary

- Matrix: RET-028. Suggested priority: P2, pending confirmation of impact through the complete result-consumer path.
- Source: `wsl-competition-service/src/competition/domain/payment_retries.py:80`, `next_retry_at`.
- Preconditions: version-16 policy, retryable failure, T0 = 20 October 2026 12:00 UTC, retry offsets 24 and 72 hours, grace 168 hours, `retries_sent=1`.
- Reproduction: call the real function with `now=T0+24h` after the first retry is recorded as sent.
- Expected: next due is 23 October 2026 12:00 UTC (T0+72h).
- Actual: next due is 21 October 2026 12:00 UTC (T0+24h), the already-used offset.
- Cause: the count only guards schedule exhaustion; the loop starts from the first configured offset and accepts `due >= now`.
- Evidence: `boundaries.xml`, `test_completed_retry_offset_is_not_rescheduled_at_same_instant`, failed assertion retained.
- Impact limit: this proves a scheduling calculation defect. A second provider charge was not demonstrated; worker claim/idempotency gates may reduce the end-to-end impact.
- Backend direction: track consumed schedule positions explicitly and preserve skip-past behavior. Test first-failure handling, delayed answers, manual failures, skipped offsets, and exact-time redeliveries before changing count semantics.

## F-02 — Manual retry preparation lacks an entry lifecycle guard

- Matrix: RET-067 and RET-078. Suggested priority: P2 for a defensive payment gate, with production reachability investigation required.
- Source: `wsl-competition-service/src/competition/application/entries.py:660`, `retry_payment_prepare`.
- Preconditions: a terminal entry still has an exposed FAILED charge eligible for manual retry.
- Reproduction A: parameterized application tests expose such a charge on Withdrawn, Removed, Not selected, and Expired entries; call manual retry preparation as Tour Manager.
- Reproduction B: in disposable Postgres, create and decline a charge, call the withdrawal repository directly, then call real manual retry preparation in the transaction.
- Expected: refuse the retry and stage no execute command for a terminal entry.
- Actual: preparation returned `chargeable=True`; execute was staged. Four unit variants and one real-DB acceptance assertion failed.
- Cause: preparation checks the exposed charge ID and claims the charge, without checking the current entry lifecycle.
- Critical scope distinction: reproduction B deliberately bypasses the application withdrawal orchestration. The complete application withdrawal path cancels charge eligibility and emits a release. A separate real-DB test running application withdrawal, alternate promotion, and the retry worker **passed**, with the old charge CANCELLED and no new scheduled execute. Fresh retries against the existing withdrawn dev fixtures also returned HTTP 409. This is not evidence that every ordinary withdrawal continues charging.
- Evidence: `lifecycle.xml`, `regressions-db.xml`; supporting safe-path evidence in `alternate-db.xml` and live retry JSON.
- Backend direction: enforce lifecycle eligibility at the transactional retry claim, then recheck at execution where practical. Preserve idempotent release and reconcile in-flight payment outcomes. A stale FAILED row must not be enough to charge a removed entrant.

## F-03 — Late success is ignored after competition charge cancellation

- Matrix: RET-087. Suggested priority: P2 for reconciliation visibility; financial impact requires provider/Finance correlation.
- Source: `wsl-competition-service/src/competition/infrastructure/persistence/repositories/events/entries.py:379`, `record_charge_result`.
- Preconditions: a REQUESTED competition charge is cancelled by withdrawal while an external attempt may already have started.
- Reproduction: create REQUESTED charge in disposable Postgres, withdraw through the repository, then deliver `succeeded=True` to the real charge-result repository method.
- Expected: preserve the terminal entry and record or route the late financial success for reconciliation.
- Actual: method returned `None`; the competition charge remained CANCELLED. The acceptance assertion failed.
- Cause: update permits OPEN and FAILED charge statuses; CANCELLED is excluded and produces an early return.
- Impact limit: the probe targets this component. It did not hold an actual provider request in flight, replay a complete live webhook/broker chain, prove a missing Finance record elsewhere, or establish a refund obligation.
- Evidence: `regressions-db.xml`, `test_late_success_is_not_lost_after_withdrawal_cancels_requested_charge`.
- Backend direction: maintain an immutable payment outcome or reconciliation record for late success without restoring the withdrawn entrant. Decide refund/manual review policy with Finance and make processing idempotent.

## F-04 — Open manager roster remains stale after successful card recovery

- Matrix: RET-105. Suggested priority: P3 for stale operational status; confirm intended live-update behavior with the product owner.
- Environment: live dev, 21 October 2026, separate authenticated athlete and manager browser contexts.
- Event: `01a15d6d-df77-76f9-99fa-5cff13be3f99`; entry: `01a15d6d-eb6b-762c-bf81-59240b572ff4`.
- Reproduction: confirm and charge the declining Stripe test card; leave the Tour Manager Athletes tab open; change the athlete's entry to a valid saved Visa from a separate session; observe the existing manager tab for 90 seconds; reload.
- Expected: the open roster reflects successful asynchronous recovery, with Collected payment, Confirmed entry, and updated counters.
- Actual: card change returned HTTP 202 at 07:47:41 UTC. API readback reached Collected/Confirmed, while the open roster remained Declined/Pending through the observation period. After refresh at 07:49:32 UTC, it displayed Collected. Exactly one successful history outcome was recorded; paid retry was rejected with HTTP 409.
- Evidence: `recovery-before-refresh.png`, `recovery-after-refresh.png`, `recovery-recording.webm`, and `recovery-results.json` in the published execution folder. Original shared-cookie observation was retested independently and is not used as sole proof.
- Code observation: `wsl-frontend/src/features/tour-manager/hooks/use-tour-manager.ts:401`, `useSeedList`, defines a query key and fetch function without a polling interval. This is consistent with the stale view, but the deployed revision and all global invalidation mechanisms were not verified, so it is a likely explanation rather than a proven production root cause.
- Frontend direction: invalidate or refresh relevant seed-list, summary and history queries on asynchronous payment updates, with bounded polling or a suitable event channel. Avoid relying only on mutations initiated in that manager tab. Preserve unsaved seed edits during refresh.

## Safe path established for the original withdrawal question

With a retryable decline 25 hours old in a disposable database, the complete application withdrawal cancelled the old charge. An alternate was promoted to seed 1 in a synthetic one-seat field. A real worker pass then emitted no execute for the old entrant. This verifies that controlled scheduled-retry path locally. It does not certify a full live event format, a payment already inside Stripe, or all execute/release message orderings.

## Time acceleration and reproducibility

Version-16 boundary fixtures explicitly use retry offsets `(24,72)`, notice offsets `(24,72,120,168)`, grace `168h`, and short-notice cutoff `10 days`. Worker tests advance injected clocks or seed old first-failure timestamps in disposable Postgres 16. No shared dev clock, UUID, first-failure timestamp, or payment policy was changed. Existing native suites also exercise code-default version 0, whose retry offsets/cutoff differ; those results are labelled separately.

New acceptance probes are in `tests/unit/test_retry_matrix_boundaries.py`, `tests/unit/test_retry_matrix_lifecycle.py`, and `tests/integration/test_retry_matrix_regressions.py` under the competition service. XML evidence contains the exact test names, assertions and timings. The seven failed native assertions represent the three findings above, not seven independent bugs. The final live browser result is reported separately in RET-105.
