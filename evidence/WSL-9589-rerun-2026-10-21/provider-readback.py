import asyncio,base64,json,uuid
from sqlalchemy import select
from payment.config import Settings
from payment.infrastructure.persistence.models.deferred_charge import DeferredCharge
from wsl_service_core.db.session import build_engine,session_factory
from wsl_service_core.db.org import bind_org
import stripe
async def main():
    settings=Settings()
    assert settings.env=='dev'
    assert settings.stripe.api_key.startswith(('sk_test_','rk_test_'))
    engine=build_engine(settings)
    try:
        async with session_factory(engine)() as session,session.begin():
            bind_org(session,uuid.UUID('01a0e312-0167-774a-a4f5-ce5bb4e80824'))
            refs=['01a1601b-fb63-77d4-b2e1-f51be6a04975','01a1601e-c722-75bf-8254-a9b33c50120c']
            rows=list(await session.scalars(select(DeferredCharge).where(DeferredCharge.reference_id.in_(refs))))
            assert len(rows)==2
            client=stripe.StripeClient(settings.stripe.api_key,stripe_version=settings.stripe.api_version)
            out=[]
            for row in rows:
                d={k:str(getattr(row,k)) if getattr(row,k) is not None else None for k in ['id','reference_id','status','amount_minor','currency','attempt_count','provider_payment_intent_id','failure_class','decline_code','last_attempt_at','last_event_at']}
                if row.provider_payment_intent_id:
                    pi=await client.v1.payment_intents.retrieve_async(row.provider_payment_intent_id)
                    assert pi.livemode is False
                    d['stripe']={k:getattr(pi,k,None) for k in ['id','status','livemode','amount','amount_received','currency','created','latest_charge']}
                out.append(d)
        print('QA_RESULT_BASE64:'+base64.b64encode(json.dumps(out).encode()).decode()+':QA_RESULT_END')
    finally:
        await engine.dispose()
asyncio.run(main())
