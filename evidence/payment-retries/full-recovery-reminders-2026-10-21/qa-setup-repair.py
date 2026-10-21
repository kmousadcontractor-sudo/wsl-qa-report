import json
from django.db import transaction
from infrastructure.contacts.models import AthleteContact
from infrastructure.card_setup.models import CardSetup
with transaction.atomic():
    contact=AthleteContact.objects.get(athlete_id='01a15ec1-e5d0-74a6-b63f-536f85f9567f')
    assert contact.account_holder_email=='heavy-actually@btj5keea.mailosaur.net'
    row=CardSetup.objects.select_for_update().get(id='01a15ec2-beb4-754e-a50a-11bb254dae05')
    assert row.user_id==contact.account_holder_user_id
    assert row.org_id==contact.org_id
    before={'setupId':str(row.id),'state':row.state,'providerAttempt':row.provider_attempt_id,'savedPaymentMethodId':str(row.saved_payment_method_id) if row.saved_payment_method_id else None}
    assert row.state=='attempt_ready' and row.saved_payment_method_id is None
    row.state='expired'
    row.last_error='expired'
    row.save(update_fields=['state','last_error','updated_at'])
    print(json.dumps({'qaFixtureOnly':True,'reason':'Expire stuck QA setup to permit a fresh provider attempt; no application fix','before':before,'after':{'setupId':str(row.id),'state':row.state},'orgId':str(contact.org_id)}))
