# Simulation of an audio system 

Simulate an audio system composed of:

- a producer;

- a transport mechanism;

- a consumer.

The _producer_ takes an audio file, chuncks it in packets, and put them in an
input FIFO ```fifoIn```. One packet every ```FRAME_INTERVAL```.

The _transport_ takes one packet out of the input FIFO ```fifoIn``` every
```TRANSPORT_INTERVAL``` and puts them in the output FIFO ```fifoOut```. The
transport simulates a Bluetooth LE link layer (ACL connection). Packets are
successfully received with a given probability that follow a certain probability
distribution. This is to simulate the propagation channel. Successfully 
received packets are stored in the output FIFO ```fifoOut```. The radio also
has a FIFO that holds packets ready to be transmitted or retransmitted.

The _consumer_ takes one packet out of the output FIFO ```fifoOut``` every
```FRAME_INTERVAL``` and store them in an output wav file.

Producer, consumer and transport are implemented using Python threads that run
in realtime. 

This simulator can be used to evaluate:

- the effect of packet losses

- the effect of buffer overflow/underflow due to different "clocks" in the 
producer, transport and consumer. Overflows result in packets in the FIFO being
overwritten; underflows result in "silence" (0s) being put in the FIFO instead 
of the missing packet.

- effect of different FIFO sizes

The Bluetooth LE link layer simulator uses infinite retransmissions or finite
retransmissions.

## TODO

- ASRC to compensate unsynchronized clocks. The consumer can estimate the 
period of the producer clock by counting how many packets are received in a 
certain period of time, and comparing with how many packets should have been
theoretically been received if the producer clock period was exact.

- Visualize results, e.g., using [PulseView](https://sigrok.org/wiki/PulseView).

- Realistic channel model.

- Instead of saving the results in an output files, the consumer reproduces 
the audio in realitime (e.g., using [PyAudio](http://people.csail.mit.edu/hubert/pyaudio/))

- Try some Packet Loss Conceilment (PLC) algorithms to cope with packet losses.
