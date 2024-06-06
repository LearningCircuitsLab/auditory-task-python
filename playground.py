import sys

from village.classes.subject import Subject

sys.path.append(".")
from follow_the_light import FollowTheLight

task = FollowTheLight()
subject = Subject("test_subject")

task.test_run(subject)