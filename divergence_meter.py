from collections import deque, namedtuple
from datetime import datetime
import random
import time
import math

try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print(
        "Error importing RPi.GPIO! This is probably because you need superuser privileges. You can achieve this by using 'sudo' to run your script")
from operator import itemgetter

# all gpio pins that need to be initialized
output_channels = [3, 5, 7, 8, 10, 11, 12, 13, 15, 16, 18, 19, 21, 22, 23, 24, 26, 29, 31, 32, 33, 35, 36, 37, 38, 40]

# nixie index -> pulsing gpio pin
nixie_channel = {0: 29, 1: 31, 2: 33, 3: 35, 4: 37, 5: 36, 6: 38, 7: 40}
# data bits -> gpio pin
data_channel = {0: 7, 1: 11, 2: 13, 3: 15}
# rgb -> gpio pin
light_channel = {'r': 12, 'g': 16, 'b': 18}
# nixie char -> data bits
state_channel = {'0': 1, '1': 10, '2': 9, '3': 8, '4': 7, '5': 6, '6': 5, '7': 4, '8': 3, '9': 2, ',': 0, '.': 11, '_': 15}
# binary mappings for testing
# state_channel = {'0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, ',': 10, '.': 11, '_': 12}

# continuous counter used for animation
counter = 0

# current states of the leds
color = {'r': 1, 'g': 1, 'b': 1}

# current state of the nixies as char list
nixie_state = list('        ')
# time to display next frame
frame_next = time.time()

# tuple for representing a state of a multi state overlay as for example a time separator
State = namedtuple('State', 'probability animation')


class Config:  # config class for multiple possible overlay states
    active = 0  # the currently active state

    def __init__(self, duration_min, duration_max, states: [State]):
        self.duration_min = duration_min
        self.duration_max = duration_max
        self.states = states
        self.next_change = time.clock() + random.randrange(duration_min, duration_max)

    def current_animation(self):  # get the current overlay from this config
        return self.states[self.active].animation()

    def update(self):  # change the current overlay state that should be displayed based on constructor parameters
        if time.clock() > self.next_change:  # check if the state should change
            self.next_change = time.clock() + random.randrange(self.duration_min,
                                                               self.duration_max)  # calculate the next time for a change
            self.active = weighted_choice(list(enumerate(map(itemgetter(0), self.states))))  # calculate the next state


configs = {
    'TIME_SEPARATOR_MODE': Config(30, 60, [  # config for separator between minutes and seconds
        State(80, lambda: '.' if datetime.now().second % 2 == 0 else ','),  # left-right
        State(7, lambda: '.'),  # left
        State(7, lambda: ','),  # right
        State(1, lambda: '.' if datetime.now().second % 2 == 0 else '_'),  # left-blink
        State(1, lambda: ',' if datetime.now().second % 2 == 0 else '_'),  # right-blink
        State(2, lambda: random.choice(['.', ',', '_'])),  # random
        State(2, lambda: '_'),  # blank
    ]),
}


def weighted_choice(choices):  # make a weighted random choice between the give possibilities
    total = sum(map(itemgetter(1), choices))
    rand = random.uniform(0, total)
    for choice, weight in choices:
        rand -= weight
        if rand <= 0:
            return choice
    assert False, "Shouldn't get here"


def setup_gpio():  # initialize the gpio pins
    GPIO.setmode(GPIO.BOARD)

    for i in output_channels:
        GPIO.setup(i, GPIO.OUT)


def teardown_gpio():  # reset the gpio pins
    for i in output_channels:
        GPIO.output(i, 0)

    GPIO.cleanup()


def set_nixie(index, state):  # set a single nixie on position 'index' (from 0 to 7) to 'state' ('0' through '9', ',', '.' or '_')
    mapping = state_channel[state]
    strobe = nixie_channel[index]

    GPIO.output(data_channel[0], mapping & 0x1)
    GPIO.output(data_channel[1], mapping & 0x2)
    GPIO.output(data_channel[2], mapping & 0x4)
    GPIO.output(data_channel[3], mapping & 0x8)

    GPIO.output(strobe, 1)
    #time.sleep(0.00002)

    GPIO.output(strobe, 0)
    #time.sleep(0.00002)


def set_nixies():  # set all nixies from the 'nixie_state'
    for i, state in enumerate(nixie_state):
        set_nixie(i, state)


def get_time():  # get the time as nixie_state string
    seconds = str(datetime.now().second).zfill(2)
    minutes = str(datetime.now().minute).zfill(2)
    hours = str(datetime.now().hour).zfill(2)
    separator = configs['TIME_SEPARATOR_MODE'].current_animation()

    return list(hours + '.' + minutes + separator + seconds)


def get_date():  # get the date as nixie_state string
    day = str(datetime.now().day).zfill(2)
    month = str(datetime.now().month).zfill(2)
    year = str(datetime.now().year)[2:4].zfill(2)

    return list(day + '.' + month + '.' + year)


# list of all valid divergence lines
divergence_lines = ['1.130212', '1.130205', '1.130426', '1.130238', '1.048596', '0.571024', '0.571046', '0.523299',
                    '0.523307', '0.456903', '0.456914', '0.409420', '0.337187', '_.275349']


def get_divergence(i):  # get a divergence line as nixie_state string
    return divergence_lines[i]


# list of all nixie states that represent digits
digit_states = [key for key in state_channel.keys() if key.isdigit()]


def clear_frame():  # return an nixie_state where every place has a random digit
    return ['_' for _ in range(8)]


def random_state():  # return an random digit
    return random.choice(digit_states)


def random_frame():  # return an nixie_state where every place has a random digit
    return [random_state() for _ in range(8)]


def scramble_single(index, frames):  # generate an scramble overlay for nixie 'index' lasting 'frames' frames
    return [random_state().ljust(8 - index).rjust(8) for _ in range(frames)]


def update_nixies():  # update the nixies according to the shown stuff and the overlays
    global frame_next
    global nixie_state

    if time.time() > frame_next:  # if it's time for the next frame
        frame_next += 0.05  # set the time for the next frame

        previous_state = nixie_state
        nixie_state = get_time()  # set the basic displayed stuff

        if frames_animation:  # if there is something in the animation list
            frame_current = frames_animation.popleft()  # get the first element

            for i, c in enumerate(frame_current):
                if c != ' ':  # change the nixie_state where there is no ' ' in the overlay
                    nixie_state[i] = c

        nixie_state.reverse()

        if nixie_state != previous_state:  # if the state was changed set the nixies
            set_nixies()


def animation_append(frames):
    global frames_animation

    if len(frames) != 0 and not isinstance(frames[0], list):
        frames = [frames]

    frames_animation += frames


def animation_insert(frames, offset=0):
    global frames_animation

    print("inserting " + str(frames) + " at offset " + str(offset))

    if not isinstance(frames, list):
        frames = [frames]

    end_frame = len(frames) + offset
    new_frames = end_frame - len(frames_animation)
    new_frames = new_frames if new_frames > 0 else 0

    for i in range(new_frames):
        frames_animation += [list('        ')]

    for i, frame in enumerate(frames):
        frame_animation = frames_animation[i + offset]
        print("begin frame " + str(i))
        print("frame: '" + str(frame) + "'")
        print("begin anim " + str(i + offset))
        print("current anim: " + str(frame_animation))

        for pos, c in enumerate(frame):
            print("pos " + str(pos) + ': ' + c)
            if frame[pos] != ' ':
                frame_animation[pos] = c


def update_color():  # update the gpio output for the leds
    rv = get_color_state(color['r'])
    gv = get_color_state(color['g'])
    bv = get_color_state(color['b'])

    # print(str(rv) + ' ' + str(gv) + ' ' + str(bv))

    GPIO.output(light_channel['r'], rv)
    GPIO.output(light_channel['g'], gv)
    GPIO.output(light_channel['b'], bv)


def get_color_state(
        level):  # calculate if the led should be on or off in this frame for reaching 'level' percent of on time
    modulus = int(counter % (1 / level) if level != 0 else 1)
    return modulus == 0
    # return level > 0.5


def colorflow():  # set the rgb values so that color flows
    color['r'] = math.sin(math.radians(counter / 40) + math.pi * 4 / 3) / 2 + 0.5
    color['r'] = round(color['r'], 2)
    if color['r'] < 0.02:
        color['r'] = 0.0
    # print(color['r'])
    color['g'] = math.sin(math.radians(counter / 40) + math.pi * 2 / 3) / 2 + 0.5
    color['g'] = round(color['g'], 2)
    if color['g'] < 0.02:
        color['g'] = 0.0
    # print(color['g'])
    color['b'] = math.sin(math.radians(counter / 40) + math.pi * 0 / 3) / 2 + 0.5
    color['b'] = round(color['b'], 2)
    if color['b'] < 0.02:
        color['b'] = 0.0
        # print(color['b'])


def test_nixies():
    print('testing nixies ...')
    for i in range(8):
        set_nixie(i, '_')
    for i in range(8):
        for c in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ',', '.', '_']:
            set_nixie(i, str(c))
            time.sleep(0.125)
    for c in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ',', '.', '_']:
        for i in range(8):
            set_nixie(i, c)
        time.sleep(0.5)
    for i, c in enumerate(['0', '1', '2', '3', '4', '5', '6', '7']):
        set_nixie(i, c)
    time.sleep(4)
    for i in range(8):
        set_nixie(i, '_')

setup_gpio()

test_nixies()

frames_animation = deque()  # create the animation deque

print("=== incoming animation ===")
for i in range(24):
    animation_append(clear_frame())
for i in range(8):
    animation_insert(scramble_single(i, 24 - i * 3), offset=i * 3)

print("=== scramble animation ===")
for i in range(40):
    animation_append(random_frame())

for frame_animation in frames_animation:
    print(str(frame_animation))

print("=== outgoing animation ===")
for i in range(8):
    animation_insert(scramble_single(i, i * 3), offset=64)

frame_next = time.time()

start = 0
end = 0
while True:
    time.sleep(max(0, 0.0001 - (end - start)))
    start = time.time()
    #    if counter % 1000 == 0:
    #        color['b'] += 0.1
    #        if color['b'] > 1.0:
    #            color['b'] = 0.1
    #        print(color['b'])
    colorflow()
    # color['r'] = 0
    # color['g'] = 0
    # color['b'] = 0.01

    for config in configs.values():
        config.update()

    update_color()
    update_nixies()

    counter += 1
    end = time.time()

teardown_gpio()

