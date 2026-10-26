"""Run the deployed worker against ONLY explicitly named QA entries and a fixture clock."""
import asyncio,base64,dataclasses,datetime as dt,json,sys,uuid,math
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
from competition.infrastructure.messaging.publisher import OutboxPublisher
def require(ok,message):
    if not ok:
        raise ValueError(message)
def environment(value):
    value=str(getattr(value,'value',value)).lower()
    require(value in ('dev','staging','staging01'),'Only dev or staging is allowed')
    return 'staging' if value in ('staging','staging01') else value
def validate_config(cfg):
    cfg=dict(cfg)
    cfg['environment']=environment(cfg.get('environment','dev'))
    require(cfg.get('mode','reminders_only')=='reminders_only','Only reminders_only mode is supported')
    require(isinstance(cfg.get('entries'),list) and 1<=len(cfg['entries'])<=10,'Provide 1–10 QA entry UUIDs')
    for key in ('orgId','athleteId'):
        uuid.UUID(cfg[key])
    ids=[uuid.UUID(x) for x in cfg['entries']]
    require(len(ids)==len(set(ids)),'Duplicate entry UUIDs')
    events=cfg.get('eventIds',[])
    require(isinstance(events,list),'eventIds must be a list')
    for value in events:
        uuid.UUID(value)
    require(cfg['environment']!='staging' or bool(events),'Staging requires explicit eventIds')
    prefix=cfg.get('eventNamePrefix','QA Full ')
    require(isinstance(prefix,str) and prefix.startswith('QA ') and len(prefix.strip())>=7,'Use a specific QA event-name prefix')
    cfg['eventNamePrefix']=prefix
    hours=cfg.get('hours')
    if hours is not None:
        require(not isinstance(hours,bool) and isinstance(hours,(int,float)) and math.isfinite(hours) and 0<=hours<=168,'hours must be null or a finite number from 0 to 168')
        version=cfg.get('expectedRuleVersion',16 if cfg['environment']=='dev' else None)
        require(not isinstance(version,bool) and isinstance(version,int) and version>0,'Set expectedRuleVersion from the baseline before a timed staging run')
        cfg['expectedRuleVersion']=version
    return cfg
async def no_payment_commands(*args,**kwargs):
    raise RuntimeError('Payment execute commands are forbidden by this reminder-only probe')
if len(sys.argv)==3 and sys.argv[1]=='--config':
    with open(sys.argv[2],encoding='utf-8-sig') as source:
        CFG=validate_config(json.load(source))
elif len(sys.argv)==2:
    CFG=validate_config(json.loads(base64.b64decode(sys.argv[1],validate=True)))
else:
    raise SystemExit('Usage: python payment-retry-scoped-worker.py BASE64_JSON | --config FILE.json')
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
        return list(await self._session.scalars(select(ChargeRequest.id).where(ChargeRequest.org_id==ORG,ChargeRequest.entry_id==self.entry,ChargeRequest.status=='requested',ChargeRequest.request_timeout_at.is_not(None),ChargeRequest.request_timeout_at<=now)))
async def main():
    settings=CoreSettings()
    require(environment(settings.env)==CFG['environment'],f"Wrong environment: configured {CFG['environment']}, service {settings.env}")
    engine=build_engine(settings);factory=session_factory(engine);result=[]
    try:
        async with factory() as session,session.begin():
            bind_org(session,ORG)
            rows=(await session.execute(select(ChargeRequest,EventEntry,Event).join(EventEntry,EventEntry.id==ChargeRequest.entry_id).join(Event,Event.id==EventEntry.event_id).where(ChargeRequest.entry_id.in_(IDS),ChargeRequest.org_id==ORG,EventEntry.org_id==ORG,Event.org_id==ORG).with_for_update(of=ChargeRequest))).all()
            require(len(rows)==len(IDS),'Expected exactly one charge per QA entry; use a fresh fixture if it has multiple attempts')
            require({c.entry_id for c,e,v in rows}==set(IDS),'QA entry set mismatch')
            for c,e,v in rows:
                require(str(e.athlete_id)==CFG['athleteId'],'QA athlete mismatch')
                require(v.name.startswith(CFG['eventNamePrefix']),'Not a named QA fixture')
                if CFG.get('eventIds'):
                    require(v.id in [uuid.UUID(x) for x in CFG['eventIds']],'Event not in QA allowlist')
                else:
                    require(' reminders ' in v.name,'Legacy dev event must contain reminders')
                require(c.org_id==ORG and e.org_id==ORG and v.org_id==ORG,'Organisation mismatch')
                before=snap(c);tick=None;clock=None
                pinned=await SqlPaymentRules(session).version(c.payment_rules_version) if c.payment_rules_version is not None else None
                pinned_rules=dataclasses.asdict(pinned.rules) if pinned else None
                if CFG.get('hours') is not None:
                    require(c.first_failed_at is not None and c.payment_rules_version==CFG['expectedRuleVersion'],'Missing recorded failure or pinned rule version mismatch')
                    require(str(c.status)=='succeeded' or c.last_failure_class=='needs_new_method','Pending/automatic-retry charges are not supported by this reminder-only probe')
                    clock=c.first_failed_at+dt.timedelta(hours=CFG['hours'])
                    tick=await run_tick(now=clock,charges=Scoped(session,c.entry_id),rules=SqlPaymentRules(session),entries=SqlEventStore(session),commands=no_payment_commands,publish=OutboxPublisher(session),isolated=session.begin_nested)
                    require(tick.failed==0 and tick.retries==0,'Unexpected worker failure or execute command; transaction rolled back')
                    await session.refresh(c)
                result.append({'environment':CFG['environment'],'mode':'reminders_only','entryId':str(c.entry_id),'eventId':str(v.id),'eventName':v.name,'pinnedRules':pinned_rules,'actualTime':dt.datetime.now(dt.UTC).isoformat(),'fixtureClock':clock.isoformat() if clock else None,'before':before,'tick':dataclasses.asdict(tick) if tick else None,'after':snap(c)})
        print('QA_RESULT_BASE64:'+base64.b64encode(json.dumps(result).encode()).decode()+':QA_RESULT_END')
    finally:
        await engine.dispose()
asyncio.run(main())

