from collections import deque, namedtuple
from datetime import datetime
import random
import time

# try:
#     import RPi.GPIO as GPIO
# except RuntimeError:
#     print(
#         "Error importing RPi.GPIO! This is probably because you need superuser privileges. You can achieve this by using 'sudo' to run your script")
from operator import itemgetter

output_channels = [3, 5, 7, 8, 10, 11, 12, 13, 15, 16, 18, 19, 21, 22, 23, 24, 26, 29, 31, 32, 33, 35, 36, 37, 38, 40]

nixie_channel = {0: 29, 1: 31, 2: 33, 3: 35, 4: 37, 5: 36, 6: 38, 7: 40}
data_channel = {0: 7, 1: 11, 2: 13, 3: 15}
light_channel = {'r': 12, 'g': 16, 'b': 18}
state_channel = {'0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, ',': 10, '.': 11,
                 '_': 15}

counter = 0

dim_level = {'r': 1, 'g': 1, 'b': 1}
max_dim_level = 249

nixie_state = list('        ')
frame_next = time.time()

State = namedtuple('State', 'probability animation')


class Config:
    active = 0

    def __init__(self, duration_min, duration_max, states: [State]):
        self.duration_min = duration_min
        self.duration_max = duration_max
        self.states = states
        self.next_change = time.clock() + random.randrange(duration_min, duration_max)

    def current_state(self) -> State:
        return self.states[self.active]

    def current_animation(self):
        return self.current_state().animation()

    def update(self):
        if time.clock() > self.next_change:
            self.next_change = time.clock() + random.randrange(self.duration_min, self.duration_max)
            self.active = weighted_choice(list(enumerate(map(itemgetter(0), self.states))))


config = {
    'TIME_SEPARATOR_MODE': Config(30, 60, [
        State(80, lambda: '.' if datetime.now().second % 2 == 0 else ','),  # left-right
        State(7, lambda: '.'),  # left
        State(7, lambda: ','),  # right
        State(1, lambda: '.' if datetime.now().second % 2 == 0 else '_'),  # left-blink
        State(1, lambda: ',' if datetime.now().second % 2 == 0 else '_'),  # right-blink
        State(2, lambda: random.choice(['.', ',', '_'])),  # random
        State(2, lambda: '_'),  # blank
    ]),
}


def weighted_choice(choices):
    total = sum(map(itemgetter(1), choices))
    rand = random.uniform(0, total)
    for choice, weight in choices:
        rand -= weight
        if rand <= 0:
            return choice
    assert False, "Shouldn't get here"


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
#     mapping = state_channel[state]
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
    print(state, end='')
    time.sleep(0.0001)


def set_nixies():
    for i, state in enumerate(nixie_state):
        set_nixie(i, state)
    print()


def get_time():
    seconds = str(datetime.now().second).zfill(2)
    minutes = str(datetime.now().minute).zfill(2)
    hours = str(datetime.now().hour).zfill(2)
    separator = config['TIME_SEPARATOR_MODE'].current_animation()

    return list(hours + '.' + minutes + separator + seconds)


def get_date():
    day = str(datetime.now().day).zfill(2)
    month = str(datetime.now().month).zfill(2)
    year = str(datetime.now().year)[2:4].zfill(2)

    return list(day + '.' + month + '.' + year)


divergence_lines = ['1.130212', '1.130205', '1.130426', '1.130238', '1.048596', '0.571024', '0.571046', '0.523299',
                    '0.523307', '0.456903', '0.456914', '0.409420', '0.337187', '_.275349']


def get_divergence(i):
    return divergence_lines[i]


digit_states = [key for key in state_channel.keys() if key.isdigit()]


def random_state():
    return random.choice(digit_states)


def random_frame():
    return [random_state() for _ in range(8)]


def scramble_single(i, f):
    return [random_state().ljust(7 - i).rjust(i + 1) for _ in range(f)]


def update_nixies():
    global frame_next
    global nixie_state

    if time.time() > frame_next:
        frame_next += 0.25

        previous_state = nixie_state
        nixie_state = get_time()

        if frame_animation:
            frame_current = frame_animation.popleft()

            for i, c in enumerate(frame_current):
                if c != ' ':
                    nixie_state[i] = c

        if nixie_state != previous_state:
            set_nixies()


def set_color(r, g, b):
    dim_level['r'] = r
    dim_level['g'] = g
    dim_level['b'] = b


def update_color():
    rv = get_color_state('r')
    gv = get_color_state('g')
    bv = get_color_state('b')

    # print(rv)
    # print(gv)
    # print(bv)

    # GPIO.output(light_channel['r'], rv)
    # GPIO.output(light_channel['g'], gv)
    # GPIO.output(light_channel['b'], bv)


def get_color_state(color):
    level = dim_level[color]
    modulus = counter % (1 / level) if level != 0 else 1
    return modulus == 0


# setup_gpio()

set_color(0, 0.1, 1)
frame_animation = deque()
# frame_animation += scramble_single(7, 20)

while True:
    update_nixies()
    update_color()
    for c in config.values():
        c.update()
    counter += 1

teardown_gpio()
