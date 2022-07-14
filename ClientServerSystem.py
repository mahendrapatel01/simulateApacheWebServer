from Server import Server
from Clients import Clients
from Request import Request
from RandomVarGenerator import RandomVarGenerator


class ClientServerSystem:
    def __init__(self, noOfCores, noOfThreads, buffSize, noOfClients, thinkTime, timeQuantum, contextSwitchOverhead):
        self.server = Server(noOfCores, noOfThreads, buffSize, timeQuantum, contextSwitchOverhead)
        self.clients = Clients(noOfClients, thinkTime)
        self.clientThreadMap = {}
        self.clientRequestMap = {}
        self.initialize_requests()

    def initialize_requests(self):
        for clientId in range(self.clients.noOfClients):
            request = Request(clientId, 0, "RequestBuffer", float('inf'), float('inf'))
            self.clientRequestMap[clientId] = request
