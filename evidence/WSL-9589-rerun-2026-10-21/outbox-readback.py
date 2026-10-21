import asyncio,base64,json,uuid
from sqlalchemy import select
from payment.config import Settings
from wsl_service_core.db.session import build_engine,session_factory
from wsl_service_core.db.org import bind_org
from wsl_service_core.db.models import OutboxMessage
async def main():
    settings=Settings()
    assert settings.env=='dev'
    engine=build_engine(settings)
    try:
        async with session_factory(engine)() as s,s.begin():
            bind_org(s,uuid.UUID('01a0e312-0167-774a-a4f5-ce5bb4e80824'))
            refs=['01a1601b-fb63-77d4-b2e1-f51be6a04975','01a1601e-c722-75bf-8254-a9b33c50120c']
            rows=list(await s.scalars(select(OutboxMessage).where(OutboxMessage.subject=='evt.payment.paid',OutboxMessage.payload['reference_id'].astext.in_(refs))))
            out=[{**{k:str(getattr(r,k,None)) if getattr(r,k,None) is not None else None for k in ['id','subject','created_at','published_at','attempts','last_error']},'reference_id':r.payload.get('reference_id')} for r in rows]
            print('QA_RESULT_BASE64:'+base64.b64encode(json.dumps({'outbox':out}).encode()).decode()+':QA_RESULT_END')
    finally:
        await engine.dispose()
asyncio.run(main())
