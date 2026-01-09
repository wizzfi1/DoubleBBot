from core.event_state import EventContext, EventState


def test_event_locks_on_first_sweep():
    ctx = EventContext()

    assert ctx.arm("BUY", 1.2000, "LONDON") is True
    assert ctx.state == EventState.ACTIVE

    # Attempt to arm opposite event
    assert ctx.arm("SELL", 1.3000, "LONDON") is False
    assert ctx.direction == "BUY"


def test_event_unlocks_only_after_resolution():
    ctx = EventContext()

    ctx.arm("SELL", 1.1000, "NY")
    ctx.primary_placed()

    assert ctx.state == EventState.PRIMARY_PLACED

    ctx.resolve()
    assert ctx.state == EventState.RESOLVED

    ctx.reset()
    assert ctx.state == EventState.IDLE


def test_flip_does_not_unlock_event():
    ctx = EventContext()

    ctx.arm("BUY", 1.3000, "LONDON")
    ctx.primary_placed()
    ctx.flip_placed()

    assert ctx.state == EventState.FLIP_PLACED

    # Still locked
    assert ctx.arm("SELL", 1.1000, "LONDON") is False
