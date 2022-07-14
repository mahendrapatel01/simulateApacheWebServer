from queue import Queue
from CpuCore import CpuCore
from WorkerThread import WorkerThread


def initialize_cores(noOfCores, timeQuantum, contextSwitchOverhead):
    return [CpuCore("Idle", timeQuantum, contextSwitchOverhead) for _ in range(noOfCores)]


def initialize_worker_threads(noOfThreads):
    return [WorkerThread(x, "Idle") for x in range(noOfThreads)]


class Server:
    def __init__(self, noOfCores, noOfThreads, buffSize, timeQuantum, contextSwitchOverhead):
        self.noOfCores = noOfCores
        self.noOfThreads = noOfThreads
        self.cpuCores = initialize_cores(noOfCores, timeQuantum, contextSwitchOverhead)
        self.workerThreads = initialize_worker_threads(noOfThreads)
        self.requestBuffer = Queue(buffSize)

    def get_idle_thread(self):
        for i in range(self.noOfThreads):
            if self.workerThreads[i].status == "Idle":
                return self.workerThreads[i]
        return None
