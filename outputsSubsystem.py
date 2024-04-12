"""Module to control outputs for Milestone 2 of MVP
Created by: Jackie Hong, Evgeny Solomin
Created Date: 04/04/2024
Version: 1.2
"""

# list of pins needed for each light system
# index 0 = red,   index 1 = yellow,     index 2 = green
# for pedestrian lights, 0 is red, 1 is green
mainLights = [4, 5, 6]
sideLights = [7, 8, 9]
pedLights = [10, 11]

# the state of each light during each traffic stage
# first column is main lights
# second is side road lights
# third is pedestrian lights
# for pedestrian lights, 2 means flashing green
lightStates = {
	1: (2, 0, 0),
	2: (1, 0, 0),
	3: (0, 0, 0),
	4: (0, 2, 1),
	5: (0, 1, 2),
	6: (0, 0, 0)
}
blinkFrequency = 3 # in hertz

lastTrafficStage = -1
stageTimes = (30, 3, 3, 30, 3, 3)
lastBlinkState = False


def init() -> None:
	"""Initializes output variables and board pins.
	
	:param board: The arduino board to set up.
	"""
	for i in (mainLights + sideLights + pedLights):
		print(f"Set pin {i} as digital output.")


def shutdown() -> None:
	"""Does any required cleanup.
	
	:param board: The arduino board to shut down.
	"""

	for i in (mainLights + sideLights + pedLights):
		print(f"Write 0 to pin {i}.")


def get_traffic_stage(normalModeTime: float) -> tuple[int, float, float]:
	"""Returns the current traffic stage (1-6) based on the time spent in normal operation mode.
	
	:param normalModeTime: Time spent in normal operation mode.

	:returns: (traffic stage, time in current stage, time until next stage).
	Current traffic stage is given as an int, 1-6.
	Time in current traffic stage and time until next traffic stage are given in seconds, as floats.
	"""

	totalStageTime = sum(stageTimes)
	timeMod = normalModeTime % totalStageTime
	runningTotal = 0
	for i in range(len(stageTimes)):
		if timeMod - runningTotal < stageTimes[i]:
			return (i + 1, timeMod - runningTotal, stageTimes[i] - (timeMod - runningTotal))
		runningTotal += stageTimes[i]
	return len(stageTimes)

def get_main_light_state(trafficStage: int) -> int:
	"""Returns the state of the main traffic light during the given state
	
	:param trafficStage: Current traffic stage (int)

	:returns: State of main traffic light (int). 0 is red, 1 is yellow, 2 is green.
	"""

	return lightStates[trafficStage][0]

def traffic_operation(normalModeTime: float) -> None:
	"""Operates outputs of the system.
	
	:param board: arduino board
	:param normalModeTime: Time spent in normal operating mode, in seconds (float)
	"""

	global lastTrafficStage, lastBlinkState
	
	currentStage = get_traffic_stage(normalModeTime)[0]
	stageStates = lightStates[currentStage]
	
	if currentStage != lastTrafficStage:
		lastTrafficStage = currentStage

		for i in range(3):
			print(f"Set pin {mainLights[i]} to {stageStates[0] == i}.")
			print(f"Set pin {sideLights[i]} to {stageStates[1] == i}.")

			if i != 2:
				print(f"Set pin {pedLights[i]} to {stageStates[2] == i}.")

	blinkState = (normalModeTime % (1/blinkFrequency)) * blinkFrequency < 0.5
	if stageStates[2] == 2 and blinkState != lastBlinkState:
		print(f"Set pin {pedLights[i]} to {stageStates[2] == i}.")
		lastBlinkState = blinkState
