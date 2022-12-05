import os
import signal
import subprocess
from random import randint

from mono_proof import Record, run_and_prove, reextension

scale = 5
min_steps = 11

instance_timeout = 20000
with open("color_maze5.csv", 'w') as outfile:
    for entry in range(0, scale):
        for exit in range(0, scale):
            instance = 'color_maze_{}_{}_{}_{}.gnf'.format(scale, entry,exit, min_steps)
            arugment_list = ["python3", "color_maze.py", str(scale), str(entry), str(exit), str(min_steps)]
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
            except Exception as e:
                print("e")
                outfile.write("{} error) \n".format(instance, instance_timeout))
            finally:
                # reset alarm
                signal.alarm(0)
                try:
                    os.remove(reextension(instance, "proof"))
                    os.remove(reextension(instance, "support"))
                    os.remove(reextension(instance, "ecnf"))
                    os.remove(reextension(instance, "cnf"))
                    os.remove(reextension(instance, "obg"))
                except:
                    pass

