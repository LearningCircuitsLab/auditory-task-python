import _thread
import json
import random
import sys

import numpy as np
from village.pybpodapi.protocol import Bpod, StateMachine

# find python files in the same folder
sys.path.append(".")
from trial_plotter import TrialPlotter
from utils import valve_ml_to_s
from virtual_mouse import SPEED, VirtualMouse, mouse_movements

# define SPEED if virtual_mouse.py is not imported
# SPEED = 1

# get parameters from the settings
with open('cot_task_settings.json') as f:
    S = json.load(f)

timer_for_response = S["timer_for_response"] / SPEED
valve_opening_time = valve_ml_to_s(S["reward_amount_ml"]) / SPEED

# determine if punishment is needed
if S["punishment"]:
    punish_condition = 'punish_state'
    punishment_timeout = S["punishment_timeout"] / SPEED
else:
    punish_condition = 'ready_for_response'
    punishment_timeout = 0

# Create an instance of TrialPlotter
plotter = TrialPlotter()

# define the maximum number of trials
n_trials = 100

bpod = Bpod()

print("Engaging virtual mouse...")
virtual_mouse = VirtualMouse(bpod)
# _thread.start_new_thread(mouse_movements, (bpod,))


for trial in range(n_trials):

    ### Define the conditions for the trial

    # pick a trial type
    this_trial_type = random.choice(S["trial_types"])
    # send it to the virtual mouse
    virtual_mouse.read_trial_type(this_trial_type)
    # engage the virtual mouse
    _thread.start_new_thread(virtual_mouse.move_mouse, ())

    ## Middle port states
    # Turn on light in the middle port, turn off everything else
    ready_to_initiate_output = [
        (Bpod.OutputChannels.PWM2, S["middle_port_light_intensity"]),
        (Bpod.OutputChannels.PWM1, 0),
        (Bpod.OutputChannels.PWM3, 0),
        (Bpod.OutputChannels.BNC1, 0),
        ('SoftCode', 255),  # sound off
        ]

    state_to_go_after_middle_poke = 'stimulus_state'
    opto_on_initiation_port_time = 0 / SPEED
    opto_on_initiation_port_actions = []

    early_withdrawal_state = 'ready_to_initiate'

    middle_port_hold_timer = .3 / SPEED
    # TODO: play sound here
    # TODO: remove the light from the middle port here?
    middle_port_output = [(Bpod.OutputChannels.PWM2, 20)]
    match this_trial_type:
        case "left":
            middle_port_output.append((Bpod.OutputChannels.PWM1, S["side_port_light_intensity"]))
            left_poke_action = 'reward_state'
            right_poke_action = punish_condition
            valve_to_open = 1
        case "right":
            middle_port_output.append((Bpod.OutputChannels.PWM3, S["side_port_light_intensity"]))
            left_poke_action = punish_condition
            right_poke_action = 'reward_state'
            valve_to_open = 4
    

    # can do opto here for instance
    ready_for_response_output = []        

    # Define the state machine
    sma = StateMachine(bpod)
    # 'start_of_trial' state that sends a TTL pulse to the BNC channel 2
    sma.add_state(
        state_name='start_of_trial',
        state_timer=0.01 / SPEED,
        state_change_conditions={Bpod.Events.Tup: 'ready_to_initiate'},
        output_actions=[(Bpod.OutputChannels.BNC2, 3)]
    )

    # 'ready_to_initiate' state that waits for the poke in the middle port
    sma.add_state(
        state_name='ready_to_initiate',
        state_timer=0,
        state_change_conditions={Bpod.Events.Port2In: state_to_go_after_middle_poke},
        output_actions=ready_to_initiate_output
    )

    sma.add_state(
        state_name='opto_on_initiation_port',
        state_timer=opto_on_initiation_port_time,
        state_change_conditions={
            Bpod.Events.Port2Out: early_withdrawal_state,
            Bpod.Events.Tup: 'stimulus_state',
            },
        output_actions=opto_on_initiation_port_actions,
    )

    # 'stimulus_state' is the second automatic state
    # If the mouse does not hold the head enough time in the central port,
    # it goes back to the start or to punishment. If timer is reached, it jumps to
    # 'wait_for_middle_poke_out'.
    sma.add_state(
        state_name='stimulus_state',
        state_timer=middle_port_hold_timer,
        state_change_conditions={
            Bpod.Events.Port2Out: early_withdrawal_state,
            Bpod.Events.Tup: 'wait_for_middle_poke_out',
            },
        output_actions=middle_port_output
    )
    # 'wait_for_middle_poke_out' changes when the mouse removes the head from the
    # middle port.
    sma.add_state(
        state_name='wait_for_middle_poke_out',
        state_timer=0,
        state_change_conditions={Bpod.Events.Port2Out: 'ready_for_response'},
        #TODO: check if middle LED turns off here. It should
        output_actions=[]
    )

    sma.add_state(
        state_name='ready_for_response',
        state_timer=timer_for_response,
        state_change_conditions={
            Bpod.Events.Port1In: left_poke_action,
            Bpod.Events.Port3In: right_poke_action,
            Bpod.Events.Tup: 'exit'},
        output_actions=ready_for_response_output
    )

    sma.add_state(
        state_name='reward_state',
        state_timer=valve_opening_time,
        state_change_conditions={Bpod.Events.Tup: 'drinking'},
        output_actions=[
            (Bpod.OutputChannels.Valve, valve_to_open),
            # ('BNC1', OptoCondition_onSidePort)
            ]
    )

    sma.add_state(
        state_name='punish_state',
        state_timer=punishment_timeout,
        state_change_conditions={Bpod.Events.Tup: 'exit'},
        output_actions=[]
    )

    # Drinking is a mock state to check that the animal has drunk. It is
    # used to plot stuff and calculate correct trials
    sma.add_state(
        state_name='drinking',
        state_timer=0,
        state_change_conditions={Bpod.Events.Tup: 'exit'},
        output_actions=[]
    )

    bpod.send_state_machine(sma)

    bpod.run_state_machine(sma)


    print("Trial {0}, type  {1} info: {2}".format(
        len(bpod.session.trials),
        this_trial_type,
        bpod.session.current_trial),
        )
    print("")

    # TODO: update plots here
    # get if the trial was correct or not

    # print visited states
    print("Visited states:")
    visited_states = [bpod.session.current_trial.sma.state_names[i] for i in bpod.session.current_trial.states]
    print(visited_states)
    print("")
    if "reward_state" in visited_states:
        result = 1
    else:
        result = 0
    
    # update the plot every 5 trials
    plotter.update_plot(result, 5)

    # This to get timestamps:
    # success_state = bpod.session.current_trial.states_durations['reward_state'][0]


bpod.close()

# Keep the plot open
plotter.keep_plotting()