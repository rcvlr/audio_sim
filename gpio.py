"""
@file    gpio.py
@author  Riccardo Cavallari
@date    2020.02.11

Class to represent a GPIO line that can be toggled
"""

from vcd import VCDWriter

class Gpio:
    """ A GPIO that can be toggled """
    
    def __init__(self, initValue, writer, name, id):
        self.value = initValue
        self.writer = writer
        self.wire = self.writer.register_var('audio_sim', name, 'wire', size=1, ident=id)

    def toggle(self, timestamp):
        self.value ^= 1
        self.writer.change(self.wire, timestamp, self.value)
