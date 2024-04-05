"""Main code for Team I07's project Milestone 2
This file makes up the control and service subsystems
Created by Evgeny Solomin (34977260)
Last modified: 03/04/2024
"""

import time
from pymata4 import pymata4
import matplotlib.pyplot as ppl

# import serviceSubsystem as service
import inputsSubsystem as inputs
import outputsSubsystem as outputs

# ===== User modifiable variables ===== 
maintenancePIN = "1234"
maxPINAttempts = 4
incorrectPINTimeout = 120
pollLoopTime = 2
distancePrintDelay = 2

# ===== Program constants =====
serviceModeConstant = "service"
normalModeConstant = "normal"
dataObservationModeConstant = "dataObservation"
maintenanceModeConstant = "maintenance"

# ===== Program variables =====
# general variables
board = None
operationMode = None

# normal mode variables
normalModeEnterTime = 0
lastTrafficStage = None
pedestrianCount = 0
ultrasonicReadings = []
nextDistancePrintTime = 0
nextUltrasonicReadTime = 0
lastPollTime = 0

# service mode variables
PINTimeoutTime = 0
incorrectPINInputs = 0


def main() -> None:
	"""Main control loop"""

	global operationMode

	init()

	while True:
		try:
			if operationMode == serviceModeConstant:
				service_mode()
			if operationMode == normalModeConstant:
				normal_operation()
			if operationMode == maintenanceModeConstant:
				maintenance_mode()
				operationMode = serviceModeConstant
			if operationMode == dataObservationModeConstant:
				data_observation_mode()
				operationMode = serviceModeConstant
		except KeyboardInterrupt:
			if operationMode == serviceModeConstant:
				break
			operationMode = serviceModeConstant
	
	shutdown()

def init() -> None:
	"""Initializes program variables"""
	global board
	global operationMode
	global incorrectPINInputs
	global PINTimeoutTime

	operationMode = serviceModeConstant
	incorrectPINInputs = 0
	PINTimeoutTime = time.time()

	board = pymata4.Pymata4()

	time.sleep(0.5)

	inputs.init(board)
	outputs.init(board)

	time.sleep(0.5)


def shutdown() -> None:
	outputs.shutdown(board)

	# noticed in testing that not adding a delay caused some commands to not register
	time.sleep(0.5)
	board.shutdown()


def init_normal_operation() -> None:
	"""Initialises normal operation mode variables. Called every time system enters into normal operation mode."""

	global normalModeEnterTime
	global pedestrianCount
	global nextUltrasonicReadTime
	global nextDistancePrintTime
	global lastPollTime

	normalModeEnterTime = time.time()
	nextUltrasonicReadTime = normalModeEnterTime
	# set the distance print to first trigger when
	nextDistancePrintTime = normalModeEnterTime
	lastPollTime = normalModeEnterTime

	pedestrianCount = 0


def poll_sensors():
	"""Polls the ultrasonic sensor and stores relevant data."""

	global ultrasonicReadings

	ultrasonicDistance = inputs.get_filtered_ultrasonic(board)
	# only add reading to list if we got a valid distance
	if ultrasonicDistance is not None:
		ultrasonicReadings.append((time.time(), ultrasonicDistance))

	while ultrasonicReadings[-1][0] - ultrasonicReadings[0][0] > 20 + pollLoopTime:
		ultrasonicReadings.pop(0)


def normal_operation() -> None:
	"""Standard operating mode.
	Polls sensors and stores relevant data, as well as operating system outputs."""

	global lastTrafficStage
	global pedestrianCount
	global nextDistancePrintTime
	global nextUltrasonicReadTime
	global lastPollTime

	if time.time() >= nextUltrasonicReadTime:
		poll_sensors()

		print(f"Polling loop took {time.time() - lastPollTime:.2f} seconds.")
		
		lastPollTime = time.time()
		nextUltrasonicReadTime += pollLoopTime
	
	if time.time() >= nextDistancePrintTime:
		if len(ultrasonicReadings):
			print(f"Last distance reading: {ultrasonicReadings[-1][1]:.1f} cm")
		
		nextDistancePrintTime += distancePrintDelay
	
	if inputs.pedestrian_button_pressed(board):
		pedestrianCount += 1
	
	normalModeTime = time.time() - normalModeEnterTime
	trafficStage, nextStageTime = outputs.get_traffic_stage(normalModeTime)
	if trafficStage != lastTrafficStage:
		print(f"Changing to traffic stage {trafficStage}.")

		if lastTrafficStage == 6 and trafficStage == 1:
			pedestrianCount = 0
		elif lastTrafficStage == 2 and trafficStage == 3:
			print(f"There were {pedestrianCount} pedestrians in this traffic cycle.")
	
	outputs.traffic_operation(board, normalModeTime)
	# outputs.show_message(str(nextStageTime))

	lastTrafficStage = trafficStage

	time.sleep(0.05)


def service_mode() -> None:
	"""Allows the user to change operating modes.
	Entering maintenance mode requires correct maintenance mode PIN.
	"""

	global operationMode

	while operationMode == serviceModeConstant:
		print("Available operating modes (press Ctrl + C to exit program):")
		print("1. Normal operation")
		print("2. Data observation")
		print("3. Maintenance")

		opModeInput = input("Select operating mode to enter: ")
		match opModeInput:
			case "1":
				operationMode = normalModeConstant
				init_normal_operation()
				break
			case "2":
				operationMode = dataObservationModeConstant
				break
			case "3":
				if get_PIN_input():
					operationMode = maintenanceModeConstant
				break


def get_PIN_input() -> bool:
	"""Gets the user's PIN input.
	Locks out the user after entering the incorrect PIN too many times.
	
	:returns: Whether the user entered the correct PIN. Returns false if the user is currently locked out.
	"""

	global incorrectPINInputs
	global PINTimeoutTime

	if time.time() < PINTimeoutTime:
		print(f"Locked out for another {PINTimeoutTime - time.time():.0f} seconds.")
		return False
	
	while incorrectPINInputs < maxPINAttempts:
		if incorrectPINInputs != 0:
			print(f"Incorrect PIN entered. {maxPINAttempts - incorrectPINInputs} attempt(s) remaining.")
		
		PINInput = input("Enter PIN: ")
		if PINInput == maintenancePIN:
			incorrectPINInputs = 0
			return True
		
		if PINInput == "":
			return False
		
		incorrectPINInputs += 1

	print(f"Incorrect PIN entered too many times. User will be locked out for {incorrectPINTimeout} seconds.")

	incorrectPINInputs = 0
	PINTimeoutTime = time.time() + incorrectPINTimeout
	return False


def maintenance_mode() -> None:
	"""Allows the user to change variables that affect the operation of the system."""

	global maintenancePIN
	global maxPINAttempts
	global incorrectPINTimeout
	global pollLoopTime
	global distancePrintDelay

	running = True
	while running:
		print("Variables available to edit:")
		print(f"1. Maintenance mode PIN: \"{maintenancePIN}\"")
		print(f"2. Maximum PIN attempts before timeout: {maxPINAttempts}")
		print(f"3. Incorrect PIN timeout time: {incorrectPINTimeout} seconds")
		print(f"4. Polling loop frequency: {pollLoopTime} seconds")
		print(f"5. Distance print frequency: {distancePrintDelay} seconds")
		print("6. Exit maintenance mode")

		varToEdit = input()
		match varToEdit:
			case "1":
				newPIN = input("Enter new maintenance mode PIN: ")

				if len(newPIN) < 4:
					print("PIN must contain at least 4 characters.")
					input("Press [Enter] to continue.")
					continue

				maintenancePIN = newPIN
			case "2":
				newMaxAttempts = input("Enter new maximum incorrect inputs: ")

				try:
					newMaxAttempts = int(str(newMaxAttempts))
				except ValueError:
					print("Value must be an integer.")
					input("Press [Enter] to continue.")
					continue

				if newMaxAttempts < 1:
					print("Value must be at least 1.")
					input("Press [Enter] to continue.")
					continue

				maxPINAttempts = newMaxAttempts
			case "3":
				newTimeout = input("Enter new PIN timeout: ")

				try:
					newTimeout = float(newTimeout)
				except ValueError:
					print("Value must be a valid number.")
					input("Press [Enter] to continue.")
					continue
					
				if newTimeout < 0:
					print("Value must be positive.")
					input("Press [Enter] to continue.")
					continue

				incorrectPINTimeout = newTimeout
			case "4":
				newLoopTime = input("Enter new polling loop frequency: ")

				try:
					newLoopTime = float(newLoopTime)
				except ValueError:
					print("Value must be a valid number.")
					input("Press [Enter] to continue.")
					continue
					
				if not 1 <= newLoopTime <= 5:
					print("Value must be between 1 and 5 seconds.")
					input("Press [Enter] to continue.")
					continue

				pollLoopTime = newLoopTime
			case "5":
				newPrintTime = input("Enter new distance print frequency: ")

				try:
					newPrintTime = float(newPrintTime)
				except ValueError:
					print("Value must be a valid number.")
					input("Press [Enter] to continue.")
					continue
					
				if not 1 <= newPrintTime <= 3:
					print("Value must be between 1 and 3 seconds.")
					input("Press [Enter] to continue.")
					continue

				distancePrintDelay = newPrintTime
			case "6":
				running = False


def data_observation_mode() -> None:
	"""Creates a graph of the past 20 seconds of traffic data."""

	if ultrasonicReadings[-1][0] - ultrasonicReadings[0][0] < 20:
		print("Warning: less than 20 seconds of data will be shown.")

	currentTime = time.time()
	
	x = [reading[0] - currentTime for reading in ultrasonicReadings]
	y = [reading[1] for reading in ultrasonicReadings]

	fig, ax = ppl.subplots()

	ax.plot(x, y)
	
	ax.set(xlim=(-20, 0), ylim=(0, max(y)))

	ppl.show()

if __name__ == "__main__":
	main()
