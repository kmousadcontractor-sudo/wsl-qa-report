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
