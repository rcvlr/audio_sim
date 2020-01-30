"""
@file    mainThread.py
@author  Riccardo Cavallari
@date    2019.10.14

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

Next steps: 
    - add asynchronous sampling rate conversion
    - add channel model
    - add GUI for plotting and playing sound
"""

import threading
import time
import packet
import random
import wave
from array import array
from collections import deque
from vcd import VCDWriter

PROB_THRESHOLD = 2
FRAMES_PER_PACKET = 160         # mono, 10 ms @ 16 kHz sampl. rate
FRAME_INTERVAL = 10e-3
TRANSPORT_INTERVAL = 7.5e-3 #FRAME_INTERVAL
IN_FIFO_LEN = 10
OUT_FIFO_LEN = IN_FIFO_LEN
RADIO_FIFO_LEN = 10

# packet + ack + 2*Tifs
# TODO: use real numbers and dependent on packet len and PHY
PACKET_DURATION = (800e-6 + 300e-6)
CONNECTION_EVENT = 0.75 * TRANSPORT_INTERVAL
MAX_TX_CONN_EVENT = int(CONNECTION_EVENT/PACKET_DURATION)

underflowCnt = 0
overflowCnt = 0
radioOverflow = 0

vcdFile = open("out.vcd", "w")
vcd = VCDWriter(vcdFile, timescale='1 ns')
consWire = vcd.register_var('libsigrok', 'consumer', 'wire', size=1, ident='!')
bleWire = vcd.register_var('libsigrok', 'BLE', 'wire', size=1, ident='$')
start = time.perf_counter_ns()

# FIFO to hold packet ready to bt tx-ed or retx-ed
fifoRadio = deque([], RADIO_FIFO_LEN)


def createPacket(payload):
    """ Create a packet with a given payload """

    pkt = packet.Packet(payload)
    return pkt


def producerCallback(fifo, wf, e):
    """ read frames from the wav input file and add it to the input FIFO.
        This represents the output of the codec """

    # add packets to the input FIFO...
    payload = wf.readframes(FRAMES_PER_PACKET)

    # ... until the wav file is not over
    while (payload != b''):
        packet = createPacket(payload)
        fifo.append(packet)
        # print("Producer", packet.seqNum)
        time.sleep(FRAME_INTERVAL)
        payload = wf.readframes(FRAMES_PER_PACKET)

    # signal to the other threads that we are done
    e.set()


def consumerCallback(fifo, file, e):
    """ Get a packet from output FIFO and reproduce it """

    global underflowCnt

    while True:
        try:
            packet = fifo.popleft()
            #print("Consumer", packet.seqNum)
            
            # TODO: don't write a file, store payloads in some data structure
            # and use a paudio callback to retrieve data from that data
            # structure and reproduce it.
            file.writeframes(packet.payload)

        except IndexError:                                  # no packet in the FIFO!
            if e.is_set():
                return
            file.writeframes(bytes(2*FRAMES_PER_PACKET))    # write 0s
            underflowCnt += 1
            print("Output FIFO is empty, consumer underflow!")

        end = time.perf_counter_ns()
        timestamp = end - start
        vcd.change(consWire, timestamp, 0)
        vcd.change(consWire, timestamp + 1000, 1)
        vcd.change(consWire, timestamp + 2000, 0)

        time.sleep(FRAME_INTERVAL)


def aclTransportCallback(fifoIn, fifoOut, e):
    """ Simulate an ACL tranport between a master and a slave. Packets are 
    retransmitted until they are successfully acknowledged. Packets are taken
    from fifoIn and put in fifoOut if successfully transmitted. """

    global fifoRadio, radioOverflow

    while True:
        try:
            # get the packet scheduled for this event
            schedPacket = fifoIn.popleft()
            schedPacket.txAttemps = packet.FLUSH_TIMEOUT_INF

            if fifoRadio.maxlen == len(fifoRadio):
                radioOverflow += 1

            fifoRadio.append(schedPacket)

        except IndexError:
            print("Input FIFO is empty!")

        # schedule packet transmission slots for this connection event
        for _ in range(min(len(fifoRadio), MAX_TX_CONN_EVENT)):
            txCallback(fifoRadio, fifoOut)
            #time.sleep(PACKET_DURATION)
        
        if e.is_set():
            return

        end = time.perf_counter_ns()
        timestamp = end - start
        vcd.change(bleWire, timestamp, 0)
        vcd.change(bleWire, timestamp + 1000, 1)
        vcd.change(bleWire, timestamp + 2000, 0)

        time.sleep(TRANSPORT_INTERVAL)


def txCallback(fifoIn, fifoOut):
    """ Get a packet from the input FIFO and send it over the air. The packet
    is successfully transmitted with probability PROB_THRESHOLD """

    global overflowCnt

    try:
        packet = fifoIn.popleft()

        if (random.random() < PROB_THRESHOLD):
            if fifoOut.maxlen == len(fifoOut):
                overflowCnt += 1

            print("Packet", packet.seqNum, "OK, re-tx", packet.txAttemps)
            fifoOut.append(packet)
        else:
            print("Packet", packet.seqNum, "Error")

            # decrease txAttempts and put the packet back in the FIFO
            packet.txAttemps -= 1
            if (packet.txAttemps):
                fifoIn.appendleft(packet)
            else:
                del packet

    except IndexError:
        print("Radio FIFO is empty!")


def main():
    """ Main function of the simulator """

    # input and output FIFOs
    fifoIn = deque([], IN_FIFO_LEN)
    fifoOut = deque([], OUT_FIFO_LEN)

    # input wave file
    wf = wave.open('440Hz.wav', 'rb')

    # output wave file
    wof = wave.open('output.wav', 'wb')
    wof.setnchannels(1)
    wof.setsampwidth(2)
    wof.setframerate(16000)

    # event to signal the consumer to stop consuming
    e = threading.Event()

    # Producer thread
    producer = threading.Thread(target=producerCallback,
                                args=(fifoIn, wf, e))

    # Bluetooth thread
    bluetooth = threading.Thread(target=aclTransportCallback,
                                 args=(fifoIn, fifoOut, e))

    # Consumer thread
    consumer = threading.Thread(target=consumerCallback,
                                args=(fifoOut, wof, e))

    producer.start()
    bluetooth.start()
    time.sleep((OUT_FIFO_LEN/2)*FRAME_INTERVAL)    # wait until the fifo is full
    consumer.start()

    # wait until all threads terminate
    producer.join()
    bluetooth.join()
    consumer.join()

    print("Consumer underflow:", underflowCnt)
    print("Consumer overflow:", overflowCnt)
    print("Radio overflow:", radioOverflow)

    wof.close()
    vcd.close()
    vcdFile.close()


if __name__ == '__main__':
    main()
