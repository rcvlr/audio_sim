"""
@file    scheduler.py
@author  Riccardo Cavallari
@date    21-05-2014

The event scheduler
"""

from operator import attrgetter

class Scheduler:
	""" A siple event scheduler """
	# Queue of events: the queue of the scheduler. An event is
	# represented as a tuple composed of (process, (args)).
	eventList = list()
	simDuration = float()	# simulation duration (in sec)
	clockTime = float()		# current clock time

class Event:
	""" an event is a periodic/single action to be executed with some arguments
		at a certain time. If the event is periodic, a stopTime can be defined. """
	def __init__(self, execTime, period, action, args, stopTime = -1):
		self.execTime 	= execTime
		self.period 	= period
		self.action 	= action
		self.args 		= args
		self.stopTime 	= stopTime

def setSimDuration(duration):
	""" Set the duration of the simulation in sec """
	Scheduler.simDuration = duration

def setClock(time):
	""" adjust current clock time """
	Scheduler.clockTime = time

def simDone():
	""" this should be called when simulation expires """
	print('Simulation done at time', Scheduler.clockTime)

def printEventQueue():
	""" Print the events currently in the list """
	for e in Scheduler.eventList:
		print(e.action)

def addEvent(event):
	""" Add an event to be executed at time execTime to the scheduler queue.
		The list is already sorted according to execTime """
	Scheduler.eventList.append(event)
	Scheduler.eventList = sorted(Scheduler.eventList, key=attrgetter('execTime'))

def removeEvent(event):
	""" Remove an event from the queue """
	# search the event into the list of event: it returns the first event with
	# the corresponding name. Notice that if more than one event are present with
	# the same name, only the closest to be executed will be removed
	toBeRemoved = next((x for x in Scheduler.eventList if x == event), None)

	if(toBeRemoved is not None): Scheduler.eventList.remove(toBeRemoved)
	else: print('Error: event not found')

def runEvents():
	""" Runs in FIFO fashion the events in the queue """
	while(len(Scheduler.eventList) > 0):
		# retrieve the first event
		e = Scheduler.eventList.pop(0)

		# update the clock: the current time is now the execution time of this
		# event.
		setClock(e.execTime)

		# run the event only if the simulation time has not expired yet
		if(Scheduler.clockTime <= Scheduler.simDuration):
			# execute the process with its arguments
			print('SCHED:	run', e.action, '@', Scheduler.clockTime)
			e.action(*e.args)

			# if the event is periodic, set the new execution time and put it
			# back into the ordered list of events.
			if (e.period != 0):
				newExecTime = Scheduler.clockTime + e.period
				if(newExecTime <= e.stopTime or e.stopTime == -1):
					newEvent = Event(newExecTime, e.period, e.action, e.args, e.stopTime)
					Scheduler.eventList.append(newEvent)
					Scheduler.eventList = sorted(Scheduler.eventList, key=attrgetter('execTime'))
		else:
			# simulation time has expired
			break
