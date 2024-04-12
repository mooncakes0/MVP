"""Module to integrate with the input subsystem of Milestone 2 MVP
Created by: Jackie Hong, Evgeny Solomin
Created date: 03/04/2024
version: 1.1
"""

# imports
import time
import random

# Hardware constants
trigger = 12
echo = 13
button = 3

# Subsystem constants
numUltrasonicReadings = 15
debounceTime = 0.1

# Subsystem variables
previousState = 0
lastButtonChangeTime = 0

def init() -> None:
	"""Initializes input variables and board pins.
	
	:param board: The arduino board to use for set up.
	"""

	global lastButtonChangeTime

	print(f"Set up sonar with pin {trigger} as trigger pin and pin {echo} as echo pin.")
	print(f"Set pin {button} to act as a digital input.")
	# board.set_pin_mode_sonar(trigger, echo)
	# board.set_pin_mode_digital_input(button)

	lastButtonChangeTime = time.time() - debounceTime


def get_filtered_ultrasonic() -> float | None:
	"""Polls the ultrasonic sensor several times and averages the result, discarding any outliers.
	
	:param board: The arduino board to read from.

	:returns: The filtered, averaged distance read from the ultrasonic sensor. Returns None if all readings were considered outliers.
	"""
	
	numReadings = 0
	total = 0

	for i in range(numUltrasonicReadings):
		reading = random.randint(2, 400)
		print(f"Take a sonar reading using pin {trigger} as trigger pin.")

		# ultrasonic range is 2-400 cm
		if 2 <= reading <= 400:
			total += reading
			numReadings += 1
	
	if numReadings == 0:
		return None

	average = total / numReadings
	return average


def pedestrian_button_pressed() -> bool:
	"""Returns whether the pedestrian button was pressed since the last call of this function.
	Debounces the button input in the process.
	
	:param board: The arduino board to read from.

	:returns: Whether or not the button was pressed.
	"""

	global button, previousState, lastButtonChangeTime

	if time.time() < lastButtonChangeTime + debounceTime:
		return False

	currentState = random.randint(0, 1)
	print(f"Read state (digital) of pin {button}.")
	if currentState != previousState:
		previousState = currentState
		lastButtonChangeTime = time.time()
		# check if the current state is 1 or 0 as instances where current and previous are different but current is 0
		if currentState == 1:
			return True
	return False
