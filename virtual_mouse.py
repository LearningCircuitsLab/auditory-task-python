import _thread
import random
import time

import numpy as np
from village.pybpodapi.protocol import Bpod

SPEED = 5


class VirtualMouse():
    def __init__(self, my_bpod):
        self.my_bpod = my_bpod
        # self.bpod = Bpod()
        self.trial_limit = 500
        self.trial_number_counter = 0
        self.performance = .5
        self.learning_rate = .005
    
    def portX_in(self, port_number):
        # somehow it has to poke out first for this to work in my laptop only
        # self.my_bpod.manual_override(Bpod.ChannelTypes.INPUT, 'Port', channel_number=port_number, value=0)
        self.my_bpod.manual_override(Bpod.ChannelTypes.INPUT, 'Port', channel_number=port_number, value=1)

    def portX_out(self, port_number):
        self.my_bpod.manual_override(Bpod.ChannelTypes.INPUT, 'Port', channel_number=port_number, value=0)
    
    def read_trial_type(self, trial_type):
        self.trial_type = trial_type
        print(f"Mouse is reading trial type: {self.trial_type}")

    def port_picker(self, trial_type, mouse_performance):
        probability_distribution = [mouse_performance, 1 - mouse_performance]
        if trial_type == "right":
            # reverse the probability distribution
            probability_distribution.reverse()
        return np.random.choice([1, 3], p=probability_distribution)
    
    def learn(self):
        self.performance += self.learning_rate
        if self.performance > 1:
            self.performance = 1
        print(f"Mouse performance: {self.performance}")

    def move_mouse(self, trial_type):
        print("Mouse is starting a new trial!")
        self.read_trial_type(trial_type)
        self.movements_for_trial(self.trial_type)
    
    def movements_for_trial(self, trial_type):
        self.trial_number_counter += 1
        # wait a bit for the bpod to load the state matrix
        time.sleep(.05)
        # poke in center port
        self.portX_in(2)
        time.sleep(.5 / SPEED)
        self.portX_out(2)
        # choose a random port to poke
        port_to_poke = self.port_picker(trial_type, self.performance)
        print(f"Mouse poked in {port_to_poke}")
        self.portX_in(port_to_poke)
        time.sleep(.5 / SPEED)
        self.portX_out(port_to_poke)
        # learn
        self.learn()
        print(f"Done trial number: {self.trial_number_counter}")

def mouse_movements(bpod):
    my_mouse = VirtualMouse(bpod)
    # wait a second for the bpod to start running
    time.sleep(2)

    # detect if there is a new trial
    # every new trial do something
    previous_trial_number = 0
    idle_time_limit = 7
    current_time = time.time()
    while time.time() - current_time < idle_time_limit:
        try:
            current_trial_number = len(bpod.session.trials)
        except AttributeError:
            print("Bpod session not found, task probabrly finished.")
            break
        if current_trial_number > my_mouse.trial_limit:
            # if the current trial number is greater than the limit, mouse does nothing
            pass
        elif len(bpod.session.trials) > previous_trial_number:
            previous_trial_number = len(bpod.session.trials)
            # poke in center port
            my_mouse.portX_in(2)
            time.sleep(.5 / SPEED)
            my_mouse.portX_out(2)
            # choose a random port to poke
            port_to_poke = random.choice([1, 3])
            my_mouse.portX_in(port_to_poke)
            time.sleep(.5 / SPEED)
            my_mouse.portX_out(port_to_poke)
        time.sleep(1 / SPEED)
        current_time = time.time()
    print("Mouse is tired...")

def simple_mouse_movements(bpod):
    my_mouse = VirtualMouse(bpod)
    # wait a second for the bpod to start running
    time.sleep(1)

    # detect if there is a new trial
    # every new trial do something
    previous_trial_number = 0
    idle_time_limit = 7
    current_time = time.time()
    while time.time() - current_time < idle_time_limit:
        current_trial_number = len(bpod.session.trials)
        if current_trial_number > my_mouse.trial_limit:
            # if the current trial number is greater than the limit, mouse does nothing
            pass
        elif len(bpod.session.trials) > previous_trial_number:
            previous_trial_number = len(bpod.session.trials)
            print("New trial detected!")
            # poke in center port
            my_mouse.portX_in(2)
            time.sleep(.5 / SPEED)
            my_mouse.portX_out(2)
        time.sleep(1 / SPEED)
        current_time = time.time()
    print("Mouse is tired...")  

