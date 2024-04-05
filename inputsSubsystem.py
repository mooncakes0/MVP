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
import time
from pymata4 import pymata4

# setup variable 
trigger = 12
echo = 13
button = 3

previousState = 0


def init(board: pymata4.Pymata4) -> None:
    """Initializes input variables and board pins."""
    board.set_pin_mode_sonar(trigger, echo)
    board.set_pin_mode_digital_input(button)


def get_filtered_ultrasonic(board: pymata4.Pymata4) -> float | None:
    """Polls the ultrasonic sensor several times and averages the result, discarding any outliers.
    
    :param board: The arduino board to read from.

    :returns: The filtered, averaged distance read from the ultrasonic sensor. Returns None if all readings were considered outliers.
    """
    target = 15
    total = 0
    i = 0
    
    time.sleep(0.5)

    while i < target:
        reading = board.sonar_read(trigger)
        total += reading[0]
        # print(f"distance: {reading}")
        i += 1
    average = total / target
    return average


def pedestrian_button_pressed(board: pymata4.Pymata4) -> bool:
    """Returns whether the pedestrian button was pressed since the last call of this function.
    Debounces the button input in the process.
    
    :param board: The arduino board to read from.

    :returns: Whether or not the button was pressed.
    """
    global button, previousState
    currentState = board.digital_read(button)
    if currentState[0] != previousState:
        previousState = currentState[0]
        # check if the current state is 1 or 0 as instances where current and previous are different but current is 0
        if currentState[0] == 1:
            return True
    return False