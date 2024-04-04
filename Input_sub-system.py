# this is a module used for the control of the input sub-system
# created by: jackie hong
# creation date: 03/04/2024
# version: 1.0

"""
still to do:
    - The rate of distance change that should trigger system alerts for your 
      project is experimentally determined and justified with results.
    - im not sure but ik there is more things to do
"""

# imports
import sys
import time
from pymata4 import pymata4 as pm

# setup variable 
distance = 2
trigger = 12
echo = 13
button = 4
board = pm.Pymata4()

def callback(data):
    print(f"distance in cm: {data[distance]}")

def sensors(board, trigger, echo, buttonPin, callback):
    """
    set pin modes for the ultrasonic sensor and push button.
    logic for detecting number of times button has been prese. 
        Parameters:
            board: 
            trigger: 
            echo:
            buttonpin: the pin number for the button detection input
            callback: the call back function for the displaying the distance recorded by ultrasonic sensor in cm

        returns:
            None as there is no returns
    """
    # sets the pin mode for the ultrasonic sensor and the digital pin for the button
    board.set_pin_mode_sonar(trigger, echo, callback)
    board.set_pin_mode_digital_input(buttonPin)
    # default values for variables used later
    pressed = 0
    previousState = 0

    while True:
        try:
            time.sleep(.01)
            #print(f"distance: {board.sonar_read(trigger)}")

            # check between previous and current button state to determin is button has been pressed
            currentState = board.digital_read(buttonPin)
            if currentState[0] != previousState:
                # check if the current state is 1 or 0 as instances where current and previous are different but current is 0
                if currentState[0] == 1:
                    pressed += 1
                    print(pressed) 
                previousState = currentState[0]
            else:
                pass

        except KeyboardInterrupt:
            board.shutdown()
            sys.exit(0)

def main():
    try:
        sensors(board, trigger, echo, button, callback)
        board.shutdown()
    except(KeyboardInterrupt, RuntimeError):
        sys.exit(0)

if __name__ == "__main__":
    main()
