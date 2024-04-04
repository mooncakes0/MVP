# feel free to make it more effeicent im just getting it kind of working so i can test and see whats going on

"""
things to do:
    - for some reason keyboard interupt dont work correctly and the leds for the pedlights just ignores the digital wrtie to 0 and keep
      the same state as before the keyboard interrupt was pressed BUT SONETIMES IT DOES TURN ALL OF THEM OFF WHAT THE FUCK!!!!!!!!!!!!!!!!!!

    - make the code more efficent cause rn its kind of just mentualy going through and stuff and its kinda clunky

    - other stuff im probably forgetting
"""

import time
import sys
from pymata4 import pymata4 as pm

# list of pins needed for each light system
# index 0 = red,   index 1 = green,     index 2 = yellow
mainLights = [4, 5, 6]
sideLights = [7, 8, 9]
pedLights = [10, 11]

def traffic_operation(board):
    # set all the pins to digital output
    for i in range(4,12):
        board.set_pin_mode_digital_output(i)
    while True:
        try:
            # the actual function of the lights
            # stage 1:
            board.digital_write(mainLights[1], 1)
            board.digital_write(sideLights[0], 1)
            board.digital_write(pedLights[0], 1)
            time.sleep(5)
            board.digital_write(mainLights[1], 0)

            # stage 2:
            board.digital_write(mainLights[2], 1)
            time.sleep(3)
            board.digital_write(mainLights[2], 0)

            # stage 3:
            board.digital_write(mainLights[0], 1)
            time.sleep(3)
            board.digital_write(sideLights[0], 0)
            board.digital_write(pedLights[0], 0)

            # stage 4:
            board.digital_write(sideLights[1], 1)
            board.digital_write(pedLights[1], 1)
            time.sleep(5)
            board.digital_write(sideLights[1], 0)

            # stage 5:
            board.digital_write(sideLights[2], 1)
            board.digital_write(pedLights[1], 1) ## need to fix 
            time.sleep(3)
            board.digital_write(sideLights[2], 0)
            board.digital_write(pedLights[1], 0)

            # stage 6:
            board.digital_write(sideLights[0], 1)
            board.digital_write(pedLights[0], 1)
            time.sleep(3)
            board.digital_write(mainLights[0], 0)
            board.digital_write(sideLights[0], 0)
            board.digital_write(pedLights[0], 0)

        except KeyboardInterrupt:
            for i in range(4,12):
                print(i)
                board.digital_write(i, 0)
            board.shutdown()
            sys.exit(0)

board = pm.Pymata4()
traffic_operation(board)
