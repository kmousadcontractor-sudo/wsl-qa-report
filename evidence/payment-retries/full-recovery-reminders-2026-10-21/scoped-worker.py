"""Run the deployed worker against ONLY explicitly named QA entries and a fixture clock."""
import asyncio,base64,dataclasses,datetime as dt,json,sys,uuid
from sqlalchemy import select
from wsl_service_core.settings import Settings as CoreSettings
from wsl_service_core.db.session import build_engine,session_factory
from wsl_service_core.db.org import bind_org
from competition.application.payment_retries import run_tick
from competition.infrastructure.persistence.repositories.charge_retries import SqlChargeRetries
from competition.infrastructure.persistence.repositories.events import SqlEventStore
from competition.infrastructure.persistence.repositories.payment_rules import SqlPaymentRules
from competition.infrastructure.persistence.models.confirmation import ChargeRequest
from competition.infrastructure.persistence.models.entry import EventEntry
from competition.infrastructure.persistence.models.structure import Event
from competition.infrastructure.messaging.commander import OutboxCommander
from competition.infrastructure.messaging.publisher import OutboxPublisher
CFG=json.loads(base64.b64decode(sys.argv[1]))
ORG=uuid.UUID(CFG['orgId'])
IDS=[uuid.UUID(x) for x in CFG['entries']]
FIELDS=['id','entry_id','status','first_failed_at','payment_rules_version','last_failure_class','retries_sent','notices_sent','next_attempt_at','deadline_at','flagged_at']
def snap(row):
    return {k:str(getattr(row,k)) if getattr(row,k) is not None else None for k in FIELDS}
class Scoped(SqlChargeRetries):
    def __init__(self,session,entry):
        super().__init__(session);self.entry=entry
    async def tracked(self):
        row=await self.latest_for_entry(self.entry)
        return [row] if row and row.first_failed_at is not None and row.flagged_at is None else []
    async def expired_claims(self,now):
        return list(await self._session.scalars(select(ChargeRequest.id).where(ChargeRequest.entry_id==self.entry,ChargeRequest.status=='requested',ChargeRequest.request_timeout_at.is_not(None),ChargeRequest.request_timeout_at<=now)))
async def main():
    settings=CoreSettings()
    assert str(settings.env).lower()=='dev',f'Wrong environment: {settings.env}'
    engine=build_engine(settings);factory=session_factory(engine);result=[]
    try:
        async with factory() as session,session.begin():
            bind_org(session,ORG)
            rows=(await session.execute(select(ChargeRequest,EventEntry,Event).join(EventEntry,EventEntry.id==ChargeRequest.entry_id).join(Event,Event.id==EventEntry.event_id).where(ChargeRequest.entry_id.in_(IDS)).with_for_update(of=ChargeRequest))).all()
            assert len(rows)==len(IDS),'Expected exactly one charge per QA entry'
            assert {c.entry_id for c,e,v in rows}==set(IDS)
            for c,e,v in rows:
                assert str(e.athlete_id)==CFG['athleteId']
                assert v.name.startswith('QA Full ') and ' reminders ' in v.name,'Not a named QA fixture'
                assert c.org_id==ORG and e.org_id==ORG and v.org_id==ORG
                before=snap(c);tick=None;clock=None
                if CFG.get('hours') is not None:
                    assert c.first_failed_at is not None and c.payment_rules_version==16
                    assert str(c.status)=='succeeded' or c.last_failure_class=='needs_new_method','This probe must not dispatch automatic payment commands'
                    clock=c.first_failed_at+dt.timedelta(hours=CFG['hours'])
                    tick=await run_tick(now=clock,charges=Scoped(session,c.entry_id),rules=SqlPaymentRules(session),entries=SqlEventStore(session),commands=OutboxCommander(session),publish=OutboxPublisher(session),isolated=session.begin_nested)
                    assert tick.failed==0 and tick.retries==0,'Unexpected worker failure or execute command'
                    await session.refresh(c)
                result.append({'entryId':str(c.entry_id),'eventName':v.name,'actualTime':dt.datetime.now(dt.UTC).isoformat(),'fixtureClock':clock.isoformat() if clock else None,'before':before,'tick':dataclasses.asdict(tick) if tick else None,'after':snap(c)})
        print('QA_RESULT_BASE64:'+base64.b64encode(json.dumps(result).encode()).decode()+':QA_RESULT_END')
    finally:
        await engine.dispose()
asyncio.run(main())

