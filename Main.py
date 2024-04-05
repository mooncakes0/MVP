"""Main code for Team I07's project Milestone 2
Created by Evgeny Solomin (34977260)
Last modified: 03/04/2024
"""

import time
from pymata4 import pymata4 as pm

# import serviceSubsystem as service
# import inputsSubsystem as inputs
# import outputsSubsystem as outputs

# ===== User modifiable variables ===== 
maintenancePIN = None
maxIncorrectPINInputs = 4
incorrectPINTimeout = 120

# ===== Program constants =====
serviceModeConstant = "service"
normalModeConstant = "normal"
dataObservationModeConstant = "dataObservation"
maintenanceModeConstant = "maintenance"

# ===== Program variables =====
operationMode = None
incorrectPINInputs = 0
PINTimeoutTime = 0


def main():
	"""Main control loop"""
	global operationMode
	operationMode = "service"

	while True:
		if False: # inputs.get_mode_button()
			operationMode = serviceModeConstant

		if operationMode == serviceModeConstant:
			service_mode()
		if operationMode == normalModeConstant:
			normal_operation()

def init():
	"""Initializes program variables"""
	global operationMode
	global incorrectPINInputs
	global PINTimeoutTime

	operationMode = serviceModeConstant
	incorrectPINInputs = 0
	PINTimeoutTime = time.time()

def normal_operation():
	"""Standard operating mode.
	Polls sensors and stores relevant data, as well as operating system outputs."""
	pass

def service_mode():
	"""Allows the user to change operating modes.
	Entering maintenance mode requires correct maintenance mode PIN."""
	global operationMode

	while operationMode == serviceModeConstant:
		print("Available operating modes:")
		print("1. Normal operation")
		print("2. Data observation")
		print("3. Maintenance")

		opModeInput = input("Select operating mode to enter: ")
		match opModeInput:
			case "1":
				operationMode = normalModeConstant
				break
			case "2":
				operationMode = dataObservationModeConstant
				break
			case "3":
				if get_PIN_input():
					operationMode = maintenanceModeConstant
				break

def get_PIN_input():
	"""Gets the user's PIN input.
	Locks out the user after entering the incorrect PIN too many times."""
	global incorrectPINInputs
	global PINTimeoutTime

	if time.time() < PINTimeoutTime:
		print(f"Locked out for another {PINTimeoutTime - time.time():.0f} seconds.")
		return False
	
	while incorrectPINInputs < maxIncorrectPINInputs:
		if incorrectPINInputs != 0:
			print(f"Incorrect PIN entered. {maxIncorrectPINInputs - incorrectPINInputs} attempt(s) remaining.")
		
		PINInput = input("Enter PIN")
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
		

if __name__ == "__main__":
	main()
