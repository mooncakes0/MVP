import time
import sys
from pymata4 import pymata4 as pm


def traffic_operation(board):
    for i in range(4,7):
        board.set_pin_mode_digital_output(i)
    board.digital_write(4,1)
    time.sleep(5)
    board.digital_write(4,0)
    board.digital_write(5,1)
    time.sleep(3)
    board.digital_write(5,0)
    

board = pm.Pymata4()
traffic_operation(board)
