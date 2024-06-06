import _thread
import json
import random
import sys

from village.classes.task import Task
from village.pybpodapi.protocol import Bpod

# find python files in the same folder
sys.path.append(".")
from trial_plotter import TrialPlotter
from utils import valve_ml_to_s
from virtual_mouse import VirtualMouse


class FollowTheLight(Task):
    def __init__(self):
        super().__init__()

        self.info = """

        Follow The Light Task
        -------------------
        
        This task is a simple visual task where the mouse has to poke the center port to start a trial.
        After the center port is poked, one of the two side ports will be illuminated.
        If the mouse licks the correct side port, it receives a reward.
        If the mouse licks the wrong side port, it receives a punishment.
        """

        # define total number of trials
        self.number_of_trials = 10

        # initiate the variable for the virtual mouse
        self.virtual_mouse = None
        # initialise the speed of the task (used normally for the virtual mouse)
        # 1 is the normal speed
        self.speed = 1

        # initiate the plotter
        self.plotter = None

    def start(self):

        # get parameters from the settings
        with open('follow_the_light_settings.json') as f:
            self.task_settings = json.load(f)

        ## Initiate variables that will be used in the task and won't change
        # Middle port states
        # Turn on light in the middle port, turn off everything else (it should be off already anyway)
        self.ready_to_initiate_output = [
            (Bpod.OutputChannels.PWM2, self.task_settings["middle_port_light_intensity"]),
            (Bpod.OutputChannels.PWM1, 0),
            (Bpod.OutputChannels.PWM3, 0),
            (Bpod.OutputChannels.BNC1, 0),
            ('SoftCode', 255),  # sound off
            ]

        # Holding state
        # Change the light of the middle port to the minimum to indicate start of poke
        self.middle_port_output = [(Bpod.OutputChannels.PWM2, 1)]

        # Time the animal has to choose a side port
        self.timer_for_response = self.task_settings["timer_for_response"] / self.speed
        self.valve_opening_time = valve_ml_to_s(self.task_settings["reward_amount_ml"]) / self.speed

        # determine if punishment is needed
        if self.task_settings["punishment"]:
            self.punish_condition = 'punish_state'
            self.punishment_timeout = self.task_settings["punishment_timeout"] / self.speed
        else:
            # if no timeout, let the mouse choose again
            self.punish_condition = 'stimulus_state'
            self.punishment_timeout = 0
        
        # define inter-trial interval. You can change this every trial if you want
        self.iti = self.task_settings["inter_trial_interval"] / self.speed

        ## initiate other variables that will be updated every trial
        self.start_of_trial_transition = None

        # start the virtual mouse if it is a class VirtualMouse
        if type(self.virtual_mouse) == VirtualMouse:
            print("Engaging virtual mouse...")
        
        # initiate the plotter if it is a class TrialPlotter
        if type(self.plotter) == TrialPlotter:
            print("Engaging plotter...")

    def configure_gui(self):
        pass

    def create_trial(self):
        """
        This function updates the variables that will be used every trial
        """
        print("")
        print("Trial {0}".format(str(self.current_trial)))

        ## Start the task
        # On the first trial, the door is closed.
        # This is coded as a transition in the 'close_door' state.
        if self.current_trial == 0:
            # Close the door
            self.start_of_trial_transition = 'close_door'
        else:
            self.start_of_trial_transition = 'ready_to_initiate'

        ## Define the conditions for the trial
        # pick a trial type. In this case it is a random choice between "left" and "right"
        self.this_trial_type = random.choice(self.task_settings["trial_types"])

        # send it to the virtual mouse
        if self.virtual_mouse:
            self.virtual_mouse.read_trial_type(self.this_trial_type)
            # engage the virtual mouse
            _thread.start_new_thread(self.virtual_mouse.move_mouse, ())

        ## Middle port states      
        # Adjust as you want the timer that the mouse has to hold the head in the middle port
        # For example, you could keep increasing this with each correct trial
        self.middle_port_hold_timer = self.task_settings["middle_port_hold_time"] / self.speed
        # Define what happens if the mouse withdraws the head from the middle port too early
        self.early_withdrawal_state = 'ready_to_initiate'

        ## Stimulus states
        self.stimulus_state_output = []
        match self.this_trial_type:
            case "left":
                self.stimulus_state_output.append((Bpod.OutputChannels.PWM1,
                                                   self.task_settings["side_port_light_intensity"]))
                self.left_poke_action = 'reward_state'
                self.right_poke_action = self.punish_condition
                self.valve_to_open = 1
            case "right":
                self.stimulus_state_output.append((Bpod.OutputChannels.PWM3,
                                                   self.task_settings["side_port_light_intensity"]))
                self.left_poke_action = self.punish_condition
                self.right_poke_action = 'reward_state'
                self.valve_to_open = 4
        
        # assemble the state machine
        self.assemble_state_machine()

    def assemble_state_machine(self):
        # 'start_of_trial' state that sends a TTL pulse to the BNC channel 2
        self.sma.add_state(
            state_name='start_of_trial',
            state_timer=0.01 / self.speed,
            state_change_conditions={Bpod.Events.Tup: self.start_of_trial_transition},
            output_actions=[(Bpod.OutputChannels.BNC2, 3)]
        )

        self.sma.add_state(
            state_name='close_door',
            state_timer=0,
            state_change_conditions={Bpod.Events.Tup: 'ready_to_initiate'},
            output_actions=[(Bpod.OutputChannels.SoftCode, 20)]
            #TODO: change this softcode to a default one
        )

        # 'ready_to_initiate' state that waits for the poke in the middle port
        self.sma.add_state(
            state_name='ready_to_initiate',
            state_timer=0,
            state_change_conditions={Bpod.Events.Port2In: 'holding_state'},
            output_actions=self.ready_to_initiate_output
        )

        # 'holding_state' is the second automatic state
        # If the mouse does not hold the head enough time in the central port,
        # it goes back to the start or to punishment. If timer is reached, it jumps to
        # 'stimulus_state'.
        self.sma.add_state(
            state_name='holding_state',
            state_timer=self.middle_port_hold_timer,
            state_change_conditions={
                Bpod.Events.Port2Out: self.early_withdrawal_state,
                Bpod.Events.Tup: 'stimulus_state',
                },
            output_actions=self.middle_port_output
        )

        self.sma.add_state(
            state_name='stimulus_state',
            state_timer=self.timer_for_response,
            state_change_conditions={
                Bpod.Events.Port1In: self.left_poke_action,
                Bpod.Events.Port3In: self.right_poke_action,
                Bpod.Events.Tup: 'exit'},
            output_actions=self.stimulus_state_output
        )

        self.sma.add_state(
            state_name='reward_state',
            state_timer=self.valve_opening_time,
            state_change_conditions={Bpod.Events.Tup: 'iti'},
            output_actions=[
                (Bpod.OutputChannels.Valve, self.valve_to_open),
                # ('BNC1', OptoCondition_onSidePort)
                ]
        )

        self.sma.add_state(
            state_name='punish_state',
            state_timer=self.punishment_timeout,
            state_change_conditions={Bpod.Events.Tup: 'iti'},
            output_actions=[]
        )

        # iti is the time that the mouse has to wait before the next trial
        self.sma.add_state(
            state_name='iti',
            state_timer=self.iti,
            state_change_conditions={Bpod.Events.Tup: 'exit'},
            output_actions=[]
        )

    def after_trial(self):
        visited_states = [self.bpod.session.current_trial.sma.state_names[i] for i in self.bpod.session.current_trial.states]
        if "reward_state" in visited_states:
            result = 1
        else:
            result = 0
    
        # update the plotter
        if type(self.plotter) == TrialPlotter:
            refresh_rate = 5 # every how many trials you want to update the plot
            self.plotter.update_plot(result, refresh_rate)

    def close(self):
        # Keep the plot open
        if type(self.plotter) == TrialPlotter:
            self.plotter.keep_plotting()
            print("Close the plot window to finish the task") 
        print("Closing the task")
