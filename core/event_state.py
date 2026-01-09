# core/event_state.py

class EventState:
    IDLE = "IDLE"
    ACTIVE = "ACTIVE"
    PRIMARY_PLACED = "PRIMARY_PLACED"
    FLIP_PLACED = "FLIP_PLACED"
    RESOLVED = "RESOLVED"


class EventContext:
    def __init__(self):
        self.state = EventState.IDLE
        self.direction = None
        self.tp_level = None
        self.session = None

        self.trade_taken = False
        self.flip_used = False

    # ---------------------------
    def arm(self, direction, tp_level, session):
        if self.state != EventState.IDLE:
            return False

        self.state = EventState.ACTIVE
        self.direction = direction
        self.tp_level = tp_level
        self.session = session
        return True

    # ---------------------------
    def primary_placed(self):
        self.state = EventState.PRIMARY_PLACED
        self.trade_taken = True

    # ---------------------------
    def flip_placed(self):
        self.state = EventState.FLIP_PLACED
        self.flip_used = True

    # ---------------------------
    def resolve(self):
        self.state = EventState.RESOLVED

    # ---------------------------
    def reset(self):
        self.__init__()
