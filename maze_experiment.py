import signal
import subprocess
import os

from mono_proof import Record, run_and_prove

max_scale = 4

instance_timeout = 200000
with open("chromatic_maze.csv", 'w') as outfile:
    for scale in range(2, max_scale+1):
        width = scale
        height = scale
        min_steps = scale * scale
        instance = 'chromatic_{}_{}_{}.gnf'.format(scale, scale ,scale*scale)
        arugment_list = ["python3.5", "chromatic_maze.py", str(width), str(height), str(min_steps)]
        process = subprocess.Popen(arugment_list,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        stdout, stderr = process.communicate()

        record = Record(instance)
        # set timeout for three hours
        signal.alarm(instance_timeout)
        try:
            res = run_and_prove(instance, record, running_opt=["-no-check-solution", "-verb=1", "-theory-order-vsids",
                                                               "-vsids-both", "-decide-theories",
                                                               "-no-decide-graph-rnd",
                                                               "-lazy-maxflow-decisions", "-conflict-min-cut",
                                                               "-adaptive-history-clear=5"], witness_reduction=True)
            outfile.write(str(record) + '\n')
        except TimeoutError:
            outfile.write("{} timeout ({} secs) \n".format(instance, instance_timeout))
        except Exception:
            outfile.write("{} error) \n".format(instance, instance_timeout))
        finally:
            # reset alarm
            signal.alarm(0)

