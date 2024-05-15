"""Module to control a shift register.
Written by: Evgeny Solomin
Created Date: 13/05/2024
Version: 1.1
"""

from pymata4 import pymata4
import time

clockTime = 30*10**-9

def init(board: pymata4.Pymata4, serPin: int, srClkPin: int, rClkPin: int):
	"""Sets up a shift register connected to the given pins.
	
	:param board: Pymata board to write to
	:param serPin: Arduino pin connected to SER on the shift register
	:param srClkPin: Arduino pin connected to SRCLK on the shift register
	:param rClkPin: Arduino pin connected to RCLK on the shift register
	"""
	board.set_pin_mode_digital_output(serPin)
	board.set_pin_mode_digital_output(srClkPin)
	board.set_pin_mode_digital_output(rClkPin)


def write_shift_reg(board: pymata4.Pymata4, serPin: int, srClkPin: int, rClkPin: int, sequence: list[int]|tuple[int], reverse: bool = False) -> None:
	"""Writes a sequence into a shift register and displays the output.
	
	:param board: Pymata board to write to
	:param serPin: Arduino pin connected to SER on the shift register
	:param srClkPin: Arduino pin connected to SRCLK on the shift register
	:param rClkPin: Arduino pin connected to RCLK on the shift register
	:param sequence: A list or tuple of 1s and 0s to write to the shift register.
	:param reverse: Whether to reverse the sequence. By default, the last element of the sequence ends up in the QA output channel.
	"""
	for value in (reversed(sequence) if reverse else sequence):
		board.digital_pin_write(serPin, value)
		
		board.digital_pin_write(srClkPin, 1)
		time.sleep(clockTime)
		board.digital_pin_write(srClkPin, 0)
	board.digital_pin_write(rClkPin, 1)
	time.sleep(clockTime)
	board.digital_pin_write(rClkPin, 0)
