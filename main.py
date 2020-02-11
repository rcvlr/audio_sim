"""
@file    main.py
@author  Riccardo Cavallari
@date    2019.10.01
"""

import scheduler
import packet
import random
import wave
import gpio
from array import array
from collections import deque
from vcd import VCDWriter

PROB_THRESHOLD = 0.3
FRAMES_PER_PACKET = 160         # mono, 10 ms @ 16 kHz sampl. rate
FRAME_INTERVAL = 10e-3
CODEC_INTERVAL = FRAME_INTERVAL
IN_FIFO_LEN = 10
OUT_FIFO_LEN = IN_FIFO_LEN
RADIO_FIFO_LEN = 10

# packet + ack + 2*Tifs 
PACKET_DURATION = 0.564e-3  # subevent duration
CONNECTION_EVENT = 0.75*FRAME_INTERVAL
MAX_TX_CONN_EVENT = int(CONNECTION_EVENT/PACKET_DURATION)

underflowCnt = 0
overflowCnt = 0
radioOverflow = 0

vcdFile = open("out.vcd", "w")
vcd = VCDWriter(vcdFile, timescale='1 us')

gpio0 = gpio.Gpio(0, vcd, 'producer', '!')
gpio1 = gpio.Gpio(0, vcd, 'consumer', '$')
gpio2 = gpio.Gpio(0, vcd, 'ble', '#')

# FIFO to hold packet ready to bt tx-ed or retx-ed
fifoRadio = deque([], RADIO_FIFO_LEN)


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
    
    gpio0.toggle(scheduler.Scheduler.clockTime*1e6)


def isochronousTransportCallback(fifoIn, fifoOut):
    """ Simulate a unicast isochronous channel between a master and a slave """

    #TODO
    

def aclTransportCallback (fifoIn, fifoOut):
    """ Simulate an ACL tranport between a master and a slave. Packets are 
    retransmitted untile they are successfully acknowledged. """

    global fifoRadio, radioOverflow

    # get the packet scheduled for this event
    schedPacket = fifoIn.popleft()
    schedPacket.txAttemps = packet.FLUSH_TIMEOUT_INF

    if fifoRadio.maxlen == len(fifoRadio):
        radioOverflow += 1

    fifoRadio.append(schedPacket)

    # schedule tx slots within a connection event
    for i in range(min(len(fifoRadio), MAX_TX_CONN_EVENT)):
        event = scheduler.Event(scheduler.Scheduler.clockTime + i*PACKET_DURATION, 
                                0, txCallaback, [fifoRadio, fifoOut])
        scheduler.addEvent(event)



def txCallaback(fifoIn, fifoOut):
    """ Get a packet from the input FIFO and send it over the air """

    global overflowCnt

    try:
        packet = fifoIn.popleft()
        
        if (random.random() < PROB_THRESHOLD):
            if fifoOut.maxlen == len(fifoOut):
                overflowCnt += 1
        
            fifoOut.append(packet)

            print("Packet", packet.seqNum, "OK, re-tx", packet.txAttemps)
            gpio2.toggle(scheduler.Scheduler.clockTime*1e6)
        else:
            print("Packet", packet.seqNum, "Error")

            # decrease txAttempts and put the packet back in the FIFO
            packet.txAttemps -= 1
            if (packet.txAttemps):
                fifoIn.appendleft(packet)
            else:
                del packet

    except IndexError:
        print("Input FIFO is empty!")
        

def consumerCallback(fifo, file):
    """ Get a packet from output FIFO and reproduce it """

    global underflowCnt

    try:
        sample = fifo.popleft()
        # print(sample.seqNum)
        file.writeframes(sample.payload)
    except IndexError:
        file.writeframes(bytes(2*FRAMES_PER_PACKET))
        underflowCnt += 1
        print("Output FIFO is empty!")

    gpio1.toggle(scheduler.Scheduler.clockTime*1e6)

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
    scheduler.setSimDuration(10.1)

    # producer adds packet to the input FIFO
    event = scheduler.Event(0, CODEC_INTERVAL, producerCallback, 
                            [fifoIn, wf])
    scheduler.addEvent(event)

    # the transport sends packets on the medium and store them in a (finte) 
    # output FIFO
    event = scheduler.Event(0, FRAME_INTERVAL, 
                            aclTransportCallback, [fifoIn, fifoOut])
    scheduler.addEvent(event)        

    # consumer takes packets from the output FIFO and writes them to a wave file 
    # RSL10: 16129/16000 or 15957/16000
    event = scheduler.Event(FRAME_INTERVAL, FRAME_INTERVAL, 
                            consumerCallback, [fifoOut, wof])
    scheduler.addEvent(event)

    # START the simulation
    scheduler.runEvents()

    # end of the simulation
    scheduler.simDone()

    print("Consumer underflow:", underflowCnt)
    print("Consumer overflow:", overflowCnt)
    print("Radio overflow:", radioOverflow)

    wof.close()
    vcd.close()
    vcdFile.close()

if __name__ == '__main__': main()