import copy
import heapq

from ClientServerSystem import ClientServerSystem
from Event import Event
from EventType import EventType
from Metrics import Metrics
from Request import Request
from RandomVarGenerator import RandomVarGenerator
import json
import numpy as np
import scipy.stats as st


class Simulator:
    def __init__(self, noOfCores, noOfThreads, buffSize, noOfClients, thinkTime, simulationTIme, timeQuantum,
                 contextSwitchOverhead, meanServiceTime, meanTimeout, servTimeDist, debug):
        self.metrics = Metrics()
        self.system = ClientServerSystem(noOfCores, noOfThreads, buffSize, noOfClients, thinkTime, timeQuantum,
                                         contextSwitchOverhead)
        self.meanServiceTime = meanServiceTime
        self.meanTimeout = meanTimeout
        self.prevTimeStamp = 0
        self.simulationTIme = simulationTIme
        self.dropCounter = 0
        self.goodCounter = 0
        self.badCounter = 0
        self.totalCpuUtilArea = 0
        self.totalResponseTime = 0
        self.randomVarGenerator = RandomVarGenerator()
        self.eventQueue = []
        heapq.heapify(self.eventQueue)
        self.initialise_event_queue(noOfClients)
        self.responseTimeArr = []
        self.servTimeDist = servTimeDist
        self.debug = debug

    def initialise_event_queue(self, noOfClients):
        for event in EventType:
            for clientId in range(noOfClients):
                if event.name == "Arrival":
                    heapq.heappush(self.eventQueue, Event(0, event.name, clientId))

    # Runs the simulation loop until simulation timer expires
    def run_simulation(self):
        while True:
            event_to_be_processed = self.eventQueue[0]
            heapq.heappop(self.eventQueue)
            # print(str(event_to_be_processed))
            # print("Time Stamp = " + str(self.prevTimeStamp))
            if event_to_be_processed.timeStamp >= self.simulationTIme:
                self.print_metrics()
                break
            self.calc_cpu_util_area(self.prevTimeStamp, event_to_be_processed.timeStamp)
            if event_to_be_processed.eventType == "Arrival":
                self.arrival_handler(event_to_be_processed)
            elif event_to_be_processed.eventType == "ContextSwitch":
                self.context_switch_handler(event_to_be_processed)
            elif event_to_be_processed.eventType == "Departure":
                self.departure_handler(event_to_be_processed)

            else:
                raise Exception("Invalid Event")
            self.prevTimeStamp = event_to_be_processed.timeStamp

    def print_metrics(self):
        self.metrics.utilization = self.totalCpuUtilArea / self.simulationTIme
        self.metrics.dropRate = self.dropCounter * 1000 / self.simulationTIme
        self.metrics.goodPut = self.goodCounter * 1000 / self.simulationTIme
        self.metrics.badput = self.badCounter * 1000 / self.simulationTIme
        self.metrics.responseTime = self.totalResponseTime / (self.goodCounter + self.badCounter)
        self.metrics.throughPut = (self.metrics.goodPut + self.metrics.badput)

        if self.debug != 1:
            return
        print("No of departures =" + str(self.badCounter + self.goodCounter))
        print("Average Response time =" + str(self.totalResponseTime / (self.goodCounter + self.badCounter)))
        print("Good put = " + str(self.metrics.goodPut))
        print("Bad put = " + str(self.metrics.badput))
        print("Utilization = " + str(self.metrics.utilization))
        print("Drop Rate = " + str(self.metrics.dropRate))
        print("Throughput = " + str(self.metrics.throughPut))

    # calculates total cpu utilization area
    def calc_cpu_util_area(self, prev_time_stamp, curr_time_stamp):
        total = 0
        for core in self.system.server.cpuCores:
            if core.status == 'Busy':
                total += (curr_time_stamp - prev_time_stamp)

        self.totalCpuUtilArea += (total / self.system.server.noOfCores)

    # Handles Arrival events
    def arrival_handler(self, event):
        req_buffer = self.system.server.requestBuffer
        request = self.system.clientRequestMap[event.clientId]

        request.arrivalTime = event.timeStamp
        if self.servTimeDist == "exp":
            request.serviceTime = self.randomVarGenerator.exponential(168)
        elif self.servTimeDist == "unf":
            request.serviceTime = self.randomVarGenerator.uniform(150, 180)
        else:
            request.serviceTime = 168
        request.remainingServiceTime = request.serviceTime
        request.timeOut = self.randomVarGenerator.erlang(self.meanTimeout, 500)

        # If buffer is full request will be dropped and next arrival event will be scheduled
        if req_buffer.full():
            self.dropCounter += 1
            # scheduling next arrival by adding Think time
            heapq.heappush(self.eventQueue,
                           Event(event.timeStamp + self.system.clients.thinkTime,
                                 EventType.Arrival.name, request.clientId))
        # Request will be added to buffer and will be assigned to a free thread
        else:
            req_buffer.put(request)
            idle_thread = self.system.server.get_idle_thread()
            if idle_thread is not None:
                # print("Idle threadId = " + str(idle_thread.threadId))
                self.system.clientThreadMap[event.clientId] = idle_thread.threadId
                cpu_core = self.system.server.cpuCores[idle_thread.threadId % self.system.server.noOfCores]
                cpu_core.jobQueue.put(request)
                req_buffer.get()
                idle_thread.status = "Busy"
                if cpu_core.status == "Idle":
                    cpu_core.status = "Busy"
                    if request.remainingServiceTime > cpu_core.timeQuantum:
                        # schedule context switch by adding timequantum and contextswitch overhead
                        heapq.heappush(self.eventQueue,
                                       Event(event.timeStamp + cpu_core.timeQuantum + cpu_core.contextSwitchOverhead,
                                             EventType.ContextSwitch.name, request.clientId))

                    else:
                        # schedule departure by adding remainingServiceTime
                        heapq.heappush(self.eventQueue,
                                       Event(event.timeStamp + request.remainingServiceTime, EventType.Departure.name,
                                             request.clientId))

    # Handles Arrival events
    def departure_handler(self, event):
        request = self.system.clientRequestMap[event.clientId]
        threadId = self.system.clientThreadMap[event.clientId]
        cpu_core = self.system.server.cpuCores[threadId % self.system.server.noOfCores]
        cpu_core.jobQueue.get()
        if cpu_core.jobQueue.empty() is not True:
            next_request_to_be_executed = cpu_core.jobQueue.queue[0]
            if next_request_to_be_executed.remainingServiceTime > cpu_core.timeQuantum:
                # schedule context switch for the next_request_to_be_executed  by adding timequantum and contextswitch overhead
                heapq.heappush(self.eventQueue,
                               Event(event.timeStamp + cpu_core.timeQuantum + cpu_core.contextSwitchOverhead,
                                     EventType.ContextSwitch.name,
                                     next_request_to_be_executed.clientId))
            else:
                # schedule departure of this next_request_to_be_executed  by adding remainingServiceTime
                heapq.heappush(self.eventQueue,
                               Event(event.timeStamp + next_request_to_be_executed.remainingServiceTime,
                                     EventType.Departure.name,
                                     next_request_to_be_executed.clientId))
        else:
            cpu_core.status = "Idle"

        req_response_time = event.timeStamp - request.arrivalTime
        self.responseTimeArr.append(req_response_time)
        # print("Service Time = " + str(request.serviceTime))
        # print("Response Time for client Id " + str(event.clientId) + " = " + str(req_response_time))
        self.totalResponseTime += req_response_time
        if req_response_time > request.timeOut:
            self.badCounter += 1
        else:
            self.goodCounter += 1

        # Schedule new arrival of this client by adding think time to current timestamp
        heapq.heappush(self.eventQueue,
                       Event(event.timeStamp + self.system.clients.thinkTime,
                             EventType.Arrival.name,
                             event.clientId))

        # picking next request if any from request buffer queue
        if self.system.server.requestBuffer.qsize() > 0:
            next_request_to_be_picked = self.system.server.requestBuffer.get()
            cpu_core = self.system.server.cpuCores[threadId % self.system.server.noOfCores]
            self.system.clientThreadMap[next_request_to_be_picked.clientId] = threadId
            cpu_core.jobQueue.put(next_request_to_be_picked)
            if cpu_core.status == "Idle":
                cpu_core.status = "Busy"
                if next_request_to_be_picked.remainingServiceTime > cpu_core.timeQuantum:
                    # schedule context switch of this request by adding timequantum and contextswitch overhead
                    heapq.heappush(self.eventQueue,
                                   Event(event.timeStamp + cpu_core.timeQuantum + cpu_core.contextSwitchOverhead,
                                         EventType.ContextSwitch.name,
                                         next_request_to_be_picked.clientId))
                else:
                    # schedule departure of this request  by adding remainingServiceTime
                    heapq.heappush(self.eventQueue,
                                   Event(event.timeStamp + next_request_to_be_picked.remainingServiceTime,
                                         EventType.Departure.name,
                                         next_request_to_be_picked.clientId))
        else:
            # update status of thread as idle if no requests in buffer queue
            self.system.server.workerThreads[threadId].status = "Idle"

    # Handles context switch events
    def context_switch_handler(self, event):
        request = self.system.clientRequestMap[event.clientId]
        threadId = self.system.clientThreadMap[event.clientId]
        cpu_core = self.system.server.cpuCores[threadId % self.system.server.noOfCores]
        request.remainingServiceTime -= cpu_core.timeQuantum

        if cpu_core.jobQueue.qsize() <= 0:
            raise Exception("Invalid Scenario")
        cpu_core.jobQueue.get()
        if cpu_core.jobQueue.empty() is not True:
            next_request_to_be_executed = cpu_core.jobQueue.queue[0]
            if next_request_to_be_executed.remainingServiceTime > cpu_core.timeQuantum:
                # schedule context switch for this next_request_to_be_executed  by adding timequantum and contextswitch overhead to current timestamp
                heapq.heappush(self.eventQueue,
                               Event(event.timeStamp + cpu_core.timeQuantum + cpu_core.contextSwitchOverhead,
                                     EventType.ContextSwitch.name,
                                     next_request_to_be_executed.clientId))
            else:
                # schedule departure of this next_request_to_be_executed  by adding remainingServiceTime
                heapq.heappush(self.eventQueue,
                               Event(event.timeStamp + next_request_to_be_executed.remainingServiceTime,
                                     EventType.Departure.name,
                                     next_request_to_be_executed.clientId))
        else:
            if request.remainingServiceTime > cpu_core.timeQuantum:
                # Set Context switch timestamp to event.timestamp+timequantum
                heapq.heappush(self.eventQueue,
                               Event(event.timeStamp + cpu_core.timeQuantum,
                                     EventType.ContextSwitch.name,
                                     request.clientId))
            else:
                # schedule departure of this request  by adding remainingServiceTime
                heapq.heappush(self.eventQueue,
                               Event(event.timeStamp + request.remainingServiceTime,
                                     EventType.Departure.name,
                                     request.clientId))
        cpu_core.jobQueue.put(request)


if __name__ == "__main__":
    input_file = open('Inputs.json', )
    input_data = json.load(input_file)

    simulator = Simulator(noOfCores=input_data["noOfCores"], noOfThreads=input_data["noOfThreads"],
                          buffSize=input_data["buffSize"], noOfClients=input_data["noOfClients"],
                          thinkTime=input_data["thinkTime"],
                          simulationTIme=input_data["simulationTIme"],
                          timeQuantum=input_data["timeQuantum"],
                          contextSwitchOverhead=input_data["contextSwitchOverhead"],
                          meanServiceTime=input_data["meanServiceTime"], meanTimeout=input_data["meanTimeout"],
                          servTimeDist=input_data["serviceTimeDistribution"], debug=input_data["debug"])

    simulator.run_simulation()
