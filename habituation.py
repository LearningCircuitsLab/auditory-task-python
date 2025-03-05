from village.classes.task import Event, Output, Task
from village.manager import manager


class Habituation(Task):
    def __init__(self):
        super().__init__()

        self.info = """

        Habituation Task
        -------------------

        This task is a simple visual task where the mouse has
        to poke in illuminated ports.
        The center port illuminates when a trial starts.
        After the center port is poked,
        both side ports are illuminated and give reward.

        To motivate mice, at the beginning, water is delivered automatically
        (3x reward amount in each side port)
        
        To keep mice engaged, ports give water if mouse has not poked after some time.
        """

        # variables are defined in training_settings.py

    def start(self):

        print("Habituation starts")

        ## Initiate states that won't change during training
        # Trial start state:
        # Turn on light in the middle port
        self.ready_to_initiate_output = [
            (
                Output.PWM2,
                int(self.settings.middle_port_light_intensity * 255),
            )
        ]

        # Time the valve needs to open to deliver the reward amount
        # Make sure to calibrate the valve before using it
        self.left_valve_opening_time = manager.water_calibration.get_valve_time(
            port=1, volume=self.settings.reward_amount_ml
        )
        self.right_valve_opening_time = manager.water_calibration.get_valve_time(
            port=3, volume=self.settings.reward_amount_ml
        )

        # use same light intensity for both side ports as in the middle port
        self.light_intensity_left = self.light_intensity_right = int(
            self.settings.middle_port_light_intensity * 255
        )

    def create_trial(self):
        """
        This function updates the variables that will be used every trial
        """
        print("")
        print("Trial {0}".format(str(self.current_trial)))

        # the first three trials gives reward automatically (equal to large reward)
        if self.current_trial < 4:
            self.start_of_trial_transition = "auto_reward_state_left"
        else:
            self.start_of_trial_transition = "ready_to_initiate"

        # assemble the state machine
        self.assemble_state_machine()

    def assemble_state_machine(self):
        # 'start_of_trial' state that sends a TTL pulse from the BNC channel 2
        # This can be used to synchronize the task with other devices (not used here)
        self.bpod.add_state(
            state_name="start_of_trial",
            state_timer=0.001,
            state_change_conditions={Event.Tup: self.start_of_trial_transition},
            output_actions=[Output.BNC2High],
        )

        # 'ready_to_initiate' state that waits for the poke in the middle port
        self.bpod.add_state(
            state_name="ready_to_initiate",
            state_timer=self.settings.time_to_auto_reward,
            state_change_conditions={
                Event.Port2In: "stimulus_state",
                Event.Tup: "auto_reward_state_left",
                },
            output_actions=self.ready_to_initiate_output,
        )

        # 'stimulus_state' state that turns on the side ports and waits for a poke
        self.bpod.add_state(
            state_name="stimulus_state",
            state_timer=0,
            state_change_conditions={
                Event.Port1In: "reward_state_left",
                Event.Port3In: "reward_state_right",
            },
            output_actions=[
                (Output.PWM1, self.light_intensity_left),
                (Output.PWM3, self.light_intensity_right),
            ],
        )

        # reward_state_left and reward_state_right are the states that deliver the reward
        self.bpod.add_state(
            state_name="reward_state_left",
            state_timer=self.left_valve_opening_time,
            state_change_conditions={Event.Tup: "exit"},
            output_actions=[Output.Valve1],
        )

        self.bpod.add_state(
            state_name="reward_state_right",
            state_timer=self.right_valve_opening_time,
            state_change_conditions={Event.Tup: "exit"},
            output_actions=[Output.Valve3],
        )

        # 'auto_reward_state' state that delivers reward automatically
        self.bpod.add_state(
            state_name="auto_reward_state_left",
            state_timer=self.left_valve_opening_time,
            state_change_conditions={Event.Tup: "reward_state_right"},
            output_actions=[Output.Valve1],
        )

    def after_trial(self):
        # register the amount of water given to the mouse in this trial
        # do not delete this variable, it is used to calculate the water consumption
        # and trigger alarms. You can override the alarms in the GUI
        self.bpod.register_value("water", self.settings.reward_amount_ml)

    def close(self):
        print("Closing Habituation task")
