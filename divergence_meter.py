from datetime import datetime
from random import randrange
import time

# try:
#     import RPi.GPIO as GPIO
# except RuntimeError:
#     print(
#         "Error importing RPi.GPIO! This is probably because you need superuser privileges. You can achieve this by using 'sudo' to run your script")

output_channels = [3, 5, 7, 8, 10, 11, 12, 13, 15, 16, 18, 19, 21, 22, 23, 24, 26, 29, 31, 32, 33, 35, 36, 37, 38, 40]

nixie_channel = {0: 29, 1: 31, 2: 33, 3: 35, 4: 37, 5: 36, 6: 38, 7: 40}
data_channel = {0: 7, 1: 11, 2: 13, 3: 15}
light_channel = {'r': 12, 'g': 16, 'b': 18}
state_data = {'0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, ',': 10, '.': 11}

counter = 0

dim_level = {'r': 1, 'g': 1, 'b': 1}
max_dim_level = 249

frame_current = list('        ')
frame_next = time.time()


# def setup_gpio():
#     GPIO.setmode(GPIO.BOARD)
#
#     for i in output_channels:
#         GPIO.setup(i, GPIO.OUT)
#
#
# def teardown_gpio():
#     for i in output_channels:
#         GPIO.output(i, 0)
#
#     GPIO.cleanup()


# def set_nixie(index, state):
#     mapping = state_data[state]
#     strobe = nixie_channel[index]
#
#     GPIO.output(strobe, 1)
#
#     GPIO.output(data_channel[0], mapping & 0x1)
#     GPIO.output(data_channel[1], mapping & 0x2)
#     GPIO.output(data_channel[2], mapping & 0x4)
#     GPIO.output(data_channel[3], mapping & 0x8)
#     time.sleep(0.001)
#
#     GPIO.output(strobe, 0)
#     time.sleep(0.001)


def set_nixie(index, state):
    print(str(index) + ': ' + state)
    time.sleep(0.02)


def set_nixies(nixie_state):
    for i, c in enumerate(nixie_state):
        set_nixie(i, c)


def get_time():
    seconds = str(datetime.now().second).zfill(2)
    minutes = str(datetime.now().minute).zfill(2)
    hours = str(datetime.now().hour).zfill(2)
    separator = '.' if datetime.now().second % 2 == 0 else ','

    return list(hours + '.' + minutes + separator + seconds)


def get_date():
    day = str(datetime.now().day).zfill(2)
    month = str(datetime.now().month).zfill(2)
    year = str(datetime.now().year)[2:4].zfill(2)

    return list(day + '.' + month + '.' + year)


def random_frame():
    states = [key for key in state_data.keys() if key.isdigit()]

    return [states[randrange(0, len(states) - 1)] for c in range(8)]


def update_nixies():
    global frame_next

    nixie_state = random_frame()

    if time.time() > frame_next:
        frame_next += 0.1
        print('frame')

    for i, c in enumerate(frame_current):
        if c != ' ':
            nixie_state[i] = frame_current[i]

    set_nixies(nixie_state)


def set_color(r, g, b):
    dim_level['r'] = r
    dim_level['g'] = g
    dim_level['b'] = b


def update_color():
    rv = get_color_state('r')
    gv = get_color_state('g')
    bv = get_color_state('b')

    print(rv)
    print(gv)
    print(bv)

    # GPIO.output(light_channel['r'], rv)
    # GPIO.output(light_channel['g'], gv)
    # GPIO.output(light_channel['b'], bv)


def get_color_state(color):
    level = dim_level[color]
    modulus = counter % (1 / level) if level != 0 else 1
    return modulus == 0

# setup_gpio()

set_color(0, 0.1, 1)

while True:
    time.sleep(0.9)
    update_nixies()
    update_color()
    counter += 1
    print('------------------------------')

teardown_gpio()
