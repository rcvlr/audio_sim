"""
@file    main.py
@author  Riccardo Cavallari
@date    2019.10.01

Simulation of
"""

import scheduler
import packet
from array import array
from collections import deque

fifoIn = deque([])
fifoOut = deque([])

def printTime():
    """ print current time """
    print(scheduler.Scheduler.clockTime,'-'*50)

def createPacket(payload):
    pkt = packet.Packet(payload)
    return pkt

def sendPacket(fifo):
    """ Get a packet from the queue (FIFO) and send it """
    try:
        packet = fifo.popleft()
        print(packet.seqNum)
    except IndexError:
        print("Input FIFO is empty!")

        

def main():
    """ Main function of the simulator """

    # add packets to the input FIFO
    for i in range(5):
        packet = createPacket(array('L', [x*i for x in range(4)]))
        fifoIn.append(packet)

    # set the simulation duration in seconds
    scheduler.setSimDuration(10)

    #-------------------------------------------------------------------------#
    # Add events to the scheduler                                             #
    # events are executed in order of                                         #
    # addition                                                                #
    #-------------------------------------------------------------------------#

    # print time at the beginning of every slot
    #event = scheduler.Event(0, 1, printTime, [])
    #scheduler.addEvent(event)

    event = scheduler.Event(0, 1, sendPacket, [fifoIn])
    scheduler.addEvent(event)

    # START the simulation
    scheduler.runEvents()

    # end of the simulation
    scheduler.simDone()

if __name__ == '__main__': main()