# this is a module used for the control of the input sub-system
# created by: jackie hong
# creation date: 03/04/2024
# version: 1.0

# imports
import sys
import time
from pymata4 import pymata4 as pm

# setup variable 
distance = 2
trigger = 12
echo = 13
board = pm.Pymata4()

# call back function that prints out the distance 
def callback(data):
    print(f"distance in cm: {data[distance]}")

def Ultrasonic(board, trigger, echo, callback):
    """
    set 
    """
    board.set_pin_mode_sonar(trigger, echo, callback)
    while True:
        try:
            time.sleep(.01)
            print(f"distance: {board.sonar_read(trigger)}")
        except KeyboardInterrupt:
            board.shutdown()
            sys.exit(0)

def push_button():
    board.set_pin_mode_digital_input(4)
    pressed = 0
    previousState = 0

    while True:
        try:
            time.sleep(.01)
            currentState = board.digital_read(4)
            if currentState[0] != previousState:
                if currentState[0] == 1:
                    pressed += 1
                    print(pressed) 
                previousState = currentState[0]
            else:
                pass
        except KeyboardInterrupt:
            board.shutdown()
            sys,exit(0)

try:
    #Ultrasonic(board, trigger, echo, callback)
    push_button()
    board.shutdown()
except(KeyboardInterrupt, RuntimeError):
    sys.exit(0)
    



while True:
    board.digital_read(pin=None)
    