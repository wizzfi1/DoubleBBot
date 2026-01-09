# core/event_context.py

class EventContext:
    def __init__(self):
        self.reset()

    # ---------------------------
    # STATE RESET
    # ---------------------------
    def reset(self):
        self.active = False

        self.detector = None
        self.direction = None
        self.flip_direction = None
        self.tp_level = None
        self.session = None

        self.primary_ticket = None
        self.flip_used = False

        self.allow_primary = False
        self.allow_flip = False

    # ---------------------------
    # ARM EVENT
    # ---------------------------
    def arm(self, detector, direction, flip_direction, tp, session):
        self.active = True

        self.detector = detector
        self.direction = direction
        self.flip_direction = flip_direction
        self.tp_level = tp
        self.session = session

        self.primary_ticket = None
        self.flip_used = False

        self.allow_primary = True
        self.allow_flip = False

    # ---------------------------
    # PRIMARY PLACED
    # ---------------------------
    def primary_placed(self, ticket: int):
        self.primary_ticket = ticket

        # 🔒 stop further primaries
        self.allow_primary = False

        # 🔓 enable flip monitoring
        self.allow_flip = True

    # ---------------------------
    # FLIP PLACED
    # ---------------------------
    def flip_placed(self):
        self.flip_used = True
        self.allow_flip = False

    # ---------------------------
    # RESOLVE EVENT
    # ---------------------------
    def resolve(self):
        self.reset()
