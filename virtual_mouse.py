import time

import numpy as np


class VirtualMouse:
    def __init__(self, my_bpod):
        self.my_bpod = my_bpod
        self.trial_limit = 200
        self.trial_number_counter = 0
        self.performance = 0.5
        self.learning_rate = 0.005
        self.speed = 50

    def portX_in(self, port_number):
        # somehow it has to poke out first for this to work
        self.my_bpod.manual_override_input("Port" + str(port_number) + "Out")
        self.my_bpod.manual_override_input("Port" + str(port_number) + "In")

    def portX_out(self, port_number):
        self.my_bpod.manual_override_input("Port" + str(port_number) + "Out")
    
    def listen_for_trial_start(self):
        while True:
            # print("Virtual Mouse is reading the current state...")
            # get the current state name
            try:
                current_state = self.my_bpod.sma.state_names[self.my_bpod.sma.current_state]
            except (TypeError, IndexError): # sometimes sma.current_state returns float if it is changing trial
                continue
            if current_state == "ready_to_initiate":
                print("Virtual Mouse is starting a new trial!")
                return
            # wait a bit before checking again
            time.sleep(0.1 / self.speed)

    def read_trial_type(self, trial_type):
        self.trial_type = trial_type

    def port_picker(self, trial_type, mouse_performance):
        probability_distribution = [mouse_performance, 1 - mouse_performance]
        if "right" in trial_type:
            # reverse the probability distribution
            probability_distribution.reverse()
        return np.random.choice([1, 3], p=probability_distribution)

    def learn(self):
        self.performance += self.learning_rate
        if self.performance > 1:
            self.performance = 1

    def move_mouse(self):
        self.movements_for_trial(self.trial_type)

    def movements_for_trial(self, trial_type):
        # check if it is moment to poke in the center port
        self.listen_for_trial_start()
        self.trial_number_counter += 1
        # poke in center port, then left then right
        for x in [2, 1, 3]:
            self.portX_in(x)
            time.sleep(0.1 / self.speed)
            self.portX_out(x)
            time.sleep(0.2 / self.speed)

        # TODO: Implement the following for learning
        # # choose a port to poke
        # port_to_poke = self.port_picker(trial_type, self.performance)
        # self.portX_in(port_to_poke)
        # time.sleep(0.5 / self.speed)
        # self.portX_out(port_to_poke)
        # # learn
        # if self.performance < 1:
        #     self.learn()