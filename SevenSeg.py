"""Module to control a seven segment display using a shift register for the digits.
Written by: Evgeny Solomin
Created Date: 13/05/2024
Version: 1.2
"""

import time
from pymata4 import pymata4
import ShiftReg

lookupTable: dict[str, tuple[int]] = {
	" ": (0, 0, 0, 0, 0, 0, 0),
	".": (0, 0, 0, 1, 0, 0, 0),
	",": (0, 0, 1, 0, 0, 0, 0),
	"-": (0, 0, 0, 0, 0, 0, 1),
	"=": (0, 0, 0, 1, 0, 0, 1),
	"0": (1, 1, 1, 1, 1, 1, 0),
	"1": (0, 1, 1, 0, 0, 0, 0),
	"2": (1, 1, 0, 1, 1, 0, 1),
	"3": (1, 1, 1, 1, 0, 0, 1),
	"4": (0, 1, 1, 0, 0, 1, 1),
	"5": (1, 0, 1, 1, 0, 1, 1),
	"6": (1, 0, 1, 1, 1, 1, 1),
	"7": (1, 1, 1, 0, 0, 0, 0),
	"8": (1, 1, 1, 1, 1, 1, 1),
	"9": (1, 1, 1, 1, 0, 1, 1),
	"A": (1, 1, 1, 0, 1, 1, 1),
	"B": (1, 1, 1, 1, 1, 1, 1),
	"C": (1, 0, 0, 1, 1, 1, 0),
	"D": (1, 1, 1, 1, 1, 1, 0),
	"E": (1, 0, 0, 1, 1, 1, 1),
	"F": (1, 0, 0, 0, 1, 1, 1),
	"G": (1, 0, 1, 1, 1, 1, 0),
	"H": (0, 1, 1, 0, 1, 1, 1),
	"I": (0, 0, 0, 0, 1, 1, 0),
	"J": (0, 1, 1, 1, 0, 0, 0),
	"L": (0, 0, 0, 1, 1, 1, 0),
	"O": (1, 1, 1, 1, 1, 1, 0),
	"P": (1, 1, 0, 0, 1, 1, 1),
	"S": (1, 0, 1, 1, 0, 1, 1),
	"U": (0, 1, 1, 1, 1, 1, 0),
	"V": (0, 1, 1, 1, 1, 1, 0),
	"Y": (0, 1, 1, 1, 0, 1, 1),
	"Z": (1, 1, 0, 1, 1, 0, 1),
	"a": (1, 1, 1, 1, 1, 0, 1),
	"b": (0, 0, 1, 1, 1, 1, 1),
	"c": (0, 0, 0, 1, 1, 0, 1),
	"d": (0, 1, 1, 1, 1, 0, 1),
	"g": (1, 1, 1, 1, 0, 1, 1),
	"h": (0, 0, 1, 0, 1, 1, 1),
	"i": (1, 0, 1, 0, 0, 0, 0),
	"j": (0, 0, 1, 1, 0, 0, 0),
	"l": (0, 1, 1, 0, 0, 0, 0),
	"n": (0, 0, 1, 0, 1, 0, 1),
	"o": (0, 0, 1, 1, 1, 0, 1),
	"q": (1, 1, 1, 0, 0, 1, 1),
	"r": (0, 0, 0, 0, 1, 0, 1),
	"t": (0, 0, 0, 1, 1, 1, 1),
	"u": (0, 0, 1, 1, 1, 0, 0)
}

lastCharDisplayed = 0
currentMessage = ' ' * 4
messageStartTime = 0
messageScrollSpeed = 0.7

serPin = 7
srClkPin = 8
rClkPin = 9

digitPins = [10, 11, 12, 13]

def init(board: pymata4.Pymata4):
	"""Sets up the connected board.
	
	:param board: Pymata board
	"""
	ShiftReg.init(board, serPin, srClkPin, rClkPin)
	for pin in digitPins:
		board.set_pin_mode_digital_output(pin)


def set_message(message: str, resetScroll: bool = True):
	"""Sets the message displayed on the seven segment display.
	
	:param message: New message to show
	:param resetScroll: Whether to reset the message scrolling or to continue where it was before.
	Message scrolling will reset regardless of this parameter if the new message is a different length.
	"""
	global currentMessage, messageStartTime

	prevMessageLen = len(currentMessage)

	# If the message is less than 4 characters in length, the scrolling will need to act slightly differently
	if len(message) < 4:
		currentMessage = message.rjust(4) + ' ' * (4 - len(message))
		if len(message) > 1:
			currentMessage += message[0:-2]
	else:
		# If the message is at least 4 characters, make the stored message string the message, 4 spaces and the first 3 characters of the new message
		currentMessage = message + "    " + message[0:3]
	
	if resetScroll or len(currentMessage) != prevMessageLen:
		messageStartTime = time.time()


def update(board: pymata4.Pymata4) -> None:
	"""Refreshes the seven segment display to show the next character in the message and scrolls the message.

	:param board: Connected pymata board.
	"""
	global lastCharDisplayed

	# Calculate the current scroll position by dividing the time since the message was set by the time per scroll
	# Then, take that mod (stored message length - 3), which will tell us the beginning of the "window" for the current 4 characters to show on the screen
	messageScroll = int(((time.time() - messageStartTime) // messageScrollSpeed) % (len(currentMessage) - 3))
	# Create a submessage which discards all the characters before the "window"
	subMessage = currentMessage[messageScroll:]

	currentChar = subMessage[lastCharDisplayed]
	charSequence = [0] * 7
	if currentChar in lookupTable:
		charSequence = lookupTable[currentChar]
	elif currentChar.swapcase() in lookupTable:
		charSequence = lookupTable[currentChar.swapcase()]
	
	ShiftReg.write_shift_reg(board, serPin, srClkPin, charSequence, True)

	for pin in digitPins:
		board.digital_write(pin, 1)
	ShiftReg.display_output(board, rClkPin)
	board.digital_write(digitPins[lastCharDisplayed], 0)

	lastCharDisplayed += 1
	lastCharDisplayed %= 4


def reset(board: pymata4.Pymata4) -> None:
	"""Clears the output of the seven segment display.
	
	:param board: Pymata board
	"""

	global messageStartTime

	for pin in digitPins:
		board.digital_write(pin, 1)
	ShiftReg.write_shift_reg(board, serPin, srClkPin, [0] * 7)
	ShiftReg.display_output(board, rClkPin)

	messageStartTime = time.time()

if __name__ == "__main__":
	board = pymata4.Pymata4()

	time.sleep(1)

	init(board)

	set_message("HELLO I LIVE")
	# set_message("1234567890")

	# board.set_pin_mode_analog_input(0)

	try:
		while True:
			update(board)
	except KeyboardInterrupt:
		pass

	print("Shutting down...")
	reset(board)
	time.sleep(1)
	board.shutdown()
