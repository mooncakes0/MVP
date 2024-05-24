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
ldrPin = 2 # A2
modeSwitchPin = 6

ultrasonicTriggers = [2, 4]
ultrasonicEchos = [3, 5]

# Subsystem constants
numUltrasonicReadings = 5
debounceTime = 0.1
sensorHeight = 28
nightThreshold = 800

# Subsystem variables
previousButtonStates = [0, 0]
buttonStates = [0, 0]
lastButtonChangeTimes = [0, 0]


def init(board: pymata4.Pymata4) -> None:
	"""Initializes input variables and board pins.
	
	:param board: The arduino board to use for set up.
	"""

	global lastButtonChangeTimes
	
	for i in range(2):
		board.set_pin_mode_sonar(ultrasonicTriggers[i], ultrasonicEchos[i], timeout=10000)

	board.set_pin_mode_digital_input(pedestianButtonPins[0])
	board.set_pin_mode_digital_input(pedestianButtonPins[1])
	board.set_pin_mode_digital_input(modeSwitchPin)
	board.set_pin_mode_analog_input(ldrPin, differential=1000)

	lastButtonChangeTimes = [time.time() - debounceTime] * 2


def update(board: pymata4.Pymata4) -> None:
	"""Updates input parameters.
	
	:param board: Pymata4 board.
	"""

	global previousButtonStates, buttonStates, lastButtonChangeTimes

	for i in range(2):
		previousButtonStates[i] = buttonStates[i]

		if time.time() < lastButtonChangeTimes[i] + debounceTime:
			continue
		
		buttonStates[i] = board.digital_read(pedestianButtonPins[i])[0]
		if buttonStates[i] != previousButtonStates[i]:
			previousButtonStates[i] = buttonStates[i]
			lastButtonChangeTimes[i] = time.time()


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


def pedestrian_button_pressed(button: int) -> bool:
	"""Returns whether the pedestrian button was pressed since the last call of this function.
	Debounces the button input in the process.
	
	:param board: The arduino board to read from.
	:param button: Which button to check

	:returns: Whether or not the button was pressed.
	"""

	return buttonStates[button] and not previousButtonStates[button]


def get_vehicle_distance(board: pymata4.Pymata4) -> float:
	"""Returns the distance to the next vehicle, in cm.
	
	:param board: Pymata4 board.

	:returns: Distance to vehicle, in cm, or 0 if the readings were faulty
	"""

	reading = get_filtered_ultrasonic(board, 0)

	if reading is None:
		return 0

	return reading


def get_vehicle_height(board: pymata4.Pymata4) -> float:
	"""Returns the heihgt of the next vehicle, in cm.
	
	:param board: Pymata4 board.

	:returns: Height of vehicle, in cm. Will return a height of zero if the reading were faulty.
	"""
	reading = get_filtered_ultrasonic(board, 1)

	if reading is None:
		return 0
	
	return sensorHeight - reading


def get_mode_switch_state(board: pymata4.Pymata4) -> bool:
	"""Returns whether the mode override switch has been turned on.
	
	:param board: Pymata4 board.

	:returns: Mode override switch state.
	"""
	return board.digital_read(modeSwitchPin)[0]


def is_night(board: pymata4.Pymata4) -> bool:
	"""Checks whether it is currently night.
	
	:param board: Pymata4 board.

	:returns: Whether it is currently night or not.
	"""

	ldrReading = board.analog_read(ldrPin)[0]
	return ldrReading > nightThreshold