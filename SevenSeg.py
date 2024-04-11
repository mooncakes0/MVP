"""Module to output to a seven segment display.
Created by: Evgeny Solomin.
Created Date: 08/04/2024.
Version: 1.1
"""

from pymata4 import pymata4
import time

sevenSegPins = [2, 3, 4, 5, 6, 7, 8]
segmentEnablePins = (9, 10, 11, 12)

lookupTable = {
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
	"Y": (0, 1, 1, 0, 0, 1, 1),
	"Z": (1, 1, 0, 1, 1, 0, 1),
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
	"t": (0, 0, 0, 0, 1, 1, 1),
	"u": (0, 0, 1, 1, 1, 0, 0)
}

messages = ["Ab12", "HELP", "M2"]
messageTime = 3


def display_message(board: pymata4.Pymata4, message: str) -> None:
	"""Displays a message on the seven segment display."""

	if len(message) > 4:
		message = message[0:4]

	for i in range(0, min(4, len(message))):
		char = message[-1 - i]
		if char in lookupTable:
			show_character(board, char, 3 - i)
		elif char.swapcase() in lookupTable:
			show_character(board, char.swapcase(), 3 - i)


def show_character(board: pymata4.Pymata4, char: str, index: int) -> None:
	"""Displays a character on a given segment of the seven segment display.
	
	:param board: Arduino board.
	:param char: Character to display.
	:param index: 7-seg character index.
	"""

	for i in range(4):
		board.digital_write(segmentEnablePins[i], i == index)
	
	states = lookupTable[char]
	for i in range(7):
		board.digital_write(sevenSegPins[i], states[i])


def get_message(time: float) -> str:
	"""Gets the message that should currently be displayed.
	
	:param time: current time (since startup).

	:returns: Message to display, as a string.
	"""

	messageIndex = time % (len(messages) * messageTime) // messageTime
	return messages[messageIndex]


if __name__ == "__main__":
	board = pymata4.Pymata4()
	initialTime = time.time()

	while True:
		try:
			display_message(board, get_message(time.time() - initialTime))
		except KeyboardInterrupt:
			break
	
	board.shutdown()
