import asyncio,base64,datetime as dt,json,uuid
from sqlalchemy import select,or_
from wsl_service_core.settings import Settings
from wsl_service_core.db.session import build_engine,session_factory
from wsl_service_core.db.org import bind_org
from notification.infrastructure.persistence.models.email import Email
from notification.infrastructure.persistence.models.email_delivery import EmailDelivery
async def main():
    settings=Settings();assert settings.env=='dev';engine=build_engine(settings)
    try:
        async with session_factory(engine)() as session,session.begin():
            bind_org(session,uuid.UUID('01a0e312-0167-774a-a4f5-ce5bb4e80824'))
            q=select(Email,EmailDelivery).outerjoin(EmailDelivery,EmailDelivery.email_id==Email.id).where(Email.recipient=='heavy-actually@btj5keea.mailosaur.net',Email.template_key=='competition.entry.payment_action_required',or_(Email.subject.contains('QA Full recovery reminders 1792593431785'),Email.subject.contains('QA Full expiry reminders 1792593451679'))).order_by(Email.created_at)
            rows=(await session.execute(q)).all()
            out=[{'emailId':str(e.id),'requestId':e.request_id,'recipient':e.recipient,'template':e.template_key,'subject':e.subject,'createdAt':e.created_at.isoformat(),'status':str(d.status) if d else None,'providerMessageId':d.provider_message_id if d else None,'failureReason':d.failure_reason if d else None} for e,d in rows]
            assert len(out)==7,f'Expected 7 payment notifications, got {len(out)}'
            assert all(x['status']=='sent' and x['providerMessageId'] for x in out),'A delivery was not sent'
        print('QA_RESULT_BASE64:'+base64.b64encode(json.dumps(out).encode()).decode()+':QA_RESULT_END')
    finally:
        await engine.dispose()
asyncio.run(main())

