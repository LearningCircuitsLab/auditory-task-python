import sys
import time

import pandas as pd

sys.path.append(".")
from follow_the_light import TwoAFC
from training_settings import TrainingSettings
from trial_plotter import TrialPlotter
from virtual_mouse import VirtualMouse

time_movements = []
time_trial_finish = []
time_plot_update = []


t_start = time.time()

# Create an instance of the task and get the default training settings
ftl_task = TwoAFC()
training = TrainingSettings()
training.default_training_settings()
ftl_task.settings = training.settings
# remove iti to go faster
ftl_task.settings.iti = 0

# Name your subject
ftl_task.subject = "test_subject"

# Activate a virtual mouse and let it know about the bpod
virtual_mouse = VirtualMouse(ftl_task.bpod)
# Change how fast the mouse learns
virtual_mouse.learning_rate = 0.005
# Set the maximum number of trials
virtual_mouse.trial_limit = 25

# Increase the speed of the task and virtual mouse
SPEED = 100
virtual_mouse.speed = SPEED

# Use an online plotter to display the results
plotter = TrialPlotter()

t_endinit = time.time()
print("Initialization time: ", t_endinit - t_start)

# Run the task
ftl_task.run_in_thread(daemon=False)
time.sleep(0.5)

t_loop = time.time()
print("Thread time: ", t_loop - t_endinit)

# run Virtual Mouse and Plotter
while virtual_mouse.trial_number_counter < virtual_mouse.trial_limit:
    virtual_mouse.read_trial_type(ftl_task.this_trial_type)
    virtual_mouse.move_mouse()

    time_movements.append(time.time() - t_loop)
    t_loop = time.time()

    # wait for the trial to finish comparing the
    # trial counters of the mouse and the task
    # this is the step that takes longer!!!!
    while virtual_mouse.trial_number_counter != ftl_task.current_trial:
        time.sleep(0.1 / SPEED)

    time_trial_finish.append(time.time() - t_loop)
    t_loop = time.time()

    # update the plotter with the new trial data reading it from the .csv file
    if ftl_task.current_trial % 2 == 0:
        # read the data from the .csv file
        ftl_task.df = pd.read_csv(ftl_task.rt_session_path, sep=";")
        # update the plot
        plotter.update_plot(ftl_task.transform_df())

        time_plot_update.append(time.time() - t_loop)
        t_loop = time.time()

print("Virtual Mouse has finished running the task")
print("Average time for movements: ", sum(time_movements) / len(time_movements))
print(
    "Average time for trial finish: ", sum(time_trial_finish) / len(time_trial_finish)
)
print("Average time for plot update: ", sum(time_plot_update) / len(time_plot_update))
time.sleep(2)
ftl_task.disconnect_and_save()
ftl_task.close()
plotter.keep_plotting()
