# feel free to make it more effeicent im just getting it kind of working so i can test and see whats going on

"""
things to do:
    - the rest of the output requirements 

    - make an init() function (takes the board as an argument) that initializes variables and board pins

    - make a function that takes the current time in normal operation and determines the current traffic stage (time in normal operation mode will be passed in from main)

    - make the output function run alongside the main code

    - make the output function print traffic stage every time it changes

    - add a function to display a message to the 7-seg display

    - make the code more efficent cause rn its kind of just mentualy going through and stuff and its kinda clunky

    - other stuff im probably forgetting
"""

from pymata4 import pymata4 as pm

# list of pins needed for each light system
# index 0 = red,   index 1 = yellow,     index 2 = green
# for pedestrian lights, 0 is red, 1 is green
mainLights = [4, 5, 6]
sideLights = [7, 8, 9]
pedLights = [10, 11]

# the state of each light during each traffic stage
# first column is main lights
# second is side road lights
# third is pedestrian lights
# for pedestrian lights, 2 means flashing green
lightStates = {
    1: (2, 0, 0),
    2: (1, 0, 0),
    3: (0, 0, 0),
    4: (0, 2, 1),
    5: (0, 1, 2),
    6: (0, 0, 0)
}
blinkFrequency = 3 # in hertz

lastTrafficStage = -1
stageTimes = (30, 3, 3, 30, 3, 3)


def init(board: pm.Pymata4) -> None:
    """Initializes output variables and board pins.
    
    :param board: The arduino board to set up.
    """
    for i in (mainLights + sideLights + pedLights):
        board.set_pin_mode_digital_output(i)


# fill this out <<<<<<<<<<
def shutdown(board: pm.Pymata4) -> None:
    """Does any required cleanup.
    
    :param board: The arduino board to shut down.
    """

    for i in (mainLights + sideLights + pedLights):
        board.digital_write(i, 0)


def get_traffic_stage(normalModeTime: float) -> tuple[int, float]:
    """Returns the current traffic stage (1-6) based on the time spent in normal operation mode.
    
    :param normalModeTime: Time spent in normal operation mode.

    :returns: Current traffic stage as an integer 1-6 and time until next traffic stage as a float.
    """

    totalStageTime = sum(stageTimes)
    timeMod = normalModeTime % totalStageTime
    runningTotal = 0
    for i in range(len(stageTimes)):
        if timeMod - runningTotal < stageTimes[i]:
            return (i + 1, stageTimes[i] - (timeMod - runningTotal))
        runningTotal += stageTimes[i]
    return len(stageTimes)

def traffic_operation(board: pm.Pymata4, normalModeTime: float) -> None:
    global lastTrafficStage
    
    currentStage = get_traffic_stage(normalModeTime)[0]
    stageStates = lightStates[currentStage]
    
    if currentStage != lastTrafficStage:
        for i in range(3):
            board.digital_write(mainLights[i], stageStates[0] == i)
            board.digital_write(sideLights[i], stageStates[1] == i)

            if i != 2:
                board.digital_write(pedLights[i], stageStates[2] == i)

    if stageStates[2] == 2:
        board.digital_write(pedLights[1], (normalModeTime % (1/blinkFrequency)) * blinkFrequency < 0.5)

    lastTrafficStage = currentStage
