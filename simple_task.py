import _thread
import sys
import time

from village.pybpodapi.protocol import Bpod, StateMachine

# find virtual_mouse.py in the same folder
sys.path.append(".")
from virtual_mouse import simple_mouse_movements

n_trials = 5

bpod = Bpod()

print("Engaging virtual mouse...")
# _thread.start_new_thread(simple_mouse_movements, (bpod,))


for trial in range(n_trials):
    sma = StateMachine(bpod)
    # 'TrialStart' state
    sma.add_state(
        state_name='TrialStart',
        state_timer=0,
        state_change_conditions={
            Bpod.Events.Port1In: 'SuccessState',
            # Bpod.Events.Tup: 'MouseTired',
            },
        output_actions=[(Bpod.OutputChannels.PWM1, 1)]
    )

    sma.add_state(
        state_name='SuccessState',
        state_timer=1,
        state_change_conditions={Bpod.Events.Tup: 'exit'},
        output_actions=[(Bpod.OutputChannels.PWM1, 50)]
    )

    sma.add_state(
        state_name='MouseTired',
        state_timer=3,
        state_change_conditions={Bpod.Events.Tup: 'exit'},
        output_actions=[(Bpod.OutputChannels.PWM1, 255)]
    )

    bpod.send_state_machine(sma)

    bpod.run_state_machine(sma)


    print("Trial {0} info: {1}".format(
        len(bpod.session.trials),
        bpod.session.current_trial),
        )


bpod.close()