from queue import Queue


class CpuCore:
    def __init__(self, status, timeQuantum, contextSwitchOverhead):
        self.jobQueue = Queue()
        self.status = status
        self.timeQuantum = timeQuantum
        self.contextSwitchOverhead = contextSwitchOverhead
