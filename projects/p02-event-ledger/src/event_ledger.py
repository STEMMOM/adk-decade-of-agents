import time
import uuid


def now_ts():
    return time.strftime("%Y-%m-%d %H:%M:%S")


class EventLedger:
    """
    A simple append-only event ledger.
    Each event is a dict with:
    - type
    - data
    - timestamp
    """

    def __init__(self):
        self.events = []

    def add(self, event_type: str, **kwargs):
        event = {
            "type": event_type,
            "timestamp": now_ts(),
            "data": kwargs,
        }
        self.events.append(event)

    def dump(self):
        return self.events


class Session:
    """
    A session encapsulates:
    - session_id
    - event ledger
    - an agent instance
    """

    def __init__(self, agent):
        self.session_id = str(uuid.uuid4())
        self.ledger = EventLedger()
        self.agent = agent
