import time

try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error importing RPi.GPIO! This is probably because you need superuser privileges. You can achieve this by using 'sudo' to run your script")

output_channels = [3, 5, 7, 8, 10, 11, 12, 13, 15, 16, 18, 19, 21, 22, 23, 24, 26, 29, 31, 32, 33, 35, 36, 37, 38, 40]

current_nixie = -1
nixie_channel = {0: 29, 1: 31, 2: 33, 3: 35, 4: 37, 5: 36, 6: 38, 7: 40}
data_channel = {0: 7, 1: 11, 2: 13, 3: 15}
light_channel = {'r': 12, 'g': 16, 'b': 18}
state_data = {'0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, ',': 10, '.': 11}

def setup_gpio():
    GPIO.setmode(GPIO.BOARD)

    for i in output_channels:
        GPIO.setup(i, GPIO.OUT)

def teardown_gpio():
    for i in output_channels:
        GPIO.output(i, 0)

    GPIO.cleanup()

def set_nixie(index, state):
    if (current_nixie != -1):
        GPIO.output(current_nixie, 0)
        time.sleep(0.01)

    mapping = state_data[state]
    GPIO.output(data_channel[0], mapping & 0x1)
    GPIO.output(data_channel[1], mapping & 0x2)
    GPIO.output(data_channel[2], mapping & 0x4)
    GPIO.output(data_channel[3], mapping & 0x8)

    current_nixie = nixie_channel[index]
    GPIO.output(current_on, 1)

def set_color(r, g, b):
    GPIO.output(color_channel['r'], r)
    GPIO.output(color_channel['g'], g)
    GPIO.output(color_channel['b'], b)

setup_gpio()

set_color(0, 1, 1)

for i in range(8):
    set_nixie(i, i)

teardown_gpio()
