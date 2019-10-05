"""
@file    main.py
@author  Riccardo Cavallari
@date    2019.10.01

Simulation of a system composed of
- a producer of audio packets
- a lossy medium 
- a consumer of audio packet

The producer generates packets with period T_in; packets are transmitted to
on the medium with probability P and with period T_m; consumer reproduces packets
with period T_out. All three timers are subject to precisioin error and are not
alligned. 

Goals of the simulation are, evaluate latency and buffer overflow/underflow
at the consumer. 

Assumption: 
    - no retransmissions
    - sine wave 
    - no channel model, just uniform probability P to correctly receive the 
    packet

Next steps: 
    - add retransmissions, 
    - use real audio from a codec
    - add asynchronous sampling rate conversion
    - add channel model
    - add interference
    - add GUI for plotting and playing sound
"""

import scheduler
import packet
import random
import wave
from array import array
from collections import deque

PROB_THRESHOLD = 1.1
FRAMES_PER_PACKET = 160         # mono, 10 ms @ 16 kHz sampl. rate
FRAME_INTERVAL = 10e-3
IN_FIFO_LEN = 10
OUT_FIFO_LEN = IN_FIFO_LEN


def printTime():
    """ print current time """

    print(scheduler.Scheduler.clockTime,'-'*50)


def createPacket(payload):
    """ Create a packet with a given payload """
    
    pkt = packet.Packet(payload)
    return pkt


def producerCallback(fifo, wf):
    """ read frames from the wav input file and add it to the input FIFO.
        This represents the output of the codec """

    # add packets to the input FIFO
    payload = wf.readframes(FRAMES_PER_PACKET)

    if (payload != b''):
        packet = createPacket(payload)
    else:
        packet = createPacket(bytes(2*FRAMES_PER_PACKET))

    fifo.append(packet)


def transportCallaback(fifoIn, fifoOut):
    """ Get a packet from the input FIFO and send it over the air """

    try:
        packet = fifoIn.popleft()
        if (random.random() < PROB_THRESHOLD):
            fifoOut.append(packet)
            print('Sending packet', packet.seqNum)
        else:
            print("packet error")
    except IndexError:
        print("Input FIFO is empty!")


def consumerCallback(fifo, file):
    """ Get a packet from output FIFO and reproduce it """

    try:
        sample = fifo.popleft()
        # print(sample.seqNum)
        file.writeframes(sample.payload)
    except IndexError:
        file.writeframes(bytes(2*FRAMES_PER_PACKET))
        print("Output FIFO is empty!")


def main():
    """ Main function of the simulator """

    # input and output FIFOs
    fifoIn = deque([], IN_FIFO_LEN)
    fifoOut = deque([], OUT_FIFO_LEN)

    # input wave file
    wf = wave.open('440Hz.wav', 'rb')

    # output wave file
    wof =  wave.open('output.wav', 'wb')
    wof.setnchannels(1)
    wof.setsampwidth(2)
    wof.setframerate(16000)
    
    # for i in range(5):
    #     packet = createPacket(array('L', [x*i for x in range(4)]))
    #     fifoIn.append(packet)

    # set the simulation duration in seconds
    scheduler.setSimDuration(10)

    # producer adds packet to the input FIFO
    event = scheduler.Event(0, FRAME_INTERVAL, producerCallback, 
                            [fifoIn, wf])
    scheduler.addEvent(event)

    # the transport sends packets on the medium and store them in a (finte) 
    # output FIFO
    event = scheduler.Event(2*FRAME_INTERVAL, FRAME_INTERVAL, 
                            transportCallaback, [fifoIn, fifoOut])
    scheduler.addEvent(event)        

    # consumer takes packets from the output FIFO and writes them to a wave file 
    event = scheduler.Event(IN_FIFO_LEN*FRAME_INTERVAL, FRAME_INTERVAL, 
                            consumerCallback, [fifoOut, wof])
    scheduler.addEvent(event)

    # START the simulation
    scheduler.runEvents()

    # end of the simulation
    scheduler.simDone()

    wof.close()

if __name__ == '__main__': main()