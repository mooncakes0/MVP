"""Module to integrate with the input subsystem of Milestone 2 MVP
Created by: Jackie Hong, Evgeny Solomin
Created date: 03/04/2024
version: 1.2
"""

# imports
import time
from pymata4 import pymata4

# Hardware constants
pedestianButtonPins = [14, 15] # A0 and A1
ldrPin = 16 # A2
modeSwitchPin = 6

ultrasonicTriggers = [2, 4]
ultrasonicEchos = [3, 5]

# Subsystem constants
numUltrasonicReadings = 15
debounceTime = 0.1
sensorHeight = 28

# Subsystem variables
previousButtonStates = [0, 0]
lastButtonChangeTimes = [0, 0]


def init(board: pymata4.Pymata4) -> None:
	"""Initializes input variables and board pins.
	
	:param board: The arduino board to use for set up.
	"""

	global lastButtonChangeTimes

	for i in range(2):
		board.set_pin_mode_sonar(ultrasonicTriggers[i], ultrasonicEchos[i])

	board.set_pin_mode_digital_input(pedestianButtonPins[0])
	board.set_pin_mode_digital_input(pedestianButtonPins[1])
	board.set_pin_mode_digital_input(modeSwitchPin)
	board.set_pin_mode_analog_input(ldrPin)

	lastButtonChangeTimes = [time.time() - debounceTime] * 2


def get_filtered_ultrasonic(board: pymata4.Pymata4, ultrasonicIndex: int) -> float | None:
	"""Polls the ultrasonic sensor several times and averages the result, discarding any outliers.
	
	:param board: The arduino board to read from.

	:returns: The filtered, averaged distance read from the ultrasonic sensor. Returns None if all readings were considered outliers.
	"""
	
	numReadings = 0
	total = 0

	for i in range(numUltrasonicReadings):
		reading = board.sonar_read(ultrasonicTriggers[ultrasonicIndex])[0]

		# Ultrasonic sensor range is between 2 and 400 cm
		if 2 <= reading <= 400:
			total += reading
			numReadings += 1
	
	if numReadings == 0:
		return None

	average = total / numReadings
	return average


def pedestrian_button_pressed(board: pymata4.Pymata4, button: int) -> bool:
	"""Returns whether the pedestrian button was pressed since the last call of this function.
	Debounces the button input in the process.
	
	:param board: The arduino board to read from.
	:param button: Which button to check

	:returns: Whether or not the button was pressed.
	"""

	global previousButtonStates, lastButtonChangeTimes

	if time.time() < lastButtonChangeTimes[button] + debounceTime:
		return False
	
	currentState = board.digital_read(pedestianButtonPins[button])[0]
	if currentState != previousButtonStates[button]:
		previousButtonStates[button] = currentState
		lastButtonChangeTimes[button] = time.time()
		# return True if the button is currently pressed
		# this code is only reached if the button state changed
		if currentState == 1:
			return True
	return False


def get_vehicle_distance(board: pymata4.Pymata4) -> float|None:
	return get_filtered_ultrasonic(board, 0)


def get_vehicle_height(board: pymata4.Pymata4) -> float|None:
	return sensorHeight - get_filtered_ultrasonic(board, 1)


def get_mode_switch_state(board: pymata4.Pymata4) -> bool:
	return board.digital_read(modeSwitchPin)[0]


def get_LDR_reading(board: pymata4.Pymata4) -> float:
	return board.analog_read(ldrPin)[0]