import time

from village.pybpodapi.protocol import Bpod


class VirtualMouse():
    def __init__(self, my_bpod):
        self.my_bpod = my_bpod
        # self.bpod = Bpod()
        self.trial_limit = 3
    
    def portX_in(self, port_number):
        # somehow it has to poke out first for this to work
        self.my_bpod.manual_override(Bpod.ChannelTypes.INPUT, 'Port', channel_number=port_number, value=0)
        self.my_bpod.manual_override(Bpod.ChannelTypes.INPUT, 'Port', channel_number=port_number, value=1)

    def portX_out(self, port_number):
        self.my_bpod.manual_override(Bpod.ChannelTypes.INPUT, 'Port', channel_number=port_number, value=0)

def mouse_movements(bpod):
    my_mouse = VirtualMouse(bpod)
    # wait some time for the bpod to start running
    time.sleep(1)

    # introduce here a way to detect if there is a new trial
    # every new trial do something
    previous_trial_number = 0
    idle_time_limit = 7
    current_time = time.time()
    while time.time() - current_time < idle_time_limit:
        current_trial_number = len(bpod.session.trials)
        if current_trial_number > my_mouse.trial_limit:
            pass
        elif len(bpod.session.trials) > previous_trial_number:
            previous_trial_number = len(bpod.session.trials)
            print("New trial detected!")
            my_mouse.portX_in(1)
            time.sleep(.5)
            my_mouse.portX_out(1)
        time.sleep(1)
    print("Mouse is tired...")

    

