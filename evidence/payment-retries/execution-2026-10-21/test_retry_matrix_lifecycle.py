"""Matrix lifecycle probes using actual application functions and version-16 test rules."""
import datetime as dt
import pytest
from competition.domain.payment_rules import PaymentRules
from competition.domain.vocabulary import ChargeStatus, EntryStatus
from .catalogue_fakes import ACTOR
from .test_application_payment_retries import _World, FIRST
from .test_application_entries import _detail, _prepare, _charge_for

RULES=PaymentRules(grace_period_hours=168,notification_offsets_hours=(24,72,120,168),retry_offsets_hours=(24,72),short_notice_days=10)

async def world(**changes):
    w=_World(**changes)
    await w.rules.append(RULES,version=16,actor=ACTOR,at=FIRST)
    return w

@pytest.mark.parametrize('offset',[24,72])
@pytest.mark.parametrize('milliseconds',[-1,0,1])
async def test_matrix_worker_dispatch_exact_due_boundaries(offset,milliseconds):
    w=await world();await w.decline(0)
    if offset==72:
        await w.tick(24);await w.decline(25)
    n=len(w.commands.sent)
    result=await w.tick(offset+milliseconds/3600000)
    assert result.retries==(0 if milliseconds<0 else 1)
    assert len(w.commands.sent)-n==result.retries
    assert (await w.tick(offset+0.1)).retries==(1 if milliseconds<0 else 0)

@pytest.mark.parametrize('milliseconds',[-1,0,1])
async def test_matrix_deadline_boundary_without_inflight(milliseconds):
    w=await world();await w.decline(0,'needs_new_method')
    result=await w.tick(168+milliseconds/3600000)
    assert result.flagged==(0 if milliseconds<0 else 1)
    assert result.retries==0

@pytest.mark.parametrize('milliseconds',[-1,0,1])
async def test_matrix_lateness_tolerance_boundary(milliseconds):
    w=await world();await w.decline(0)
    result=await w.tick(192+milliseconds/3600000)
    assert result.retries==(1 if milliseconds<0 else 0)

@pytest.mark.parametrize('status',[EntryStatus.WITHDRAWN,EntryStatus.REMOVED,EntryStatus.NOT_SELECTED,EntryStatus.EXPIRED])
async def test_matrix_terminal_entry_must_not_prepare_manual_retry(status):
    entry=_detail(status=status,retryable_charge=True)
    facts=await _prepare(entry,_charge_for(entry))
    assert facts.chargeable is False, f'Terminal entry {status} was allowed to claim retry'

async def test_matrix_retry_exactly_at_cutoff_current_code():
    w=await world(event_starts_at=FIRST+dt.timedelta(days=11));await w.decline(0)
    assert w.now_row.deadline_at==FIRST+dt.timedelta(hours=24)
    assert (await w.tick(24)).retries==1

async def test_matrix_due_retry_after_cutoff_within_late_window_current_code():
    w=await world(event_starts_at=FIRST+dt.timedelta(days=11));await w.decline(0)
    assert (await w.tick(25)).retries==1

async def test_matrix_no_third_retry_under_version16():
    w=await world();await w.decline(0)
    await w.tick(24);await w.decline(25);await w.tick(72);await w.decline(73)
    assert w.now_row.next_attempt_at is None
    assert (await w.tick(120)).retries==0
    assert len(w.commands.sent)==2

async def test_matrix_no_first_failure_timestamp_does_not_dispatch():
    w=await world(status=ChargeStatus.SCHEDULED,next_attempt_at=FIRST)
    assert (await w.tick(24)).retries==0
    assert not w.commands.sent

@pytest.mark.parametrize('status',[EntryStatus.WITHDRAWN,EntryStatus.REMOVED,EntryStatus.NOT_SELECTED,EntryStatus.EXPIRED])
async def test_matrix_terminal_entry_stops_scheduled_retry_and_notices(status):
    w=await world();await w.decline(0)
    w.charges._set(w.row.charge_id,entry_status=status)
    result=await w.tick(25)
    assert result.stopped==1
    assert not w.commands.sent and not w.notices()
