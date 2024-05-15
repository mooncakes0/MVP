"""Module to control outputs for Milestone 2 of MVP
Created by: Jackie Hong, Evgeny Solomin
Created Date: 04/04/2024
Version: 2.0
"""

import time
from pymata4 import pymata4

import InputsSubsystem

import SevenSeg
import ShiftReg

# the state of each light during each traffic stage
# first column is main lights
# second is side road lights
# third is pedestrian lights
# 0 is red, 1 is yellow, 2 is green
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
heightLimit = 20
yellowLightExtensionDistance = 50

trafficStage = 0

trafficStageTimer = 0
currentStageTime = 0
lastUpdateTime = 0

sevenSegRefreshes = 0

stageTimes = [30, 3, 3, 30, 3, 3]

overHeightBuzzerTimer = -1
overHeightLEDTimer = -1

mainLightStates = [0, 0, 0]
sideLightStates = [0, 0, 0]
pedLightStates = [0, 0]

overHeightBuzzerState = 0
overHeightLEDState = 0

maintenanceLEDsState = 0

stage4BuzzerState = 0
stage5BuzzerState = 0

outputsModified = False

auxSerPin = 17 # A3
auxSrClkPin = 18 # A4
auxRClkPin = 19 # A5


def init(board: pymata4.Pymata4) -> None:
	"""Initializes output variables and board pins.
	
	:param board: The arduino board to set up.
	"""

	board.set_pin_mode_digital_output(auxSerPin)
	board.set_pin_mode_digital_output(auxSrClkPin)
	board.set_pin_mode_digital_output(auxRClkPin)

	SevenSeg.init(board)
	ShiftReg.init(auxSerPin, auxSrClkPin, auxRClkPin)

	reset()


def set_maintenance_LEDs(board: pymata4.Pymata4, state: bool) -> None:
	global maintenanceLEDsState, outputsModified

	maintenanceLEDsState = state
	outputsModified = True
	write_outputs(board)


def reset(board: pymata4.Pymata4) -> None:
	"""Shuts off all outputs.
	
	:param board: The Pymata4 board.
	"""

	global trafficStage, trafficStageTimer, lastUpdateTime, currentStageTime
	global mainLightStates, sideLightStates, pedLightStates, overHeightBuzzerState, overHeightLEDState, maintenanceLEDsState, stage4BuzzerState, stage5BuzzerState, outputsModified
	global overHeightBuzzerTimer, overHeightLEDTimer
	global sevenSegRefreshes
	
	trafficStage = 0
	trafficStageTimer = stageTimes[0]
	currentStageTime = 0
	lastUpdateTime = time.time()
	sevenSegRefreshes = 0

	reset(board)
	for i in range(3):
		mainLightStates[i] = 0
		sideLightStates[i] = 0

		if i != 2:
			pedLightStates[i] = 0
	
	overHeightBuzzerState = 0
	overHeightLEDState = 0
	maintenanceLEDsState = 0
	stage4BuzzerState = 0
	stage5BuzzerState = 0

	overHeightBuzzerTimer = -1
	overHeightLEDTimer = -1

	write_outputs(board, True)


def write_outputs(board: pymata4.Pymata4, forceWrite: bool = False):
	"""Updates the physical output components by pushing new data into the auxillary shift register.
	
	:param board: Pymata4 board.
	:param forceWrite: [optional] Whether to forcefully write the current values, regardless of whether they were modified.
	"""

	global outputsModified 

	if not outputsModified and not forceWrite:
		return

	sequence = []

	sequence += mainLightStates
	sequence += sideLightStates
	sequence += pedLightStates

	sequence.append(overHeightBuzzerState)
	sequence.append(overHeightLEDState)
	sequence.append(maintenanceLEDsState)
	sequence.append(stage4BuzzerState)
	sequence.append(stage5BuzzerState)

	ShiftReg.write_shift_reg(board, auxSerPin, auxSrClkPin, auxRClkPin, sequence, True)

	outputsModified = False


def get_main_light_state() -> int:
	return lightStates[trafficStage][0]


def update_traffic_stage(deltaTime: float) -> None:
	"""Returns the current traffic stage (1-6) based on the time spent in normal operation mode.
	
	:param normalModeTime: Time spent in normal operation mode.

	:returns: (traffic stage, time in current stage, time until next stage).
	Current traffic stage is given as an int, 1-6.
	Time in current traffic stage and time until next traffic stage are given in seconds, as floats.
	"""

	global trafficStageTimer, trafficStage, currentStageTime
	global sevenSegRefreshes

	trafficStageTimer -= deltaTime

	if trafficStageTimer < 0:
		print(f"Nominal 7-segment refresh rate: {currentStageTime / sevenSegRefreshes:.2f} Hz.")

		trafficStage += 1
		trafficStage %= len(stageTimes)
		trafficStageTimer += stageTimes[trafficStage]
		currentStageTime = 0
		sevenSegRefreshes = 0


def update(board: pymata4.Pymata4) -> None:
	"""Operates outputs of the system.
	
	:param board: arduino board
	:param normalModeTime: Time spent in normal operating mode, in seconds (float)
	"""

	global mainLightStates, sideLightStates, pedLightStates, outputsModified, lastUpdateTime
	global trafficStageTimer, currentStageTime
	global overHeightBuzzerState, overHeightBuzzerTimer
	global overHeightLEDState, overHeightLEDTimer
	global stage4BuzzerState, stage5BuzzerState
	global sevenSegRefreshes
	
	deltaTime = time.time() - lastUpdateTime
	lastUpdateTime = time.time()
	currentStageTime += deltaTime

	# In stage 1, set remaining time to 5 seconds if one of the ped buttons is pressed
	pedButtonPressed = InputsSubsystem.pedestrian_button_pressed(board, 0) or \
		InputsSubsystem.pedestrian_button_pressed(board, 1)

	if trafficStage == 0 and pedButtonPressed:
		trafficStageTimer = min(trafficStageTimer, 5)

	prevTrafficStage = trafficStage
	update_traffic_stage(deltaTime)
	stageStates = lightStates[trafficStage]
	
	if trafficStage != prevTrafficStage:
		for i in range(3):
			mainLightStates[i] = stageStates[0] == i
			sideLightStates[i] = stageStates[1] == i

			if i != 2:
				pedLightStates[i] = stageStates[2] == i
		
		stage4BuzzerState = int(trafficStage == 3)
		stage5BuzzerState = int(trafficStage == 4)

		outputsModified = True

	sevenSegMessage = f"SG {trafficStage + 1}: {str(int(stageTimes[trafficStage] - currentStageTime)):2d} s"
	sevenSegMessage += f" - {InputsSubsystem.get_LDR_reading() / 1023:3.0f}"
	SevenSeg.set_message(sevenSegMessage, False)

	blinkState = (currentStageTime % (1 / blinkFrequency)) * blinkFrequency < 0.5
	if stageStates[2] == 2 and blinkState != pedLightStates[1]:
		pedLightStates[1] = blinkState
		outputsModified = True
	
	if InputsSubsystem.get_vehicle_height(board) > heightLimit:
		overHeightBuzzerTimer = 2
		overHeightLEDTimer = 6

		if overHeightBuzzerState == 0 and overHeightLEDState == 0:
			print("WARNING: Vehicle exceeding maximum height detected.")

		if overHeightBuzzerState == 0:
			overHeightBuzzerState = 1
			outputsModified = True

		if overHeightLEDState == 0:
			overHeightLEDState = 1
			outputsModified = True

	if get_main_light_state() == 1 and InputsSubsystem.get_vehicle_distance(board) < yellowLightExtensionDistance:
		trafficStageTimer = max(trafficStageTimer, 3)

	if overHeightBuzzerTimer > 0:
		overHeightBuzzerTimer -= deltaTime

		if overHeightBuzzerTimer <= 0:
			overHeightBuzzerState = 0
			outputsModified = True

	if overHeightLEDTimer > 0:
		overHeightLEDTimer -= deltaTime

		if overHeightLEDTimer <= 0:
			overHeightLEDState = 0
			outputsModified = True

	write_outputs(board)

	prevSevenSegChar = SevenSeg.lastCharDisplayed
	SevenSeg.update(board)

	if SevenSeg.lastCharDisplayed == 0 and prevSevenSegChar != 0:
		sevenSegRefreshes += 1
