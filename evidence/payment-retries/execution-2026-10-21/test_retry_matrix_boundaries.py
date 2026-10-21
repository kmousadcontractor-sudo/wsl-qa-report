"""Additional exact-boundary and regression coverage for the 110-case QA matrix.

No application code is modified; time is supplied to the real domain functions.
"""
import datetime as dt
import pytest
from competition.domain.payment_retries import deadline_at, event_starts_at, latest_notice_due, next_retry_at
from competition.domain.payment_rules import PaymentRules

T0=dt.datetime(2026,10,20,12,tzinfo=dt.UTC)
RULES=PaymentRules(grace_period_hours=168,notification_offsets_hours=(24,72,120,168),retry_offsets_hours=(24,72),short_notice_days=10)
D=T0+dt.timedelta(hours=168)

@pytest.mark.parametrize('offset', [24,72])
@pytest.mark.parametrize('delta_ms', [-1,0,1])
def test_notice_exact_boundary(offset,delta_ms):
    now=T0+dt.timedelta(hours=offset,milliseconds=delta_ms)
    sent=0 if offset==24 else 1
    got=latest_notice_due(RULES,first_failed_at=T0,notices_sent=sent,now=now,deadline=D)
    assert got == (None if delta_ms<0 else (1 if offset==24 else 2))

@pytest.mark.parametrize('offset,index', [(120,3),(168,4)])
@pytest.mark.parametrize('delta_ms', [-1,0,1])
def test_late_notice_exact_boundary(offset,index,delta_ms):
    assert latest_notice_due(RULES,first_failed_at=T0,notices_sent=index-1,now=T0+dt.timedelta(hours=offset,milliseconds=delta_ms),deadline=D)==(None if delta_ms<0 else index)

@pytest.mark.parametrize('offset', [24,72])
def test_next_retry_at_exact_due_and_just_after(offset):
    due=T0+dt.timedelta(hours=offset)
    assert next_retry_at(RULES,first_failed_at=T0,retries_sent=0,failure_class='retryable',deadline=D,now=due)==due
    got=next_retry_at(RULES,first_failed_at=T0,retries_sent=0,failure_class='retryable',deadline=D,now=due+dt.timedelta(milliseconds=1))
    assert got==(T0+dt.timedelta(hours=72) if offset==24 else None)

@pytest.mark.parametrize('class_', ['needs_new_method','action_required',None,'unexpected'])
def test_non_retryable_never_scheduled(class_):
    assert next_retry_at(RULES,first_failed_at=T0,retries_sent=0,failure_class=class_,deadline=D,now=T0) is None

@pytest.mark.parametrize('remaining', [-1,0,1,48,168,240])
def test_effective_deadline_around_cutoff(remaining):
    cutoff=T0+dt.timedelta(hours=remaining)
    assert deadline_at(RULES,first_failed_at=T0,event_start=cutoff+dt.timedelta(days=10))==min(D,cutoff)

def test_no_event_start_uses_grace():
    assert deadline_at(RULES,first_failed_at=T0,event_start=None)==D

def test_no_retry_after_configured_attempts_exhausted():
    assert next_retry_at(RULES,first_failed_at=T0,retries_sent=2,failure_class='retryable',deadline=D,now=T0) is None

def test_zero_retry_policy_still_has_notices():
    rules=PaymentRules(grace_period_hours=168,notification_offsets_hours=(24,72,120,168),retry_offsets_hours=(),short_notice_days=10)
    assert next_retry_at(rules,first_failed_at=T0,retries_sent=0,failure_class='retryable',deadline=D,now=T0) is None
    assert latest_notice_due(rules,first_failed_at=T0,notices_sent=0,now=T0+dt.timedelta(hours=24),deadline=D)==1

@pytest.mark.parametrize('start', [dt.datetime(2026,3,7,12,tzinfo=dt.UTC),dt.datetime(2028,2,28,12,tzinfo=dt.UTC),dt.datetime(2026,12,31,12,tzinfo=dt.UTC)])
def test_dst_leap_year_and_year_rollover_elapsed_offsets(start):
    due=next_retry_at(RULES,first_failed_at=start,retries_sent=0,failure_class='retryable',deadline=start+dt.timedelta(hours=168),now=start)
    assert (due-start).total_seconds()==86400

def test_current_utc_event_midnight_is_explicit():
    assert event_starts_at(dt.date(2026,11,20))==dt.datetime(2026,11,20,tzinfo=dt.UTC)

def test_completed_retry_offset_is_not_rescheduled_at_same_instant():
    """Acceptance criterion RET-028: an already-sent offset must not be chosen again."""
    due=next_retry_at(RULES,first_failed_at=T0,retries_sent=1,failure_class='retryable',deadline=D,now=T0+dt.timedelta(hours=24))
    assert due==T0+dt.timedelta(hours=72), 'Already sent 24h offset was selected again at its exact timestamp'
