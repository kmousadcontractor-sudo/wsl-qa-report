"""Application-level impact probes; explicit clocks, no real provider charge."""
import pytest
from .test_retry_matrix_lifecycle import world

@pytest.mark.parametrize('answer_delay_ms',[0,1])
async def test_completed_offset_full_worker_sequence(answer_delay_ms):
    w=await world()
    await w.decline(0)
    first=await w.tick(24)
    assert first.retries==1
    await w.decline(24+answer_delay_ms/3600000)
    due=w.now_row.next_attempt_at
    second=await w.tick(24+answer_delay_ms/3600000)
    print(f'answer_delay_ms={answer_delay_ms}; next_due={due}; second_tick_retries={second.retries}; execute_commands={len(w.commands.sent)}')
    assert second.retries==0, 'Completed 24h retry was dispatched again after its same-instant failure result'
