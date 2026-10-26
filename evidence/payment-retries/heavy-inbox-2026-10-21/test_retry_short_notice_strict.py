"""Strict stop-at-cutoff acceptance: real worker with isolated fake collaborators."""
import datetime as dt
import pytest
from .test_retry_matrix_lifecycle import world
from .test_application_payment_retries import FIRST

@pytest.mark.parametrize('hours',[48,48.00000027777778,49,71.999,72])
async def test_overdue_pending_retry_must_stop_at_short_notice_cutoff(hours):
    w=await world(event_starts_at=FIRST+dt.timedelta(days=12))
    await w.decline(0)
    assert w.now_row.deadline_at==FIRST+dt.timedelta(hours=48)
    assert w.now_row.next_attempt_at==FIRST+dt.timedelta(hours=24)
    result=await w.tick(hours)
    print(f'hours={hours}; deadline={w.now_row.deadline_at}; retries={result.retries}; flagged={result.flagged}; commands={len(w.commands.sent)}')
    assert result.retries==0,'Automatic retry dispatched after entering short-notice window'
    assert result.flagged==1

async def test_normal_sequence_stops_before_72h_retry():
    w=await world(event_starts_at=FIRST+dt.timedelta(days=12))
    await w.decline(0)
    assert (await w.tick(24)).retries==1
    await w.decline(24.001)
    assert w.now_row.next_attempt_at is None
    assert (await w.tick(48)).flagged==1
    assert (await w.tick(72)).retries==0
    assert len(w.commands.sent)==1

@pytest.mark.parametrize('cutoff',[24,72])
async def test_retry_exactly_on_short_notice_cutoff_must_not_dispatch(cutoff):
    w=await world(event_starts_at=FIRST+dt.timedelta(days=10,hours=cutoff))
    await w.decline(0)
    if cutoff==72:
        await w.tick(24)
        await w.decline(24.001)
    result=await w.tick(cutoff)
    print(f'cutoff={cutoff}; retries={result.retries}; flagged={result.flagged}')
    assert result.retries==0,'Retry at the cutoff must stop under strict short-notice requirement'
