"""
@file    packet.py
@author  Riccardo Cavallari
@date    2019.10.03

Radio packet class
"""

from scheduler import Scheduler
from array import array

class Packet:
    """ A packet to be transmitted and received """
    sn = 0              # to generate unique incremental sequence number

    def __init__(self, payload):
        self.payload = payload
        self.seqNum = Packet.sn
        self.birthTime = Scheduler.clockTime
        self.txTime = 0
        Packet.sn += 1
