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
	0: (2, 0, 0),
	1: (1, 0, 0),
	2: (0, 0, 0),
	3: (0, 2, 1),
	4: (0, 1, 2),
	5: (0, 0, 0)
}
blinkFrequency = 3 # in hertz
heightLimit = 20
yellowLightExtensionDistance = 30

trafficStage = 0

trafficStageTimer = 0
currentStageTime = 0
lastUpdateTime = 0

sevenSegRefreshes = 0
yellowLightExtensionUsed = False

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
	ShiftReg.init(board, auxSerPin, auxSrClkPin, auxRClkPin)

	SevenSeg.set_message("HELLO")

	reset(board)
	write_outputs(board)


def set_maintenance_LEDs(board: pymata4.Pymata4, state: bool) -> None:
	"""Turns the maintenance mode flashing LEDs on or off.
	
	:param board: Pymata4 board.
	:param state: Whether to turn the LEDs on or off.
	"""
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
	global sevenSegRefreshes, yellowLightExtensionUsed
	
	trafficStage = 0
	trafficStageTimer = stageTimes[0]
	currentStageTime = 0
	lastUpdateTime = time.time()
	sevenSegRefreshes = 0
	yellowLightExtensionUsed = False

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
	outputsModified = True

	SevenSeg.reset(board)


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

	ShiftReg.write_shift_reg(board, auxSerPin, auxSrClkPin, sequence, True)
	ShiftReg.display_output(board, auxRClkPin)

	outputsModified = False


def get_main_light_state() -> int:
	"""Gets the current state of the main road traffic lights.
	
	:returns: Main traffic light state. 0 is red, 1 is yellow, 2 is green.
	"""
	return lightStates[trafficStage][0]


def update_traffic_stage(deltaTime: float) -> None:
	"""Updates the current traffic stage.
	
	:param deltaTime: Time since the last call to this function.
	"""

	global trafficStageTimer, trafficStage, currentStageTime
	global sevenSegRefreshes, yellowLightExtensionUsed

	trafficStageTimer -= deltaTime

	if trafficStageTimer < 0:
		if sevenSegRefreshes:
			print(f"Nominal 7-segment refresh rate: {sevenSegRefreshes / currentStageTime:.2f} Hz.")

		trafficStage += 1
		trafficStage %= len(stageTimes)
		trafficStageTimer = stageTimes[trafficStage]
		currentStageTime = 0
		sevenSegRefreshes = 0
		yellowLightExtensionUsed = False


def update(board: pymata4.Pymata4, vehicleDistace: float, vehicleHeight: float) -> None:
	"""Operates outputs of the system.
	
	:param board: arduino board
	"""

	global mainLightStates, sideLightStates, pedLightStates, outputsModified, lastUpdateTime
	global trafficStageTimer, currentStageTime
	global overHeightBuzzerState, overHeightBuzzerTimer
	global overHeightLEDState, overHeightLEDTimer
	global stage4BuzzerState, stage5BuzzerState
	global sevenSegRefreshes, yellowLightExtensionUsed
	
	deltaTime = time.time() - lastUpdateTime
	lastUpdateTime = time.time()
	currentStageTime += deltaTime

	# In stage 1, set remaining time to 5 seconds if one of the ped buttons is pressed
	pedButtonPressed = InputsSubsystem.pedestrian_button_pressed(0) or \
		InputsSubsystem.pedestrian_button_pressed(1)

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
		
	sevenSegMessage = f"SG {trafficStage + 1} {str(int(trafficStageTimer)).rjust(2)}s "
	if InputsSubsystem.is_night(board):
		sevenSegMessage += "night"
	else:
		sevenSegMessage += "day"
	SevenSeg.set_message(sevenSegMessage, False)

	blinkState = (currentStageTime % (1 / blinkFrequency)) * blinkFrequency < 0.5
	if stageStates[2] == 2 and blinkState != pedLightStates[1]:
		pedLightStates[1] = blinkState
		outputsModified = True
	
	if vehicleHeight > heightLimit:
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

	if get_main_light_state() == 1 and vehicleDistace < yellowLightExtensionDistance and not yellowLightExtensionUsed:
		trafficStageTimer += 3
		yellowLightExtensionUsed = True

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
