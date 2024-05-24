"""Module to control a shift register.
Written by: Evgeny Solomin
Created Date: 13/05/2024
Version: 1.2
"""

from pymata4 import pymata4
import time

clockTime_ns = 10*10**5

def init(board: pymata4.Pymata4, serPin: int, srClkPin: int, rClkPin: int) -> None:
	"""Sets up a shift register connected to the given pins.
	
	:param board: Pymata board to write to
	:param serPin: Arduino pin connected to SER on the shift register
	:param srClkPin: Arduino pin connected to SRCLK on the shift register
	:param rClkPin: Arduino pin connected to RCLK on the shift register
	"""
	board.set_pin_mode_digital_output(serPin)
	board.set_pin_mode_digital_output(srClkPin)
	board.set_pin_mode_digital_output(rClkPin)


def better_sleep(time_ns: float) -> None:
	"""A more accurate but more resource-intensive sleep statement.
	
	:param time_ns: Time to sleep for, in nanoseconds
	"""
	target = time.perf_counter_ns() + time_ns
	while time.perf_counter_ns() < target:
		pass


def write_shift_reg(board: pymata4.Pymata4, serPin: int, srClkPin: int, sequence: list[int]|tuple[int], reverse: bool = False) -> None:
	"""Writes a sequence into the internal state storage of a shift register, but does not display it.
	
	:param board: Pymata4 board
	:param serPin: Arduino pin connected to SER on the shift register
	:param srClkPin: Arduino pin connected to SRCLK on the shift register
	:param sequence: A list or tuple of 1s and 0s to write to the shift register.
	:param reverse: Whether to reverse the sequence. By default, the last element of the sequence ends up in the QA output channel.
	"""
	for value in (reversed(sequence) if reverse else sequence):
		board.digital_write(serPin, value)
		
		board.digital_write(srClkPin, 1)
		better_sleep(clockTime_ns)
		# writeBegin = time.perf_counter_ns()
		board.digital_write(srClkPin, 0)
		# writeEnd = time.perf_counter_ns()
		# print(f"Shift reg write took {writeEnd - writeBegin} ns.")

def display_output(board: pymata4.Pymata4, rClkPin: int) -> None:
	"""Displays the output stored in the shift register connected to the RCLK pin.
	
	:param rClkPin: Pin number of pin connected to shift register RCLK terminal
	"""
	board.digital_write(rClkPin, 1)
	better_sleep(clockTime_ns)
	board.digital_write(rClkPin, 0)
