"""Real-Postgres acceptance probes for withdrawn charge lifecycle gaps."""
import datetime as dt
import asyncio
import pytest
from sqlalchemy import select, update, delete
from wsl_messaging.ids import uuid7
from wsl_service_core.db.org import bound_org
from wsl_service_core.db.session import session_factory
from wsl_service_core.testing.org import bound_to
from competition.application.entries import retry_payment_prepare, withdraw_entry, promote_entry
from competition.application.ports.audit import Actor
from competition.infrastructure.persistence.repositories.audit import SqlAuditLog
from competition.infrastructure.messaging.publisher import OutboxPublisher
from competition.domain.vocabulary import EntryStatus, ChargeStatus
from competition.application.ports.event_store import WithdrawalWrite
from competition.domain.vocabulary import WithdrawalStage
from competition.infrastructure.messaging.commander import OutboxCommander
from competition.infrastructure.persistence.repositories.events import SqlEventStore
from competition.infrastructure.persistence.repositories.charge_retries import SqlChargeRetries
from competition.infrastructure.persistence import models as m
from .test_payment_retry import _entries_charging, _decline
from .test_payment_retry import _outbox
from competition import payment_retry
from competition.application.entries import EntryNotFoundError
from competition.infrastructure.messaging.subjects import CMD_DEFERRED_CHARGE_EXECUTE

async def test_withdrawal_blocks_manual_retry_of_failed_charge(db):
    org=bound_org(db);(entry_id,)=await _entries_charging(db,1);factory=session_factory(db.bind)
    await _decline(factory,org,entry_id,failure_class='needs_new_method',hours_ago=1)
    async with bound_to(factory,org)() as s,s.begin():
        store=SqlEventStore(s);detail=await store.entry_detail(entry_id)
        await store.withdraw_entry(entry_id,version=detail.version,write=WithdrawalWrite(stage=list(WithdrawalStage)[0],reason='QA matrix withdrawal',decided_by_user_id=None))
        facts=await retry_payment_prepare(roles=frozenset({'tour_manager'}),entry_id=entry_id,request_id='matrix-'+str(uuid7()),store=store,charges=SqlChargeRetries(s),commands=OutboxCommander(s),now=dt.datetime.now(dt.UTC))
        assert facts.chargeable is False, 'Real withdrawn FAILED charge accepted a new retry and staged an execute command'

async def test_late_success_is_not_lost_after_withdrawal_cancels_requested_charge(db):
    org=bound_org(db);(entry_id,)=await _entries_charging(db,1);factory=session_factory(db.bind)
    async with bound_to(factory,org)() as s,s.begin():
        store=SqlEventStore(s);detail=await store.entry_detail(entry_id)
        await store.withdraw_entry(entry_id,version=detail.version,write=WithdrawalWrite(stage=list(WithdrawalStage)[0],reason='QA late provider success',decided_by_user_id=None))
        updated=await store.record_charge_result(entry_id,succeeded=True,failure_code=None)
        charge=await s.scalar(select(m.ChargeRequest).where(m.ChargeRequest.entry_id==entry_id))
        assert updated is not None, f'Late successful payment ignored; local charge still {charge.status}; needs reconciliation'

async def test_two_real_workers_claim_one_due_charge_once(db):
    org=bound_org(db);(entry_id,)=await _entries_charging(db,1);factory=session_factory(db.bind)
    await _decline(factory,org,entry_id,failure_class='retryable',hours_ago=25)
    await asyncio.gather(payment_retry._pass_once(factory),payment_retry._pass_once(factory))
    commands=await _outbox(factory,org,CMD_DEFERRED_CHARGE_EXECUTE)
    assert len(commands)==1
    assert commands[0].payload['reference_id']==str(entry_id)

async def test_other_organisation_cannot_prepare_retry_or_read_entry(db):
    org=bound_org(db);(entry_id,)=await _entries_charging(db,1);factory=session_factory(db.bind)
    await _decline(factory,org,entry_id,failure_class='needs_new_method',hours_ago=1)
    async with bound_to(factory,uuid7())() as s,s.begin():
        store=SqlEventStore(s)
        assert await store.entry_detail(entry_id) is None
        with pytest.raises(EntryNotFoundError):
            await retry_payment_prepare(roles=frozenset({'tour_manager'}),entry_id=entry_id,request_id='other-org-'+str(uuid7()),store=store,charges=SqlChargeRetries(s),commands=OutboxCommander(s),now=dt.datetime.now(dt.UTC))

async def test_declined_withdrawal_alternate_promotion_stops_old_scheduled_retry(db):
    org=bound_org(db);(entry_id,)=await _entries_charging(db,1);factory=session_factory(db.bind)
    async with bound_to(factory,org)() as s,s.begin():
        entry=await s.get(m.EventEntry,entry_id);event_id=entry.event_id
        alt_id=await s.scalar(select(m.EventEntry.id).where(m.EventEntry.event_id==event_id,m.EventEntry.id!=entry_id).limit(1))
        assert alt_id is not None
        await s.execute(update(m.Event).where(m.Event.id==event_id).values(field_size=1))
        await s.execute(update(m.EventEntry).where(m.EventEntry.event_id==event_id,m.EventEntry.id!=entry_id).values(entry_status=EntryStatus.WITHDRAWN,seed_rank=None,is_alternate=False,alternate_position=None))
        await s.execute(update(m.EventEntry).where(m.EventEntry.id==entry_id).values(seed_rank=1,is_alternate=False,alternate_position=None))
        await s.execute(update(m.EventEntry).where(m.EventEntry.id==alt_id).values(entry_status=EntryStatus.ALTERNATE,is_alternate=True,alternate_position=1,seed_rank=None,fee_waived=False))
        await s.execute(delete(m.ChargeRequest).where(m.ChargeRequest.entry_id==alt_id))
    await _decline(factory,org,entry_id,failure_class='retryable',hours_ago=25)
    actor=Actor(user_id=uuid7(),display_name='Matrix QA manager');now=dt.datetime.now(dt.UTC)
    async with bound_to(factory,org)() as s,s.begin():
        store=SqlEventStore(s);current=await store.entry_detail(entry_id)
        await withdraw_entry(roles=frozenset({'tour_manager'}),actor=actor,entry_id=entry_id,version=current.version,reason='QA declined replacement',store=store,audit=SqlAuditLog(s),now=now,publish=OutboxPublisher(s),commands=OutboxCommander(s))
        alt=await store.entry_detail(alt_id)
        moved=await promote_entry(roles=frozenset({'tour_manager'}),actor=actor,entry_id=alt_id,version=alt.version,store=store,audit=SqlAuditLog(s),now=now,publish=OutboxPublisher(s))
        assert moved.entry_id==alt_id and moved.seed_rank==1
    await payment_retry._pass_once(factory)
    assert await _outbox(factory,org,CMD_DEFERRED_CHARGE_EXECUTE)==[]
    async with bound_to(factory,org)() as s:
        old=await s.get(m.EventEntry,entry_id);charge=await s.scalar(select(m.ChargeRequest).where(m.ChargeRequest.entry_id==entry_id))
        assert old.entry_status is EntryStatus.WITHDRAWN
        assert charge.status is ChargeStatus.CANCELLED
        assert (await s.get(m.EventEntry,alt_id)).seed_rank==1
