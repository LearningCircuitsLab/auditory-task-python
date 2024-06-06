import sys

from village.classes.subject import Subject

sys.path.append(".")
from follow_the_light import FollowTheLight
from trial_plotter import TrialPlotter
from virtual_mouse import VirtualMouse

# Create an instance of the task
ftl_task = FollowTheLight()

# Set the number of trials
ftl_task.number_of_trials = 100

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
ftl_task.test_run(subject)