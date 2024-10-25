import sys

from village.classes.subject import Subject

sys.path.append(".")
from follow_the_light import FollowTheLight
from trial_plotter import TrialPlotter
from virtual_mouse import VirtualMouse
from training_settings import TrainingSettings

# Create an instance of the task and get the default training settings
ftl_task = FollowTheLight()
training = TrainingSettings()
training.default_training_settings()
ftl_task.settings = training.settings

# Activate a virtual mouse and let it know about the bpod
ftl_task.virtual_mouse = VirtualMouse(ftl_task.bpod)
# Change how fast the mouse learns
ftl_task.virtual_mouse.learning_rate = .005

# Increase the speed of the task and virtual mouse
SPEED = 50
ftl_task.speed = SPEED
ftl_task.virtual_mouse.speed = SPEED

# Use an online plotter to display the results
ftl_task.plotter = TrialPlotter()

# Create a subject
subject = Subject("test_subject")

# Run the task
ftl_task.run_one_trial_in_thread()
#     time.sleep(.5)
#     # poke in the middle port
#     task.bpod.manual_override_input("Port2In")
#     task.bpod.manual_override_input("Port2Out")
#     # poke in the left port
#     task.bpod.manual_override_input("Port1In")
#     task.bpod.manual_override_input("Port1Out")
#     time.sleep(0.1)
#     # poke in the right port
#     task.bpod.manual_override_input("Port3In")
#     task.bpod.manual_override_input("Port3Out")
#     # leave enough time for the bpod to finish
#     time.sleep(2)