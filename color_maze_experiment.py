import signal
import subprocess
from random import randint

from mono_proof import Record, run_and_prove

max_scale = 5

instance_timeout = 200000
with open("chromatic_maze.csv", 'w') as outfile:
    for scale in range(2, max_scale+1):
        entry_point = randint(0, scale -1)
        exit_point = randint(0, scale -1)
        min_steps = (scale * scale) -1
        instance = 'color_maze_{}_{}_{}_{}.gnf'.format(scale, entry_point,exit_point, min_steps)
        arugment_list = ["python3", "color_maze.py", str(scale), str(entry_point), str(exit_point), str(min_steps)]
        process = subprocess.Popen(arugment_list,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        stdout, stderr = process.communicate()

        record = Record(instance)
        # set timeout for three hours
        signal.alarm(instance_timeout)
        try:
            res = run_and_prove(instance, record, running_opt=["-no-decide-theories"], witness_reduction=True)
            outfile.write(str(record) + '\n')
        except TimeoutError:
            outfile.write("{} timeout ({} secs) \n".format(instance, instance_timeout))
        except Exception:
            outfile.write("{} error) \n".format(instance, instance_timeout))
        finally:
            # reset alarm
            signal.alarm(0)

