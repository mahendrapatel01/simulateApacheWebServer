class Event:
    def __init__(self, timeStamp, eventType, clientId):
        self.timeStamp = timeStamp
        self.eventType = eventType
        self.clientId = clientId

    def __lt__(self, other):
        return self.timeStamp < other.timeStamp

    def __repr__(self):
        return "Time Stamp = "+str(self.timeStamp)+"\tEventType = "+self.eventType+"\tClientId = "+str(self.clientId)
