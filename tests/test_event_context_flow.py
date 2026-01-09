# tests/test_event_context_flow.py

from core.event_context import EventContext


def test_full_event_lifecycle():
    event = EventContext()

    assert event.active is False

    event.arm(
        detector="detector",
        direction="BUY",
        flip_direction="SELL",
        tp=1.25,
        session="LONDON",
    )

    assert event.active is True
    assert event.allow_primary is True

    event.primary_placed(ticket=123)
    assert event.allow_primary is False
    assert event.allow_flip is True

    event.flip_placed()
    event.resolve()

    assert event.active is False
    assert event.allow_primary is False
    assert event.allow_flip is False
