import enum


class EventType(enum.Enum):
    Arrival = 1
    ContextSwitch = 2
    Departure = 3
