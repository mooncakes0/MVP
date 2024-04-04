# feel free to make it more effeicent im just getting it kind of working so i can test and see whats going on

"""
things to do:
    - the rest of the output requirements 

    - make the code more efficent cause rn its kind of just mentualy going through and stuff and its kinda clunky

    - other stuff im probably forgetting
"""

import time
import inputsSubsystem
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
            # stage 1
            print("stage 1")
            board.digital_write(mainLights[1], 1)
            board.digital_write(sideLights[0], 1)
            board.digital_write(pedLights[0], 1)
            time.sleep(5)
            board.digital_write(mainLights[1], 0)

            # stage 2:
            print("stage 2")
            board.digital_write(mainLights[2], 1)
            time.sleep(3)
            board.digital_write(mainLights[2], 0)

            # stage 3:
            print("stage 3")
            board.digital_write(mainLights[0], 1)
            time.sleep(3)
            board.digital_write(sideLights[0], 0)
            board.digital_write(pedLights[0], 0)

            # stage 4:
            print("stage 4")
            board.digital_write(sideLights[1], 1)
            board.digital_write(pedLights[1], 1)
            time.sleep(5)
            board.digital_write(sideLights[1], 0)

            # stage 5:
            print("stage 5")
            board.digital_write(sideLights[2], 1)
            board.digital_write(pedLights[1], 1) ## need to fix 
            time.sleep(3)
            board.digital_write(sideLights[2], 0)
            board.digital_write(pedLights[1], 0)

            # stage 6:
            print("stage 6")
            board.digital_write(sideLights[0], 1)
            board.digital_write(pedLights[0], 1)
            time.sleep(3)
            board.digital_write(mainLights[0], 0)
            board.digital_write(sideLights[0], 0)
            board.digital_write(pedLights[0], 0)

        except KeyboardInterrupt:
            for i in range(4,12):
                print(i)
                time.sleep(.1)
                board.digital_write(i, 0)
            board.shutdown()
            break


board = pm.Pymata4()

def main():
    traffic_operation()
    output = inputsSubsystem.callback()
    print(output)
    



if __name__ == "__main__":
    main()