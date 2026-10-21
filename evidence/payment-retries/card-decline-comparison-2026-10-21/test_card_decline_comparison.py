"""Actual classification -> actual scheduler; isolated stores, no provider calls."""
import pytest
from payment.infrastructure.gateways.stripe.declines import classify
from .test_retry_matrix_lifecycle import world

@pytest.mark.parametrize('code,expected,retries',[
    ('generic_decline','needs_new_method',0),
    ('insufficient_funds','retryable',1),
])
async def test_card_decline_behavior(code,expected,retries):
    failure=classify(code='card_declined',decline_code=code)
    assert failure.value==expected
    w=await world()
    await w.decline(0,failure.value)
    first=await w.tick(24)
    assert first.retries==retries
    assert first.notices==1
    if retries:
        await w.decline(24.001,failure.value)
    second=await w.tick(72)
    assert second.retries==retries
    assert second.notices==1
    if retries:
        await w.decline(72.001,failure.value)
    third=await w.tick(120)
    final=await w.tick(168)
    assert third.retries==0
    assert third.notices==1
    assert final.retries==0
    assert final.notices==1
    assert final.flagged==1
    print(f'{code}: class={failure.value}; automatic_executes={len(w.commands.sent)}; notice_events={sum(1 for e in w.notices() if e.reason=="notice")}; flagged={final.flagged}')
    assert len(w.commands.sent)==retries*2

