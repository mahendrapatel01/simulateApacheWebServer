class Request:
    def __init__(self, clienId, arrivalTime, location, remainingServiceTime, timeOut):
        self.clientId = clienId
        self.arrivalTime = arrivalTime
        self.location = location
        self.serviceTime = remainingServiceTime
        self.remainingServiceTime = remainingServiceTime
        self.timeOut = timeOut

    def __repr__(self):
        return "Request : ClientId = " + str(self.clientId) + "\tArrivalTime = " + str(
            self.arrivalTime) + "\tLocation = " + str(
            self.location + "\tRemaining service time = " + str(self.remainingServiceTime) + "\tTime out = " + str(
                self.timeOut))
