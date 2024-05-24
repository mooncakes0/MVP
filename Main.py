"""Main code for Team I07's project Milestone 2
This file makes up the control and service subsystems
Created by: Evgeny Solomin
Created Date: 03/04/2024
Version: 1.4
"""

import time
from pymata4 import pymata4
import matplotlib.pyplot as ppl

import InputsSubsystem as inputs
import OutputsSubsystem as outputs

# ===== User modifiable variables ===== 
maintenancePIN = "1234"
maxPINAttempts = 3
incorrectPINTimeout = 120
pollLoopInterval = 1.5
distancePrintDelay = 2

# ===== Program constants =====
serviceModeConstant = "service"
normalModeConstant = "normal"
dataObservationModeConstant = "dataObservation"
maintenanceModeConstant = "maintenance"
exitConstant = "exit"

# ===== Program variables =====
# general variables
board = None
operationMode = None

# normal mode variables
normalModeEnterTime = 0
lastTrafficStage = None
pedestrianCount = 0
ultrasonicReadings = []
vehicleDistance = 0
vehicleHeight = 0
nextDistancePrintTime = 0
nextUltrasonicReadTime = 0
lastPollTime = 0
maxVehicleDeceleration = 20 # used for system alerts. In cm/s^2
stallTime = 0

# service mode variables
PINTimeoutTime = 0
incorrectPINInputs = 0


def main() -> None:
	"""Main control loop"""

	global operationMode

	init()
 
	# weird double while true loop to avoid KeyboardInterrupts from going uncaught
	while operationMode != exitConstant:
		try:
			while operationMode != exitConstant:
				if inputs.get_mode_switch_state(board) and operationMode == normalModeConstant:
					operationMode = serviceModeConstant

				if operationMode == serviceModeConstant:
					service_mode()
					continue
				if operationMode == normalModeConstant:
					normal_operation()
					continue
				if operationMode == maintenanceModeConstant:
					outputs.set_maintenance_LEDs(board, True)
					maintenance_mode()
					outputs.set_maintenance_LEDs(board, False)
					operationMode = serviceModeConstant
					continue
				if operationMode == dataObservationModeConstant:
					data_observation_mode()
					operationMode = serviceModeConstant
					continue
		except KeyboardInterrupt:
			if operationMode == serviceModeConstant:
				operationMode = exitConstant
			else:
				operationMode = serviceModeConstant
			outputs.reset(board)

	shutdown()

def init() -> None:
	"""Initializes program variables"""

	global board, operationMode, incorrectPINInputs, PINTimeoutTime

	operationMode = serviceModeConstant
	incorrectPINInputs = 0
	PINTimeoutTime = time.time()

	board = pymata4.Pymata4()

	time.sleep(1)

	# board.set_sampling_interval(100000)

	inputs.init(board)
	outputs.init(board)


def shutdown() -> None:
	"""Shuts down the board, and allows other subsystems to call their own shutdown methods."""
	
	print("\nShutting down...")

	outputs.reset(board)

	# noticed in testing that not adding a delay caused the board to shut down before some commands were excecuted
	time.sleep(1)
	board.shutdown()


def init_normal_operation() -> None:
	"""Initialises normal operation mode variables. Called every time system enters into normal operation mode."""

	global normalModeEnterTime, pedestrianCount, nextUltrasonicReadTime, nextDistancePrintTime, lastPollTime

	normalModeEnterTime = time.time()
	# set the distance print and poll to first trigger when entering normal operation
	nextUltrasonicReadTime = normalModeEnterTime
	nextDistancePrintTime = normalModeEnterTime
	lastPollTime = normalModeEnterTime - pollLoopInterval

	pedestrianCount = 0

	outputs.reset(board)


def poll_sensors() -> None:
	"""Polls the ultrasonic sensor and stores relevant data."""

	global ultrasonicReadings, vehicleHeight, vehicleDistance

	ultrasonicDistance = inputs.get_vehicle_distance(board)
	# only add reading to list if we got a valid distance
	if ultrasonicDistance is not None:
		vehicleDistance = ultrasonicDistance
		ultrasonicReadings.append((time.time(), ultrasonicDistance))

		# Remove excess data from the readings buffer
		while (ultrasonicReadings[-1][0] - ultrasonicReadings[0][0] > 20 # Check if there is more than 20 seconds of data
			and ultrasonicReadings[-1][0] - ultrasonicReadings[1][0] > 20):	# Ensure that there will still be more than 20 seconds of data left if a reading is removed
			ultrasonicReadings.pop(0)

	heightReading = inputs.get_vehicle_height(board)
	if heightReading is not None:
		vehicleHeight = heightReading


def normal_operation() -> None:
	"""Standard operating mode.
	Polls sensors and stores relevant data, as well as operating system outputs.
	"""

	global lastTrafficStage, pedestrianCount, nextDistancePrintTime, nextUltrasonicReadTime, lastPollTime
	global stallTime

	inputs.update(board)
	
	if inputs.pedestrian_button_pressed(0):
		pedestrianCount += 1
	
	if inputs.pedestrian_button_pressed(1):
		pedestrianCount += 1
	
	if outputs.trafficStage != lastTrafficStage:
		lastTrafficStage = outputs.trafficStage

		print(f"Changing to traffic stage {outputs.trafficStage + 1}.")

		if outputs.trafficStage == 1:
			pedestrianCount = 0
		elif outputs.trafficStage == 3:
			print(f"There were {pedestrianCount} pedestrians in this traffic cycle.")

	if time.time() >= nextUltrasonicReadTime:
		poll_sensors()

		pollLoopTime = time.time() - lastPollTime
		print(f"Polling loop took {pollLoopTime:.2f} seconds (intended {pollLoopInterval:.2f}).")
		
		lastPollTime = time.time()
		nextUltrasonicReadTime += pollLoopInterval

		if len(ultrasonicReadings) >= 2:
			speed = (ultrasonicReadings[-2][1] - ultrasonicReadings[-1][1]) / pollLoopTime
			lightState = outputs.get_main_light_state()

			# During a red light, check if vehicle is predicted to not stop in time
			# Using the constant acceleration formula v^2 = u^2 + 2as
			if speed > 0 and lightState == 0 and speed**2 / 2 / maxVehicleDeceleration > ultrasonicReadings[-1][1]:
				print("ALERT: Vehicle likely run a red light.")

			# During a green light, issue an alert if vehicle seems to not be moving after 3 seconds
			if lightState == 2 and -1 / pollLoopTime <= speed <= 1 / pollLoopTime:
				stallTime += pollLoopInterval

				if stallTime > 3 and stallTime - pollLoopInterval <= 3:
					print("ALERT: Vehicle stalling at green light.")
			else:
				stallTime = 0
	
	if time.time() >= nextDistancePrintTime and len(ultrasonicReadings):
		print(f"Last distance reading: {ultrasonicReadings[-1][1]:.2f} cm")
	
		nextDistancePrintTime += distancePrintDelay
	
	outputs.update(board, vehicleDistance, vehicleHeight)


def service_mode() -> None:
	"""Allows the user to change operating modes.
	Entering maintenance mode requires correct maintenance mode PIN.
	"""

	global operationMode

	while operationMode == serviceModeConstant:
		print("Available operating modes:")
		print("1. Normal operation")
		print("2. Data observation")
		print("3. Maintenance")
		print("4. Exit program")

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
			case "4":
				operationMode = exitConstant


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
		print(f"6. Maximum vehicle height: {outputs.heightLimit} cm")
		print(f"7. Max yellow light extension distance: {outputs.yellowLightExtensionDistance} cm")
		print("8. Exit maintenance mode")

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
				newMaxHeight = input("Enter new maximum vehicle height: ")

				try:
					newMaxHeight = float(newMaxHeight)
				except ValueError:
					print("Value must be a valid number.")
					input("Press [Enter] to continue.")
					continue
					
				if not 0 <= newMaxHeight <= 28:
					print("Value must be between 0 and 28 cm.")
					input("Press [Enter] to continue.")
					continue

				outputs.heightLimit = newMaxHeight
			case "7":
				newMaxDist = input("Enter new maximum vehicle height: ")

				try:
					newMaxDist = float(newMaxDist)
				except ValueError:
					print("Value must be a valid number.")
					input("Press [Enter] to continue.")
					continue
					
				if not 0 <= newMaxDist <= 50:
					print("Value must be between 0 and 50 cm.")
					input("Press [Enter] to continue.")
					continue

				outputs.yellowLightExtensionDistance = newMaxDist
			case "8":
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
