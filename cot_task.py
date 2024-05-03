"""
Two Alternative Choice task for freely moving and three ports. The stimulus
can be either visual (LED light on top of either of the side ports), or
auditory (low tones vs high tones to indicate right or left port, respectively).
There is a habituation version, where mouse gets rewarded either side.
There is a psychometric version of the auditory task.

- The mouse initiates the trial by poking on the middle port. This triggers
the stimulus.
- There is a time limit to respond ('ResponseTime'). If time up is reached
there is a punishment time ('PunishDelay') before any more trial
can start.

If 'PhotoStimulation' is selected, a percentage of times ('PSProb') the
PulsePal will be triggered.


TODO:
- Fix random seed for sound generation if asked to. Save random seed
always
- white noise on punish action in the auditory task?
- Calibrate sound decibels.
"""

from village.pybpodapi.protocol import Bpod, StateMachine

bpod = Bpod()

sma = StateMachine(bpod)

# 'TrialStart' state
sma.add_state(
    state_name='TrialStart',
    state_timer=0.5,
    state_change_conditions={Bpod.Events.Tup: 'WaitForPoke'},
    output_actions=[]
)

# 'WaitForPoke' state
sma.add_state(
    state_name='WaitForPoke',
    state_timer=1,
    state_change_conditions={Bpod.Events.Tup: 'exit'},
    output_actions=[(Bpod.OutputChannels.PWM1, 155)]
)

bpod.send_state_machine(sma)

bpod.run_state_machine(sma)

bpod.close()