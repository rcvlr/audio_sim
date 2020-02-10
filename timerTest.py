import threading
import time
from vcd import VCDWriter

"""
import threading

def printit():
  threading.Timer(5.0, printit).start()
  print "Hello, World!"

printit()
"""

counter = 0
start = 0

def timer1_func(e, vcd, gpio1):
    global counter
    
    counter += 1
    if (counter == 20):
        e.set()
    else:
        timer1 = threading.Timer(10e-3, timer1_func, args=(e, vcd, gpio1))
        timer1.start()
        
        print ("Timer-1 ", counter)
        
        end = time.perf_counter_ns()
        timestamp = end - start
        vcd.change(gpio1, timestamp, 0)
        vcd.change(gpio1, timestamp + 1000, 1)
        vcd.change(gpio1, timestamp + 2000, 0)
        
def timer2_func(e, vcd, gpio2):
    if (e.is_set()):
        return
    else:
        timer2 = threading.Timer(15e-3, timer2_func, args=(e, vcd, gpio2))
        timer2.start()
        
        print ("Timer-2 ", counter)
        
        end = time.perf_counter_ns()
        timestamp = end - start
        vcd.change(gpio2, timestamp, 0)
        vcd.change(gpio2, timestamp + 1000, 1)
        vcd.change(gpio2, timestamp + 2000, 0)
    

def main():
    
    global start

    vcdFile = open("out.vcd", "w")
    vcd = VCDWriter(vcdFile, timescale='1 ns')
    gpio1 = vcd.register_var('libsigrok', 'timer1', 'wire', size=1, ident='!')
    gpio2 = vcd.register_var('libsigrok', 'timer2', 'wire', size=1, ident='$')
    start = time.perf_counter_ns()
    
    # event to signal the consumer to stop consuming
    e = threading.Event()

    timer1 = threading.Timer(10e-3, timer1_func, args=(e, vcd, gpio1))
    timer2 = threading.Timer(15e-3, timer2_func, args=(e, vcd, gpio2))

    timer1.start()
    time.sleep(10e-3)
    timer2.start()
    
    # wait until all threads terminate
    while (e.is_set() == False):
        time.sleep(0.1)

    print("Finish")
    
    vcd.close()
    vcdFile.close()


if __name__ == '__main__':
    main()