"""Main code for Team I07's project Milestone 2
This file makes up the control and service subsystems
Created by: Evgeny Solomin
Created Date: 03/04/2024
Version: 1.3
"""

import time
import matplotlib.pyplot as ppl

import inputsSubsystem as inputs
import outputsSubsystem as outputs

# ===== User modifiable variables ===== 
maintenancePIN = "1234"
maxPINAttempts = 4
incorrectPINTimeout = 120
pollLoopInterval = 1.5
distancePrintDelay = 2

# ===== Program constants =====
serviceModeConstant = "service"
normalModeConstant = "normal"
dataObservationModeConstant = "dataObservation"
maintenanceModeConstant = "maintenance"

# ===== Program variables =====
# general variables
operationMode = None

# normal mode variables
normalModeEnterTime = 0
lastTrafficStage = None
pedestrianCount = 0
ultrasonicReadings = []
nextDistancePrintTime = 0
nextUltrasonicReadTime = 0
lastPollTime = 0
maxVehicleDeceleration = 20 # used for system alerts. In cm/s^2

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
	global operationMode, incorrectPINInputs, PINTimeoutTime

	operationMode = serviceModeConstant
	incorrectPINInputs = 0
	PINTimeoutTime = time.time()

	print("Set up arduino board.")

	time.sleep(0.5)

	inputs.init()
	outputs.init()

	time.sleep(0.5)


def shutdown() -> None:
	"""Shuts down the board, and allows other subsystems to call their own shutdown methods."""
	outputs.shutdown()

	# noticed in testing that not adding a delay caused the board to shut down before some commands were excecuted
	time.sleep(1)
	print("Shut down board.")


def init_normal_operation() -> None:
	"""Initialises normal operation mode variables. Called every time system enters into normal operation mode."""

	global normalModeEnterTime, pedestrianCount, nextUltrasonicReadTime, nextDistancePrintTime, lastPollTime

	normalModeEnterTime = time.time()
	# set the distance print and poll to first trigger when entering normal operation
	nextUltrasonicReadTime = normalModeEnterTime
	nextDistancePrintTime = normalModeEnterTime
	lastPollTime = normalModeEnterTime

	pedestrianCount = 0


def poll_sensors():
	"""Polls the ultrasonic sensor and stores relevant data."""

	global ultrasonicReadings

	ultrasonicDistance = inputs.get_filtered_ultrasonic()
	# only add reading to list if we got a valid distance
	if ultrasonicDistance is not None:
		ultrasonicReadings.append((time.time(), ultrasonicDistance))

		# Remove excess data from the readings buffer
		while (ultrasonicReadings[-1][0] - ultrasonicReadings[0][0] > 20 # Check if there is more than 20 seconds of data
			and ultrasonicReadings[-1][0] - ultrasonicReadings[1][0] > 20):	# Ensure that there will still be more than 20 seconds of data left if a reading is removed
			ultrasonicReadings.pop(0)


def normal_operation() -> None:
	"""Standard operating mode.
	Polls sensors and stores relevant data, as well as operating system outputs."""

	global lastTrafficStage, pedestrianCount, nextDistancePrintTime, nextUltrasonicReadTime, lastPollTime
	
	if inputs.pedestrian_button_pressed():
		pedestrianCount += 1
	
	normalModeTime = time.time() - normalModeEnterTime
	trafficStage, currentStageTime, nextStageTime = outputs.get_traffic_stage(normalModeTime)
	if trafficStage != lastTrafficStage:
		print(f"Changing to traffic stage {trafficStage}.")

		if trafficStage == 1:
			pedestrianCount = 0
		elif trafficStage == 3:
			print(f"There were {pedestrianCount} pedestrians in this traffic cycle.")

	if time.time() >= nextUltrasonicReadTime:
		poll_sensors()

		pollLoopTime = time.time() - lastPollTime
		print(f"Polling loop took {pollLoopTime:.2f} seconds (intended {pollLoopInterval:.2f}).")
		
		lastPollTime = time.time()
		nextUltrasonicReadTime += pollLoopInterval

		if len(ultrasonicReadings) >= 2:
			speed = (ultrasonicReadings[-2][1] - ultrasonicReadings[-1][1]) / pollLoopTime
			lightState = outputs.get_main_light_state(trafficStage)

			# During a red light, check if vehicle is predicted to not stop in time
			# Using the constant acceleration formula v^2 = u^2 + 2as
			if speed > 0 and lightState == 0 and speed**2 / 2 / maxVehicleDeceleration > ultrasonicReadings[-1]:
				print("ALERT: Vehicle likely run a red light.")

			# During a green light, issue an alert if vehicle seems to not be moving after 3 seconds
			if lightState == 2 and currentStageTime > 3 and -1 / pollLoopTime <= speed <= 1 / pollLoopTime:
				print("ALERT: Vehicle stalling at green light.")
	
	if time.time() >= nextDistancePrintTime and len(ultrasonicReadings):
		print(f"Last distance reading: {ultrasonicReadings[-1][1]:.2f} cm")
	
		nextDistancePrintTime += distancePrintDelay
	
	outputs.traffic_operation(normalModeTime)

	lastTrafficStage = trafficStage

	# time.sleep(0.05)


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

	global incorrectPINInputs, PINTimeoutTime

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

	global maintenancePIN, maxPINAttempts, incorrectPINTimeout, pollLoopInterval, distancePrintDelay

	running = True
	while running:
		print("Variables available to edit:")
		print(f"1. Maintenance mode PIN: \"{maintenancePIN}\"")
		print(f"2. Maximum PIN attempts before timeout: {maxPINAttempts}")
		print(f"3. Incorrect PIN timeout time: {incorrectPINTimeout} seconds")
		print(f"4. Polling loop interval: {pollLoopInterval} seconds")
		print(f"5. Distance print interval: {distancePrintDelay} seconds")
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
				newMaxAttempts = input("Enter new maximum PIN attempts: ")

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
				newLoopTime = input("Enter new polling loop interval: ")

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

				pollLoopInterval = newLoopTime
			case "5":
				newPrintTime = input("Enter new distance print interval: ")

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

	if len(ultrasonicReadings) == 0:
		print("No data to display!")
		return

	if ultrasonicReadings[-1][0] - ultrasonicReadings[0][0] < 20:
		print("Warning: less than 20 seconds of data will be shown.")
	
	x = [reading[0] - ultrasonicReadings[-1][0] for reading in ultrasonicReadings]
	y = [reading[1] for reading in ultrasonicReadings]

	_, ax = ppl.subplots()

	ax.plot(x, y)
	ax.set(xlim=(-20, 0), ylim=(0, max(y)))

	ax.set_xlabel("Time (sec)")
	ax.set_ylabel("Distance (cm)")
	ax.set_title("Vehicle distance over time")

	ppl.show()

if __name__ == "__main__":
	main()
