import sys
import time

import pandas as pd

sys.path.append(".")
from training_settings import TrainingSettings
from trial_plotter import TrialPlotter
from twoAFC import TwoAFC
from virtual_mouse import VirtualMouse


def main():

    time_movements = []
    time_trial_finish = []
    time_plot_update = []


    t_start = time.time()

    # Create an instance of the task and get the default training settings
    tafc_task = TwoAFC()
    training = TrainingSettings()
    training.default_training_settings()
    tafc_task.settings = training.settings
    tafc_task.settings.stimulus_modality = "visual"
    tafc_task.settings.current_training_stage = "TwoAFC_visual_easy"
    tafc_task.settings.trial_types = ["left_easy", "right_easy"]
    tafc_task.settings.holding_response_time = 0.0
    tafc_task.settings.holding_response_time_step = 0.00
    tafc_task.settings.middle_port_light_intensity = 0.1
    # remove iti to go faster
    tafc_task.settings.iti = 0.1

    # Name your subject
    tafc_task.subject = "test_subject"

    # Activate a virtual mouse and let it know about the bpod
    virtual_mouse = VirtualMouse(tafc_task.bpod)
    # Change how fast the mouse learns
    virtual_mouse.learning_rate = 0.005
    # Set the maximum number of trials
    virtual_mouse.trial_limit = 15

    # Increase the speed of the task and virtual mouse
    SPEED = 5
    virtual_mouse.speed = SPEED

    # Use an online plotter to display the results
    plotter = TrialPlotter()

    t_endinit = time.time()
    print("Initialization time: ", t_endinit - t_start)

    # Run the task
    tafc_task.run_in_thread(daemon=False)
    time.sleep(0.5)

    t_loop = time.time()
    print("Thread time: ", t_loop - t_endinit)

    # run Virtual Mouse and Plotter
    while virtual_mouse.trial_number_counter < virtual_mouse.trial_limit:
        previous_trial = tafc_task.current_trial
        virtual_mouse.read_trial_type(tafc_task.this_trial_side)
        virtual_mouse.move_mouse()

        time_movements.append(time.time() - t_loop)
        t_loop = time.time()

        # wait for the trial to finish comparing the
        # trial counters of the task
        # this is the step that takes longer!!!!
        while previous_trial == tafc_task.current_trial:
            time.sleep(0.1 / SPEED)

        time_trial_finish.append(time.time() - t_loop)
        t_loop = time.time()

        # update the plotter with the new trial data reading it from the .csv file
        if tafc_task.current_trial % 2 == 0:
            # read the data from the .csv file
            tafc_task.df = pd.read_csv(tafc_task.rt_session_path, sep=";")
            # update the plot
            plotter.update_plot(tafc_task.transform_df())

            time_plot_update.append(time.time() - t_loop)
            t_loop = time.time()

    print("Virtual Mouse has finished running the task")
    print("Average time for movements: ", sum(time_movements) / len(time_movements))
    print(
        "Average time for trial finish: ", sum(time_trial_finish) / len(time_trial_finish)
    )
    print("Average time for plot update: ", sum(time_plot_update) / len(time_plot_update))
    time.sleep(2)
    tafc_task.disconnect_and_save()
    tafc_task.close()
    plotter.keep_plotting()


if __name__ == "__main__":
    main()